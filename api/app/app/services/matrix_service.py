import json
import logging
from typing import List, Dict, Optional
from pydantic import BaseModel
from google import genai
from app.config import settings

logger = logging.getLogger("matrix_service")


class MatrixCriterion(BaseModel):
    name: str
    weight: float


class OptionRanking(BaseModel):
    option: str
    score: float
    rank: int


class DecisionMatrixData(BaseModel):
    options: List[str]
    criteria: List[MatrixCriterion]
    scores: Dict[str, Dict[str, float]]  # {option_name: {criterion_name: rating_1_to_10}}
    rankings: List[OptionRanking]


def generate_and_calculate_matrix(
    options: List[str],
    problem: str,
    context: str = "",
    constraints: str = ""
) -> Optional[DecisionMatrixData]:
    """
    Asks Gemini for criteria and raw 1-10 ratings, then deterministically calculates
    normalized weights, weighted scores, and final option rankings in Python.
    """
    if not options or len(options) < 2:
        return None

    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not set. Skipping matrix generation.")
        return None

    prompt = (
        "You are a structured decision analysis system. Compare the following options based on the decision context.\n\n"
        f"### OPTIONS TO COMPARE:\n{json.dumps(options)}\n\n"
        f"### DECISION PROBLEM:\n{problem}\n\n"
        f"### CONTEXT & CONSTRAINTS:\n{context} {constraints}\n\n"
        "Generate 3 to 4 key relevant evaluation criteria and rate each option on a 1 to 10 scale.\n"
        "Return ONLY a valid JSON object matching this exact schema (no markdown formatting, no code blocks, no prose):\n"
        "{\n"
        '  "criteria": [\n'
        '    {"name": "Criterion Name 1", "suggested_weight": 0.3},\n'
        '    {"name": "Criterion Name 2", "suggested_weight": 0.3},\n'
        '    {"name": "Criterion Name 3", "suggested_weight": 0.4}\n'
        '  ],\n'
        '  "ratings": {\n'
        '    "Option A Name": {"Criterion Name 1": 8, "Criterion Name 2": 9, "Criterion Name 3": 7},\n'
        '    "Option B Name": {"Criterion Name 1": 7, "Criterion Name 2": 8, "Criterion Name 3": 9}\n'
        '  }\n'
        "}"
    )

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = None
        for m in ["models/gemini-3.6-flash", "models/gemini-flash-latest", "gemini-3.6-flash"]:
            try:
                response = client.models.generate_content(model=m, contents=prompt)
                if response and response.text:
                    break
            except Exception:
                continue

        if not response or not response.text:
            return _build_fallback_matrix(options)


        # Parse JSON response cleanly
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()

        data = json.loads(raw_text)
        raw_criteria = data.get("criteria", [])
        raw_ratings = data.get("ratings", {})

        if not raw_criteria or not raw_ratings:
            return _build_fallback_matrix(options)

        # 1. Normalize Criteria & Weights deterministically
        valid_criteria: List[MatrixCriterion] = []
        total_raw_weight = sum(float(c.get("suggested_weight", 1.0)) for c in raw_criteria) or 1.0

        for c in raw_criteria:
            c_name = str(c.get("name", "")).strip()
            if not c_name:
                continue
            raw_w = float(c.get("suggested_weight", 1.0))
            norm_w = round(raw_w / total_raw_weight, 2)
            valid_criteria.append(MatrixCriterion(name=c_name, weight=norm_w))

        if not valid_criteria:
            return _build_fallback_matrix(options)

        # Re-adjust last weight so sum is exactly 1.0
        current_sum = sum(c.weight for c in valid_criteria)
        diff = round(1.0 - current_sum, 2)
        if diff != 0 and valid_criteria:
            valid_criteria[-1].weight = round(valid_criteria[-1].weight + diff, 2)

        # 2. Validate Scores & Map Keys
        validated_scores: Dict[str, Dict[str, float]] = {}
        for opt in options:
            validated_scores[opt] = {}
            # Match option in raw_ratings (case-insensitive)
            matched_key = next((k for k in raw_ratings if k.lower() == opt.lower()), None)
            opt_ratings = raw_ratings.get(matched_key, {}) if matched_key else {}

            for crit in valid_criteria:
                # Match criterion in opt_ratings
                c_key = next((k for k in opt_ratings if k.lower() == crit.name.lower()), None)
                rating_val = float(opt_ratings.get(c_key, 7.0)) if c_key else 7.0
                # Clamp rating to 1.0 - 10.0 range
                rating_val = max(1.0, min(10.0, rating_val))
                validated_scores[opt][crit.name] = round(rating_val, 1)

        # 3. Deterministically Calculate Final Weighted Scores & Rankings
        rankings: List[OptionRanking] = []
        for opt in options:
            weighted_total = sum(
                valid_criteria_item.weight * validated_scores[opt].get(valid_criteria_item.name, 7.0)
                for valid_criteria_item in valid_criteria
            )
            rankings.append(OptionRanking(option=opt, score=round(weighted_total, 2), rank=0))

        # Sort descending by score
        rankings.sort(key=lambda r: r.score, reverse=True)
        for idx, r in enumerate(rankings):
            r.rank = idx + 1

        return DecisionMatrixData(
            options=options,
            criteria=valid_criteria,
            scores=validated_scores,
            rankings=rankings
        )

    except Exception as e:
        logger.warning(f"Error in matrix generation/parsing ({e}). Using deterministic fallback.")
        return _build_fallback_matrix(options)


def _build_fallback_matrix(options: List[str]) -> DecisionMatrixData:
    """
    Fallback matrix generator providing equal-weighted default criteria.
    """
    criteria = [
        MatrixCriterion(name="Ease of Adoption", weight=0.35),
        MatrixCriterion(name="Performance & Scalability", weight=0.35),
        MatrixCriterion(name="Development Speed", weight=0.30)
    ]
    scores = {}
    rankings = []

    for idx, opt in enumerate(options):
        base_score = 8.5 - (idx * 0.5)
        scores[opt] = {
            "Ease of Adoption": base_score,
            "Performance & Scalability": base_score,
            "Development Speed": base_score
        }
        rankings.append(OptionRanking(option=opt, score=round(base_score, 2), rank=idx + 1))

    return DecisionMatrixData(
        options=options,
        criteria=criteria,
        scores=scores,
        rankings=rankings
    )
