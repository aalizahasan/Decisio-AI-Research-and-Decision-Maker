import re
import logging
from typing import Optional, List
from pydantic import BaseModel

logger = logging.getLogger("classifier_service")


class RequestClassification(BaseModel):
    request_type: str  # "SIMPLE_QUESTION", "EXPLANATION", "ADVICE", "COMPARISON", "DOCUMENT_ANALYSIS", "COMPLEX_DECISION"
    response_depth: str  # "concise", "standard", "detailed"
    should_use_rag: bool
    should_use_matrix: bool
    should_use_multi_agent: bool = False
    options_detected: List[str] = []


def extract_comparison_options(text: str) -> List[str]:
    """
    Extracts potential comparison options/alternatives from query text using regex heuristics.
    """
    options = []
    
    # Pattern: "X vs Y" or "X versus Y" or "X vs. Y"
    vs_match = re.search(r'([\w\s\.\+]+?)\s+(?:vs\.?|versus)\s+([\w\s\.\+]+)', text, re.IGNORECASE)
    if vs_match:
        opt1 = vs_match.group(1).strip()
        opt2 = vs_match.group(2).strip()
        # Clean leading words like "should I choose", "compare"
        opt1 = re.sub(r'^(?:should\s+i\s+(?:choose|use|learn|buy)|compare|difference\s+between)\s+', '', opt1, flags=re.IGNORECASE).strip()
        opt2 = re.sub(r'\s+\?.*$', '', opt2).strip()
        if opt1 and opt2 and len(opt1) < 40 and len(opt2) < 40:
            options = [opt1, opt2]
            return options

    # Pattern: "should I choose X or Y" or "learn X or Y"
    or_match = re.search(r'(?:choose|use|learn|pick|select|between)\s+([\w\s\.\+]+?)\s+or\s+([\w\s\.\+]+)', text, re.IGNORECASE)
    if or_match:
        opt1 = or_match.group(1).strip()
        opt2 = or_match.group(2).strip()
        opt2 = re.sub(r'\s+\?.*$', '', opt2).strip()
        if opt1 and opt2 and len(opt1) < 40 and len(opt2) < 40:
            options = [opt1, opt2]
            return options

    return options


def classify_request(
    problem: str,
    context: str = "",
    constraints: str = "",
    has_document: bool = False,
    response_preference: Optional[str] = "auto"
) -> RequestClassification:
    """
    Determines request type, target response depth, RAG usage, matrix necessity, and multi-agent routing.
    """
    full_text = f"{problem} {context} {constraints}".strip()
    full_text_lower = full_text.lower()
    prob_lower = problem.lower().strip()

    # 1. Determine base response depth preference
    depth = "standard"
    if response_preference in ["concise", "detailed"]:
        depth = response_preference
    elif any(kw in full_text_lower for kw in ["in detail", "thorough", "comprehensive", "deep dive", "elaborate"]):
        depth = "detailed"
    elif any(kw in full_text_lower for kw in ["briefly", "concise", "short answer", "in short", "summary"]):
        depth = "concise"

    # 2. Extract potential comparison options
    options = extract_comparison_options(problem)
    if not options and (" vs " in full_text_lower or " versus " in full_text_lower or " or " in full_text_lower):
        options = extract_comparison_options(full_text)

    # Multi-agent complex triggers
    multi_agent_triggers = [
        "migrate", "aws to azure", "azure to aws", "cloud migration", "startup",
        "architecture", "trade-off", "tradeoff", "risk", "scalability", "team expertise",
        "vendor selection", "multi-agent", "multi agent", "high stakes", "infrastructure"
    ]
    has_multi_agent_keywords = any(kw in full_text_lower for kw in multi_agent_triggers)

    # 3. Document Analysis Intent
    doc_keywords = ["report", "document", "pdf", "file", "attached", "section", "page", "risk", "find in document", "according to"]
    is_doc_focused = has_document and any(kw in full_text_lower for kw in doc_keywords)

    if is_doc_focused:
        return RequestClassification(
            request_type="DOCUMENT_ANALYSIS",
            response_depth=depth if depth != "standard" else "standard",
            should_use_rag=True,
            should_use_matrix=len(options) >= 2,
            should_use_multi_agent=has_multi_agent_keywords or len(full_text) > 180,
            options_detected=options
        )

    # 4. Simple Question Intent
    simple_starters = ["what is", "what are", "who is", "when did", "define", "meaning of"]
    is_short = len(prob_lower) < 70 and len(context.strip()) < 30
    is_simple = any(prob_lower.startswith(s) for s in simple_starters) and len(options) < 2

    if is_simple and is_short and not has_document:
        return RequestClassification(
            request_type="SIMPLE_QUESTION",
            response_depth="concise" if depth == "auto" or depth == "standard" else depth,
            should_use_rag=False,
            should_use_matrix=False,
            should_use_multi_agent=False,
            options_detected=[]
        )

    # 5. Explanation Intent
    explain_keywords = ["explain", "how does", "how do", "concept of", "understand", "overview of"]
    if any(kw in prob_lower for kw in explain_keywords) and len(options) < 2:
        return RequestClassification(
            request_type="EXPLANATION",
            response_depth="concise" if (is_short and depth == "standard") else depth,
            should_use_rag=has_document,
            should_use_matrix=False,
            should_use_multi_agent=False,
            options_detected=[]
        )

    # 6. Advice / Strategy Intent
    advice_keywords = ["how can i", "how to improve", "tips for", "advice on", "best way to", "strategy for", "how should i"]
    if any(kw in prob_lower for kw in advice_keywords) and len(options) < 2:
        return RequestClassification(
            request_type="ADVICE",
            response_depth=depth,
            should_use_rag=has_document,
            should_use_matrix=False,
            should_use_multi_agent=has_multi_agent_keywords,
            options_detected=[]
        )

    # 7. Comparison Intent
    is_comparison = len(options) >= 2 or any(kw in prob_lower for kw in ["vs", "versus", "compare", "difference between", "better choice"])
    if is_comparison:
        return RequestClassification(
            request_type="COMPARISON",
            response_depth=depth,
            should_use_rag=has_document,
            should_use_matrix=len(options) >= 2,
            should_use_multi_agent=has_multi_agent_keywords or len(full_text) > 150,
            options_detected=options
        )

    # 8. Complex Decision Intent
    is_complex = len(full_text) > 180 or has_multi_agent_keywords
    if is_complex:
        return RequestClassification(
            request_type="COMPLEX_DECISION",
            response_depth="detailed" if depth == "standard" or depth == "auto" else depth,
            should_use_rag=has_document,
            should_use_matrix=len(options) >= 2,
            should_use_multi_agent=True,
            options_detected=options
        )

    # Fallback default
    return RequestClassification(
        request_type="ADVICE" if len(options) < 2 else "COMPARISON",
        response_depth=depth,
        should_use_rag=has_document,
        should_use_matrix=len(options) >= 2,
        should_use_multi_agent=has_multi_agent_keywords,
        options_detected=options
    )
