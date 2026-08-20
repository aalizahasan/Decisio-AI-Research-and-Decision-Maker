import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List

from app.config import settings
from app.db.database import SessionLocal, init_db
from app.routes import analyze_decision, DecisionRequest
from app.evaluation.evaluators import (
    evaluate_deterministic,
    evaluate_classification,
    evaluate_rag_quality,
    evaluate_llm_as_judge,
    EvaluationMetrics
)

logger = logging.getLogger("evaluation_runner")

DATASET_PATH = os.path.join(os.path.dirname(__file__), "dataset.json")
REPORT_PATH = os.path.join(os.path.dirname(__file__), "latest_report.json")


async def run_evaluation_suite() -> Dict[str, Any]:
    """
    Runs the full evaluation benchmark suite over dataset.json,
    computes deterministic and LLM-as-judge metrics, outputs console summary,
    and writes machine-readable latest_report.json.
    """
    print("\n==================================================")
    print(" [EVAL] AI RESEARCH & DECISION PLATFORM - EVALUATION SUITE")
    print("==================================================\n")


    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Evaluation dataset not found at {DATASET_PATH}")

    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    init_db()
    db = SessionLocal()

    results: List[EvaluationMetrics] = []
    total_tests = len(dataset)
    passed_count = 0

    class_matches = 0
    agent_matches = 0
    matrix_math_passes = 0
    secret_passes = 0
    rag_recalls = []
    groundedness_scores = []

    judge_relevance_list = []
    judge_groundedness_list = []
    judge_clarity_list = []
    judge_conciseness_list = []

    start_time = datetime.utcnow()

    for idx, test_case in enumerate(dataset, start=1):
        test_id = test_case["id"]
        category = test_case["category"]
        inp = test_case["input"]
        expected = test_case["expected"]

        print(f"[{idx}/{total_tests}] Running test '{test_id}' ({category})...")

        req = DecisionRequest(
            problem=inp["problem"],
            context=inp.get("context", ""),
            constraints=inp.get("constraints", "")
        )

        try:
            # Execute backend analyze route
            res_obj = await analyze_decision(req, db)
            res_dict = res_obj.dict()

            # 1. Deterministic Evaluation
            det_eval = evaluate_deterministic(res_dict, expected, api_key_secret=settings.GEMINI_API_KEY)
            
            # 2. Classification Evaluation
            class_eval = evaluate_classification(
                actual_type=res_obj.request_type,
                expected_type=expected["request_type"],
                actual_multi_agent=res_obj.multi_agent_used,
                expected_multi_agent=expected.get("should_use_multi_agent", False)
            )

            # 3. RAG Quality Evaluation
            rag_eval = evaluate_rag_quality(
                res_dict,
                should_use_rag=expected.get("should_use_rag", False)
            )

            # 4. LLM-as-Judge Evaluation
            judge_eval = await asyncio.to_thread(
                evaluate_llm_as_judge,
                problem=req.problem,
                analysis_text=res_obj.analysis or ""
            )

            # Check overall test pass criteria
            test_passed = (
                det_eval["secret_leak_free"] and
                det_eval["matrix_math_valid"] and
                class_eval["classification_match"] and
                class_eval["multi_agent_match"]
            )

            if test_passed:
                passed_count += 1

            if class_eval["classification_match"]:
                class_matches += 1
            if class_eval["multi_agent_match"]:
                agent_matches += 1
            if det_eval["matrix_math_valid"]:
                matrix_math_passes += 1
            if det_eval["secret_leak_free"]:
                secret_passes += 1

            rag_recalls.append(rag_eval["retrieval_recall"])
            groundedness_scores.append(rag_eval["groundedness_ratio"])

            if judge_eval:
                judge_relevance_list.append(judge_eval.relevance)
                judge_groundedness_list.append(judge_eval.groundedness)
                judge_clarity_list.append(judge_eval.clarity)
                judge_conciseness_list.append(judge_eval.conciseness)

            metrics = EvaluationMetrics(
                test_id=test_id,
                category=category,
                passed=test_passed,
                classification_match=class_eval["classification_match"],
                multi_agent_match=class_eval["multi_agent_match"],
                matrix_math_valid=det_eval["matrix_math_valid"],
                secret_leak_free=det_eval["secret_leak_free"],
                rag_recall_score=rag_eval["retrieval_recall"],
                groundedness_score=rag_eval["groundedness_ratio"],
                llm_judge=judge_eval,
                failure_reasons=det_eval["reasons"]
            )
            results.append(metrics)

            status_symbol = "[PASS]" if test_passed else "[FAIL]"
            print(f"    Status: {status_symbol} | Intent: {res_obj.request_type} | Multi-Agent: {res_obj.multi_agent_used}")

        except Exception as err:
            logger.error(f"Error evaluating test '{test_id}': {err}")
            results.append(EvaluationMetrics(
                test_id=test_id,
                category=category,
                passed=False,
                classification_match=False,
                multi_agent_match=False,
                matrix_math_valid=False,
                secret_leak_free=True,
                failure_reasons=[str(err)]
            ))
            print(f"    Status: [ERROR] ({err})")

    end_time = datetime.utcnow()
    duration_sec = round((end_time - start_time).total_seconds(), 2)

    # Calculate Aggregate Metrics
    classification_acc = round((class_matches / total_tests) * 100, 1)
    multi_agent_acc = round((agent_matches / total_tests) * 100, 1)
    matrix_math_acc = round((matrix_math_passes / total_tests) * 100, 1)
    secret_safety_acc = round((secret_passes / total_tests) * 100, 1)

    avg_rag_recall = round(sum(rag_recalls) / len(rag_recalls) * 100, 1) if rag_recalls else 100.0
    avg_groundedness = round(sum(groundedness_scores) / len(groundedness_scores) * 100, 1) if groundedness_scores else 100.0

    avg_judge_rel = round(sum(judge_relevance_list) / len(judge_relevance_list), 2) if judge_relevance_list else 5.0
    avg_judge_grd = round(sum(judge_groundedness_list) / len(judge_groundedness_list), 2) if judge_groundedness_list else 5.0
    avg_judge_clr = round(sum(judge_clarity_list) / len(judge_clarity_list), 2) if judge_clarity_list else 5.0
    avg_judge_cnc = round(sum(judge_conciseness_list) / len(judge_conciseness_list), 2) if judge_conciseness_list else 5.0

    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "duration_seconds": duration_sec,
        "summary": {
            "total_tests": total_tests,
            "passed": passed_count,
            "failed": total_tests - passed_count,
            "pass_rate_percent": round((passed_count / total_tests) * 100, 1)
        },
        "metrics": {
            "classification_accuracy_percent": classification_acc,
            "multi_agent_routing_accuracy_percent": multi_agent_acc,
            "matrix_math_validity_percent": matrix_math_acc,
            "secret_protection_percent": secret_safety_acc,
            "rag_retrieval_recall_percent": avg_rag_recall,
            "rag_groundedness_percent": avg_groundedness
        },
        "llm_as_judge_scores": {
            "relevance_out_of_5": avg_judge_rel,
            "groundedness_out_of_5": avg_judge_grd,
            "clarity_out_of_5": avg_judge_clr,
            "conciseness_out_of_5": avg_judge_cnc
        },
        "detailed_test_results": [r.dict() for r in results]
    }

    # Save machine-readable report JSON
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Print Console Summary
    print("\n==================================================")
    print(" [SUMMARY] EVALUATION SUMMARY REPORT")
    print("==================================================")
    print(f"Total Tests Executed:  {total_tests}")
    print(f"Passed:                {passed_count} / {total_tests} ({report['summary']['pass_rate_percent']}%)")
    print(f"Failed:                {total_tests - passed_count}")
    print(f"Execution Duration:    {duration_sec}s")
    print("--------------------------------------------------")
    print(" ACCURACY & RELIABILITY SIGNALS:")
    print(f"  * Intent Classification Accuracy:   {classification_acc}%")
    print(f"  * Multi-Agent Routing Accuracy:     {multi_agent_acc}%")
    print(f"  * Matrix Deterministic Math:        {matrix_math_acc}%")
    print(f"  * API Secret Protection:            {secret_safety_acc}%")
    print("--------------------------------------------------")
    print(" RAG & GROUNDEDNESS SIGNALS:")
    print(f"  * RAG Retrieval Recall:            {avg_rag_recall}%")
    print(f"  * RAG Evidence Groundedness:        {avg_groundedness}%")
    print("--------------------------------------------------")
    print(" LLM-AS-JUDGE SCORES (1.0 - 5.0):")
    print(f"  * Relevance Score:                  {avg_judge_rel} / 5.0")
    print(f"  * Groundedness Score:               {avg_judge_grd} / 5.0")
    print(f"  * Response Clarity Score:           {avg_judge_clr} / 5.0")
    print(f"  * Conciseness Score:                {avg_judge_cnc} / 5.0")
    print("==================================================\n")

    return report

