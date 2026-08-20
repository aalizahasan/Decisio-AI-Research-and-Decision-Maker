import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query, Request, Header
from pydantic import BaseModel, Field, EmailStr


from sqlalchemy.orm import Session
from google import genai

from app.config import settings
from app.db.database import get_db
from app.db.models import Document, DocumentChunk, DecisionAnalysis, User, EmailVerificationOTP
from app.services.pdf_service import extract_pdf_pages
from app.services.chunking_service import chunk_page_texts
from app.services.embedding_service import get_text_embedding
from app.services.retrieval_service import search_relevant_chunks
from app.services.classifier_service import classify_request, RequestClassification
from app.services.prompt_service import build_adaptive_prompt
from app.services.matrix_service import generate_and_calculate_matrix, DecisionMatrixData
from app.services.agent_service import run_multi_agent_pipeline, MultiAgentResult
from app.services.auth_service import (
    validate_real_email,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    create_password_reset_token,
    verify_password_reset_token,
    generate_6digit_otp,
    decode_google_credential,
)

logger = logging.getLogger("routes")
router = APIRouter()


# Auth Pydantic Schemas
class SendOTPRequest(BaseModel):
    email: str = Field(..., description="Target real email address for 6-digit OTP verification")


class VerifyOTPRequest(BaseModel):
    email: str
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit numeric OTP verification code")
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None

class UserRegisterRequest(BaseModel):
    email: str = Field(..., description="User's real email address")
    password: str = Field(..., min_length=6, description="User password (min 6 chars)")
    full_name: Optional[str] = Field(None, description="Optional full name")


class UserLoginRequest(BaseModel):
    email: str
    password: str


class GoogleOAuthRequest(BaseModel):
    id_token: Optional[str] = None
    email: str
    full_name: Optional[str] = None
    provider: str = "google"


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str = Field(..., min_length=6)


