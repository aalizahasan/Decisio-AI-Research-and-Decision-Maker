import logging
from app.services.classifier_service import RequestClassification

logger = logging.getLogger("prompt_service")


def build_adaptive_prompt(
    problem: str,
    context: str,
    constraints: str,
    classification: RequestClassification,
    evidence_text: str = ""
) -> str:
    """
    Constructs a tailor-made Gemini prompt adhering strictly to:
    'Give the smallest answer that completely solves the user's problem.'
    """
    req_type = classification.request_type
    depth = classification.response_depth

    # Core System Directive
    system_rules = (
        "CORE INSTRUCTIONS:\n"
        "- Answer the user's actual question directly.\n"
        "- Be concise by default. Give the smallest answer that completely solves the user's problem.\n"
        "- Do NOT use generic AI introductions (e.g. 'Certainly!', 'Here is a comprehensive analysis...').\n"
        "- Do NOT use generic AI conclusions (e.g. 'In conclusion...', 'To summarize...').\n"
        "- Do NOT repeat the user's problem statement.\n"
        "- Do NOT create unnecessary markdown headings unless they genuinely improve readability.\n"
        "- Do NOT add artificial filler or generic boilerplate text.\n\n"
    )

    # Category-Specific Instructions
    if req_type == "SIMPLE_QUESTION":
        type_instructions = (
            "RESPONSE STYLE:\n"
            "- Provide a single, direct, clear answer (1 to 2 short paragraphs).\n"
            "- Do NOT use any headings or bullet points.\n"
        )
    elif req_type == "EXPLANATION":
        type_instructions = (
            "RESPONSE STYLE:\n"
            "- Explain the concept clearly and simply.\n"
            "- Use short paragraphs or 2-3 bullet points only if helpful.\n"
            "- Avoid excessive technical jargon or bloated filler.\n"
        )
    elif req_type == "ADVICE":
        type_instructions = (
            "RESPONSE STYLE:\n"
            "- Provide practical, logical, actionable suggestions.\n"
            "- Use bullet points or numbered steps for clarity.\n"
            "- Do NOT force artificial comparison criteria or option scoring.\n"
        )
    elif req_type == "COMPARISON":
        type_instructions = (
            "RESPONSE STYLE:\n"
            "- Directly compare the alternatives based on user context.\n"
            "- Highlight key trade-offs (pros/cons) concisely.\n"
            "- Give a clear, decisive recommendation for the user's situation.\n"
        )
    elif req_type == "DOCUMENT_ANALYSIS":
        type_instructions = (
            "RESPONSE STYLE:\n"
            "- Answer the question based strictly on the RETRIEVED DOCUMENT EVIDENCE.\n"
            "- Clearly distinguish documented facts from assumptions.\n"
            "- If evidence is insufficient, state so directly.\n"
        )
    elif req_type == "COMPLEX_DECISION":
        type_instructions = (
            "RESPONSE STYLE:\n"
            "- Provide a structured, evidence-based strategic evaluation.\n"
            "- Include key trade-offs, strategic risks, and a clear recommendation.\n"
        )
    else:
        type_instructions = "RESPONSE STYLE:\n- Answer directly and concisely.\n"

    # Depth Directive
    if depth == "concise":
        depth_instruction = "DEPTH: Maximum 2 short paragraphs. Keep it as brief as possible while fully answering."
    elif depth == "detailed":
        depth_instruction = "DEPTH: Provide thorough reasoning and details, but eliminate all filler and repetition."
    else:
        depth_instruction = "DEPTH: Standard balanced depth."

    # Evidence Context
    evidence_block = f"\n### RETRIEVED DOCUMENT EVIDENCE:\n{evidence_text}\n" if evidence_text else ""

    prompt = (
        f"{system_rules}"
        f"{type_instructions}"
        f"{depth_instruction}\n\n"
        f"### USER DECISION STATEMENT:\n{problem}\n\n"
        f"### RELEVANT CONTEXT:\n{context}\n\n"
        f"### CONSTRAINTS:\n{constraints}\n"
        f"{evidence_block}\n"
        "Provide your clean, direct response now."
    )

    return prompt
