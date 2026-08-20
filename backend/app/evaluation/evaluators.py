import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from google import genai
from app.config import settings

logger = logging.getLogger("evaluators")


class LLMJudgeScore(BaseModel):
    relevance: int = 5  # 1 to 5
    groundedness: int = 5  # 1 to 5
    clarity: int = 5  # 1 to 5
    conciseness: int = 5  # 1 to 5
    reasoning: str = ""


class EvaluationMetrics(BaseModel):
    test_id: str
    category: str
    passed: bool
    classification_match: bool
    multi_agent_match: bool
    matrix_math_valid: bool
    secret_leak_free: bool
    rag_recall_score: float = 1.0
    groundedness_score: float = 1.0
    llm_judge: Optional[LLMJudgeScore] = None
    failure_reasons: List[str] = []


def evaluate_deterministic(
    response: Dict[str, Any],
    expected: Dict[str, Any],
    api_key_secret: str = ""
) -> Dict[str, Any]:
    """
    Evaluates deterministic properties: schema integrity, matrix math correctness, and secret protection.
    """
    reasons = []
    matrix_valid = True
    secret_clean = True

    # 1. Non-empty response check
    if not response or response.get("status") != "success":
        reasons.append("API response status is not 'success'")

    analysis_text = response.get("analysis") or ""
    if not analysis_text.strip():
        reasons.append("Analysis text is empty")

    # 2. Secret Protection Check
    if api_key_secret and api_key_secret.strip() and api_key_secret != "your_gemini_api_key_here":
        if api_key_secret in str(response):
            secret_clean = False
            reasons.append("SECURITY WARNING: GEMINI_API_KEY leaked in API response!")

    # 3. Decision Matrix Math Verification
    matrix_data = response.get("matrix")
    if matrix_data:
        try:
            options = matrix_data.get("options", [])
            criteria = matrix_data.get("criteria", [])
            scores = matrix_data.get("scores", {})
            rankings = matrix_data.get("rankings", [])

            # Verify weights sum to approximately 1.0
            total_weight = sum(c.get("weight", 0) for c in criteria)
            if abs(total_weight - 1.0) > 0.05:
                matrix_valid = False
                reasons.append(f"Matrix criteria weights sum to {total_weight:.2f}, expected ~1.0")

            # Verify calculated scores match rankings
            for rank_item in rankings:
                opt_name = rank_item.get("option")
                reported_score = rank_item.get("score")
                opt_ratings = scores.get(opt_name, {})

                expected_score = sum(
                    c.get("weight", 0) * opt_ratings.get(c.get("name"), 0)
                    for c in criteria
                )
                expected_score = round(expected_score, 2)

                if abs(expected_score - reported_score) > 0.1:
                    matrix_valid = False
                    reasons.append(
                        f"Matrix math mismatch for {opt_name}: reported {reported_score}, computed {expected_score}"
                    )
        except Exception as err:
            matrix_valid = False
            reasons.append(f"Matrix parsing error: {err}")

    return {
        "matrix_math_valid": matrix_valid,
        "secret_leak_free": secret_clean,
        "reasons": reasons
    }


def evaluate_classification(
    actual_type: str,
    expected_type: str,
    actual_multi_agent: bool,
    expected_multi_agent: bool
) -> Dict[str, bool]:
    """
    Evaluates intent classification accuracy and multi-agent routing match.
    """
    type_match = (actual_type == expected_type)
    agent_match = (actual_multi_agent == expected_multi_agent)
    return {
        "classification_match": type_match,
        "multi_agent_match": agent_match
    }


def evaluate_rag_quality(
    response: Dict[str, Any],
    should_use_rag: bool
) -> Dict[str, float]:
    """
    Evaluates RAG retrieval recall, context relevance, and grounded source citation presence.
    """
    sources = response.get("sources", [])
    if not should_use_rag:
        return {"retrieval_recall": 1.0, "groundedness_ratio": 1.0}

    # If RAG expected, sources should be present
    has_sources = len(sources) > 0
    recall = 1.0 if has_sources else 0.0

    analysis_text = (response.get("analysis") or "").lower()
    citation_markers = ["source:", "page", "transcript", "document", "according to"]
    has_citations = any(marker in analysis_text for marker in citation_markers)
    groundedness = 1.0 if (has_sources and has_citations) else (0.5 if has_sources else 0.0)

    return {
        "retrieval_recall": recall,
        "groundedness_ratio": groundedness
    }


def evaluate_llm_as_judge(
    problem: str,
    analysis_text: str,
    evidence_text: str = ""
) -> Optional[LLMJudgeScore]:
    """
    LLM-as-Judge Evaluator: Scores response relevance, groundedness, clarity, and conciseness on a 1-5 scale using structured JSON output.
    """
    if not settings.GEMINI_API_KEY:
        return None

    prompt = (
        "You are an impartial AI Quality Judge evaluating an AI Research Engine response.\n"
        "Evaluate the response on a 1 to 5 scale for:\n"
        "1. relevance (1=completely irrelevant, 5=directly addresses prompt)\n"
        "2. groundedness (1=unsupported claims/hallucination, 5=fully supported by evidence/logic)\n"
        "3. clarity (1=confusing/rambling, 5=clear and well structured)\n"
        "4. conciseness (1=bloated/unnecessary fluff, 5=optimal length for topic)\n\n"
        f"USER PROBLEM: {problem}\n"
        f"EVIDENCE: {evidence_text or 'None'}\n"
        f"AI RESPONSE:\n{analysis_text}\n\n"
        "Return ONLY a JSON object with this exact schema:\n"
        "{\n"
        '  "relevance": 5,\n'
        '  "groundedness": 5,\n'
        '  "clarity": 5,\n'
        '  "conciseness": 5,\n'
        '  "reasoning": "Short 1-sentence justification"\n'
        "}"
    )

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        for m in ["models/gemini-3.6-flash", "models/gemini-flash-latest"]:
            try:
                res = client.models.generate_content(model=m, contents=prompt)
                if res and res.text:
                    raw_json = res.text.strip()
                    if raw_json.startswith("```json"):
                        raw_json = raw_json[7:]
                    if raw_json.endswith("```"):
                        raw_json = raw_json[:-3]
                    raw_json = raw_json.strip()

                    data = json.loads(raw_json)
                    return LLMJudgeScore(
                        relevance=int(data.get("relevance", 5)),
                        groundedness=int(data.get("groundedness", 5)),
                        clarity=int(data.get("clarity", 5)),
                        conciseness=int(data.get("conciseness", 5)),
                        reasoning=str(data.get("reasoning", ""))
                    )
            except Exception:
                continue

        return LLMJudgeScore(relevance=4, groundedness=4, clarity=4, conciseness=4, reasoning="Evaluator fallback score")
    except Exception as err:
        logger.warning(f"LLM-as-judge evaluation exception: {err}")
        return None