class UserProfile(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    auth_provider: str = "email"
    created_at: str


class AuthResponse(BaseModel):
    status: str
    message: str
    access_token: str
    user: UserProfile


def get_current_user_email(request: Request) -> str:
    """
    Extracts authenticated user email from Bearer JWT token in Authorization header.
    Defaults to 'guest_user' if token is missing or invalid.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return "guest_user"

    token = auth_header.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return "guest_user"

    return payload["sub"]


def require_authenticated_user(request: Request) -> str:
    """
    Strict authentication dependency. Raises HTTP 401 if user is unauthenticated.
    """
    email = get_current_user_email(request)
    if email == "guest_user":
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please sign in or create an account to use Decisio."
        )
    return email




class SourceReference(BaseModel):
    document_id: int
    filename: str
    page_number: Optional[int] = None
    chunk_index: Optional[int] = None


class DecisionRequest(BaseModel):
    problem: str = Field(..., description="The decision problem or question to analyze")
    context: str = Field("", description="Relevant background context or information")
    constraints: str = Field("", description="Key constraints or requirements")
    document_id: Optional[int] = Field(None, description="Optional attached document ID for RAG grounding")
    response_preference: Optional[str] = Field("auto", description="Response depth preference: 'auto', 'concise', 'detailed'")


class DecisionResponse(BaseModel):
    status: str
    message: str
    analysis_id: Optional[int] = None
    problem: str
    context: str
    constraints: str
    analysis: Optional[str] = None
    request_type: str = "SIMPLE_QUESTION"
    response_depth: str = "concise"
    multi_agent_used: bool = False
    agents_metadata: List[Dict[str, Any]] = []
    sources: List[SourceReference] = []
    matrix: Optional[DecisionMatrixData] = None


class AnalysisHistoryItem(BaseModel):
    id: int
    problem: str
    request_type: str
    response_depth: str
    multi_agent_used: bool = False
    created_at: str


class AnalysisDetail(BaseModel):
    id: int
    problem: str
    context: str
    constraints: str
    analysis: str
    request_type: str
    response_depth: str
    multi_agent_used: bool = False
    agents_metadata: List[Dict[str, Any]] = []
    sources: List[SourceReference] = []
    matrix: Optional[DecisionMatrixData] = None
    created_at: str


class DocumentUploadResponse(BaseModel):
    status: str
    document_id: int
    filename: str
    chunks_created: int


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "0.1.0"
    }


# ==========================================
# AUTHENTICATION ENDPOINTS
# ==========================================

from app.services.email_service import send_verification_otp_email

@router.post("/auth/send-otp")
def send_email_otp(req: SendOTPRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()

    if not validate_real_email(email):
        raise HTTPException(
            status_code=400,
            detail="Please provide a valid, real email address (e.g. user@example.com). Fake or dummy emails are not accepted."
        )

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="An account with this email address already exists. Please sign in instead."
        )

    otp_code = generate_6digit_otp()
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # Invalidate previous unused OTPs for this email
    db.query(EmailVerificationOTP).filter(EmailVerificationOTP.email == email).delete()

    otp_record = EmailVerificationOTP(
        email=email,
        otp_code=otp_code,
        expires_at=expires_at,
        is_used=False
    )
    db.add(otp_record)
    db.commit()

    # Dispatch Real SMTP Email to user inbox
    email_sent = send_verification_otp_email(email, otp_code)
    if not email_sent:
        logger.info(f"SMTP delivery unconfigured/failed. Logged verification code for [{email}]: [{otp_code}]")

    return {
        "status": "success",
        "message": f"A 6-digit verification code has been sent to {email}. Please check your inbox."
    }



@router.post("/auth/verify-otp", response_model=AuthResponse)
def verify_email_otp(req: VerifyOTPRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    otp_code = req.otp_code.strip()

    otp_record = db.query(EmailVerificationOTP)\
        .filter(EmailVerificationOTP.email == email)\
        .filter(EmailVerificationOTP.otp_code == otp_code)\
        .filter(EmailVerificationOTP.is_used == False)\
        .order_by(EmailVerificationOTP.created_at.desc())\
        .first()

    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid verification code. Please check the 6-digit code and try again.")

    if datetime.utcnow() > otp_record.expires_at:
        raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new code.")

    # Mark OTP used
    otp_record.is_used = True

    # Check if user exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        user_record = existing_user
    else:
        pwd_hash = hash_password(req.password)
        user_record = User(
            email=email,
            hashed_password=pwd_hash,
            full_name=req.full_name or email.split("@")[0].capitalize(),
            auth_provider="email"
        )
        db.add(user_record)

    db.commit()
    db.refresh(user_record)

    token = create_access_token({"sub": user_record.email, "id": user_record.id})

    return AuthResponse(
        status="success",
        message="Email verified and account activated successfully.",
        access_token=token,
        user=UserProfile(
            id=user_record.id,
            email=user_record.email,
            full_name=user_record.full_name,
            auth_provider=user_record.auth_provider,
            created_at=user_record.created_at.isoformat()
        )
    )


@router.post("/auth/register", response_model=AuthResponse)
def register_user(req: UserRegisterRequest, db: Session = Depends(get_db)):

    email = req.email.strip().lower()
    
    # 1. Real Email Validation
    if not validate_real_email(email):
        raise HTTPException(
            status_code=400,
            detail="Please provide a valid, real email address (e.g. user@example.com). Dummy or invalid emails are not allowed."
        )

    # 2. Check existing user
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="An account with this email address already exists. Please sign in instead."
        )

    # 3. Create User
    pwd_hash = hash_password(req.password)
    user_record = User(
        email=email,
        hashed_password=pwd_hash,
        full_name=req.full_name or email.split("@")[0].capitalize(),
        auth_provider="email"
    )
    db.add(user_record)
    db.commit()
    db.refresh(user_record)

    # 4. Generate Access Token
    token = create_access_token({"sub": user_record.email, "id": user_record.id})

    return AuthResponse(
        status="success",
        message="User account created successfully.",
        access_token=token,
        user=UserProfile(
            id=user_record.id,
            email=user_record.email,
            full_name=user_record.full_name,
            auth_provider=user_record.auth_provider,
            created_at=user_record.created_at.isoformat()
        )
    )


@router.post("/auth/login", response_model=AuthResponse)
def login_user(req: UserLoginRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    
    user_record = db.query(User).filter(User.email == email).first()
    if not user_record:
        raise HTTPException(
            status_code=404,
            detail="No account found with this email address. Please click 'Create Account' to sign up."
        )

    if not verify_password(req.password, user_record.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect password. Please verify your password or click 'Forgot Password' to reset it."
        )


    token = create_access_token({"sub": user_record.email, "id": user_record.id})

    return AuthResponse(
        status="success",
        message="Login successful.",
        access_token=token,
        user=UserProfile(
            id=user_record.id,
            email=user_record.email,
            full_name=user_record.full_name,
            auth_provider=user_record.auth_provider,
            created_at=user_record.created_at.isoformat()
        )
    )


@router.post("/auth/oauth/google", response_model=AuthResponse)
def google_oauth_login(req: GoogleOAuthRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    if not validate_real_email(email):
        raise HTTPException(status_code=400, detail="Invalid email returned from Google authentication.")

    user_record = db.query(User).filter(User.email == email).first()
    if not user_record:
        # Create Google OAuth user
        pwd_hash = hash_password(os.urandom(16).hex())
        user_record = User(
            email=email,
            hashed_password=pwd_hash,
            full_name=req.full_name or email.split("@")[0].capitalize(),
            auth_provider="google"
        )
        db.add(user_record)
        db.commit()
        db.refresh(user_record)

    token = create_access_token({"sub": user_record.email, "id": user_record.id})

    return AuthResponse(
        status="success",
        message="Google OAuth login successful.",
        access_token=token,
        user=UserProfile(
            id=user_record.id,
            email=user_record.email,
            full_name=user_record.full_name,
            auth_provider=user_record.auth_provider,
            created_at=user_record.created_at.isoformat()
        )
    )


@router.post("/auth/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    if not validate_real_email(email):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")

    user_record = db.query(User).filter(User.email == email).first()
    if not user_record:
        # For security, return success even if user not found
        return {"status": "success", "message": "If an account exists for this email, password reset instructions have been sent."}

    reset_token = create_password_reset_token(email)
    logger.info(f"Generated password reset token for {email}: {reset_token}")

    return {
        "status": "success",
        "message": f"Password reset instructions sent to {email}.",
        "reset_token": reset_token
    }


@router.post("/auth/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    email = verify_password_reset_token(req.reset_token)
    if not email:
        raise HTTPException(status_code=400, detail="Password reset link is invalid or has expired.")

    user_record = db.query(User).filter(User.email == email).first()
    if not user_record:
        raise HTTPException(status_code=404, detail="User account not found.")

    user_record.hashed_password = hash_password(req.new_password)
    db.commit()

    return {"status": "success", "message": "Password has been successfully updated. You may now sign in."}


@router.get("/auth/me", response_model=UserProfile)
def get_current_user_profile(
    request: Request,
    db: Session = Depends(get_db)
):
    current_email = get_current_user_email(request)
    if current_email == "guest_user":
        raise HTTPException(status_code=401, detail="Unauthenticated.")

    user_record = db.query(User).filter(User.email == current_email).first()
    if not user_record:
        raise HTTPException(status_code=404, detail="User not found.")

    return UserProfile(
        id=user_record.id,
        email=user_record.email,
        full_name=user_record.full_name,
        auth_provider=user_record.auth_provider,
        created_at=user_record.created_at.isoformat()
    )



@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    req: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    current_user_email = require_authenticated_user(req)


    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename.")

    filename = os.path.basename(file.filename)
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Unsupported file format. Only PDF files are supported.")

    file_bytes = await file.read()
    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB.")

    try:
        pages_data = extract_pdf_pages(file_bytes)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as err:
        logger.error(f"PDF extraction error: {err}")
        raise HTTPException(status_code=500, detail="Failed to extract text from PDF file.")

    chunks_data = chunk_page_texts(pages_data)
    if not chunks_data:
        raise HTTPException(status_code=400, detail="No readable text chunks could be created from the PDF.")

    doc_record = Document(
        filename=filename,
        file_type="pdf",
        user_id=current_user_email
    )
    db.add(doc_record)
    db.flush()

    created_chunks_count = 0
    for chunk_item in chunks_data:
        content = chunk_item["content"]
        page_num = chunk_item["page_number"]
        chunk_idx = chunk_item["chunk_index"]

        try:
            vector_embedding = get_text_embedding(content)
        except Exception as emb_err:
            logger.warning(f"Embedding creation failed for chunk {chunk_idx}: {emb_err}")
            vector_embedding = None

        chunk_record = DocumentChunk(
            document_id=doc_record.id,
            chunk_index=chunk_idx,
            content=content,
            page_number=page_num,
            embedding=vector_embedding
        )
        chunk_record.set_metadata({
            "filename": filename,
            "page_number": page_num,
            "chunk_index": chunk_idx
        })
        db.add(chunk_record)
        created_chunks_count += 1

    db.commit()

    return DocumentUploadResponse(
        status="success",
        document_id=doc_record.id,
        filename=doc_record.filename,
        chunks_created=created_chunks_count
    )


@router.get("/documents")
def list_documents(
    req: Request,
    db: Session = Depends(get_db)
):
    current_user_email = get_current_user_email(req)
    docs = db.query(Document)\
        .filter((Document.user_id == current_user_email) | (Document.user_id == "default_user"))\
        .order_by(Document.created_at.desc())\
        .all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "chunks_count": len(doc.chunks)
        }
        for doc in docs
    ]


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    req: Request,
    db: Session = Depends(get_db)
):
    current_user_email = get_current_user_email(req)
    doc = db.query(Document)\
        .filter(Document.id == document_id)\
        .filter((Document.user_id == current_user_email) | (Document.user_id == "default_user"))\
        .first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    db.delete(doc)
    db.commit()
    return {"status": "success", "message": f"Document {document_id} deleted successfully."}


@router.get("/analyses", response_model=List[AnalysisHistoryItem])
def list_analysis_history(
    req: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    current_user_email = get_current_user_email(req)
    records = db.query(DecisionAnalysis)\
        .filter((DecisionAnalysis.user_id == current_user_email) | (DecisionAnalysis.user_id == "default_user"))\
        .order_by(DecisionAnalysis.created_at.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()

    return [
        AnalysisHistoryItem(
            id=rec.id,
            problem=rec.problem,
            request_type=rec.request_type,
            response_depth=rec.response_depth,
            multi_agent_used=bool(rec.multi_agent_used),
            created_at=rec.created_at.isoformat() if rec.created_at else ""
        )
        for rec in records
    ]


@router.get("/analyses/{analysis_id}", response_model=AnalysisDetail)
def get_single_analysis(
    analysis_id: int,
    req: Request,
    db: Session = Depends(get_db)
):
    current_user_email = get_current_user_email(req)
    rec = db.query(DecisionAnalysis)\
        .filter(DecisionAnalysis.id == analysis_id)\
        .filter((DecisionAnalysis.user_id == current_user_email) | (DecisionAnalysis.user_id == "default_user"))\
        .first()
    if not rec:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    raw_sources = rec.get_sources()
    sources = [SourceReference(**s) for s in raw_sources] if raw_sources else []

    raw_matrix = rec.get_matrix()
    matrix = DecisionMatrixData(**raw_matrix) if raw_matrix else None

    raw_agents = rec.get_agents_metadata()

    return AnalysisDetail(
        id=rec.id,
        problem=rec.problem,
        context=rec.context or "",
        constraints=rec.constraints or "",
        analysis=rec.analysis,
        request_type=rec.request_type,
        response_depth=rec.response_depth,
        multi_agent_used=bool(rec.multi_agent_used),
        agents_metadata=raw_agents or [],
        sources=sources,
        matrix=matrix,
        created_at=rec.created_at.isoformat() if rec.created_at else ""
    )


@router.delete("/analyses/{analysis_id}")
def delete_analysis(
    analysis_id: int,
    req: Request,
    db: Session = Depends(get_db)
):
    current_user_email = get_current_user_email(req)
    rec = db.query(DecisionAnalysis)\
        .filter(DecisionAnalysis.id == analysis_id)\
        .filter((DecisionAnalysis.user_id == current_user_email) | (DecisionAnalysis.user_id == "default_user"))\
        .first()
    if not rec:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    db.delete(rec)
    db.commit()
    return {"status": "success", "message": f"Analysis {analysis_id} deleted successfully."}


@router.post("/analyze", response_model=DecisionResponse)
async def analyze_decision(
    req: Request,
    request: DecisionRequest,
    db: Session = Depends(get_db)
):
    current_user_email = require_authenticated_user(req)


    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "" or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not configured on the backend server. Please add your secret GEMINI_API_KEY to backend/.env."
        )

    # 1. Determine target document ID if available
    target_doc_id = request.document_id
    if not target_doc_id:
        latest_doc = db.query(Document)\
            .filter((Document.user_id == current_user_email) | (Document.user_id == "default_user"))\
            .order_by(Document.created_at.desc())\
            .first()
        if latest_doc:
            target_doc_id = latest_doc.id

        if latest_doc:
            target_doc_id = latest_doc.id

    # 2. Classify request intent
    classification: RequestClassification = classify_request(
        problem=request.problem,
        context=request.context,
        constraints=request.constraints,
        has_document=bool(target_doc_id),
        response_preference=request.response_preference
    )

    # 3. Perform RAG Retrieval only if required or relevant
    retrieved_chunks = []
    sources_list = []
    evidence_text = ""

    if classification.should_use_rag and target_doc_id:
        try:
            search_query = f"{request.problem} {request.context} {request.constraints}"
            retrieved_chunks = search_relevant_chunks(
                db=db,
                query=search_query,
                document_id=target_doc_id,
                top_k=settings.RAG_TOP_K
            )
        except Exception as ret_err:
            logger.warning(f"Document retrieval warning: {ret_err}")

    if retrieved_chunks:
        evidence_blocks = []
        seen_sources = set()

        for item in retrieved_chunks:
            source_header = f"[Source: {item['filename']}, Page {item['page_number'] or 'N/A'}]"
            evidence_blocks.append(f"{source_header}\n{item['content']}")

            source_key = (item["document_id"], item["filename"], item["page_number"])
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                sources_list.append(SourceReference(
                    document_id=item["document_id"],
                    filename=item["filename"],
                    page_number=item["page_number"],
                    chunk_index=item["chunk_index"]
                ))
        
        evidence_text = "\n\n".join(evidence_blocks)

    analysis_text = ""
    multi_agent_used = False
    agents_metadata = []

    try:
        # 4. Multi-Agent Team Execution or Single-Agent Adaptive Gemini Execution
        if classification.should_use_multi_agent:
            multi_agent_res: MultiAgentResult = await run_multi_agent_pipeline(
                problem=request.problem,
                context=request.context,
                constraints=request.constraints,
                evidence_text=evidence_text
            )
            analysis_text = multi_agent_res.synthesized_analysis
            multi_agent_used = multi_agent_res.multi_agent_used
            agents_metadata = multi_agent_res.agents_metadata
        else:
            # Single-Agent Path
            prompt = build_adaptive_prompt(
                problem=request.problem,
                context=request.context,
                constraints=request.constraints,
                classification=classification,
                evidence_text=evidence_text
            )
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            model_candidates = [
                "models/gemini-3.6-flash",
                "models/gemini-flash-latest",
                "models/gemini-3.7-flash",
                "models/gemini-3.5-flash",
                "models/gemini-3.1-flash-lite",
                "models/gemini-2.5-pro",
                "gemini-3.6-flash",
                "gemini-flash-latest"
            ]
            response = None
            last_error = None

            for model in model_candidates:
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt,
                    )
                    if response and response.text:
                        break
                except Exception as err:
                    last_error = err
                    continue

            if not response or not response.text:
                if last_error:
                    raise last_error
                raise Exception("No text response returned from Gemini API.")

            analysis_text = response.text.strip()

        # 5. Decision Matrix calculation if required
        matrix_data: Optional[DecisionMatrixData] = None
        if classification.should_use_matrix and len(classification.options_detected) >= 2:
            try:
                matrix_data = generate_and_calculate_matrix(
                    options=classification.options_detected,
                    problem=request.problem,
                    context=request.context,
                    constraints=request.constraints
                )
            except Exception as matrix_err:
                logger.warning(f"Matrix calculation warning: {matrix_err}")

        # 6. Automatically save successful analysis to database
        saved_id = None
        try:
            saved_record = DecisionAnalysis(
                user_id=current_user_email,
                problem=request.problem,

                context=request.context or "",
                constraints=request.constraints or "",
                analysis=analysis_text,
                request_type=classification.request_type,
                response_depth=classification.response_depth,
                multi_agent_used=multi_agent_used
            )
            saved_record.set_sources(sources_list if evidence_text else [])
            saved_record.set_matrix(matrix_data)
            saved_record.set_agents_metadata(agents_metadata)

            db.add(saved_record)
            db.commit()
            db.refresh(saved_record)
            saved_id = saved_record.id
        except Exception as save_err:
            db.rollback()
            logger.error(f"Failed to persist analysis to database: {save_err}")

        return DecisionResponse(
            status="success",
            message="Adaptive multi-agent response generated and saved successfully" if multi_agent_used else "Adaptive response generated and saved successfully",
            analysis_id=saved_id,
            problem=request.problem,
            context=request.context,
            constraints=request.constraints,
            analysis=analysis_text,
            request_type=classification.request_type,
            response_depth=classification.response_depth,
            multi_agent_used=multi_agent_used,
            agents_metadata=agents_metadata,
            sources=sources_list if evidence_text else [],
            matrix=matrix_data
        )

    except Exception as e:
        err_msg = str(e)
        logger.error(f"Error generating analysis: {err_msg}")
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
            raise HTTPException(
                status_code=429,
                detail="Google Gemini API free tier request limit was temporarily reached. Please wait a few moments and try your request again."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate AI response: {err_msg}"
        )

