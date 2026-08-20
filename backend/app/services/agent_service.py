import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from google import genai
from app.config import settings
from app.services.classifier_service import RequestClassification

logger = logging.getLogger("agent_service")


class AgentFinding(BaseModel):
    claim: str
    importance: str = "medium"  # "high", "medium", "low"
    reasoning: str
    evidence_type: str = "INFERENCE"  # "FACT", "INFERENCE", "ASSUMPTION"


class AgentOutput(BaseModel):
    agent_role: str  # "research", "risk", "tradeoff"
    status: str = "success"  # "success", "error"
    findings: List[AgentFinding] = []
    summary: str = ""
    error_message: Optional[str] = None


class MultiAgentResult(BaseModel):
    multi_agent_used: bool = True
    agent_outputs: List[AgentOutput] = []
    synthesized_analysis: str = ""
    agents_metadata: List[Dict[str, str]] = []


def _call_gemini_api(prompt: str) -> Optional[str]:
    """
    Helper function to invoke Gemini API with model candidate fallbacks.
    """
    if not settings.GEMINI_API_KEY:
        return None

    try:
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


        for m in model_candidates:
            try:
                response = client.models.generate_content(model=m, contents=prompt)
                if response and response.text:
                    return response.text.strip()
            except Exception:
                continue

        return None
    except Exception as err:
        logger.error(f"Gemini API invocation error: {err}")
        return None


async def run_research_agent(
    problem: str,
    context: str,
    constraints: str,
    evidence_text: str
) -> AgentOutput:
    """
    Research Agent: Focuses on factual considerations, RAG evidence grounding, and supporting claims.
    """
    prompt = (
        "You are a specialized Research Agent in a Multi-Agent AI system.\n"
        "YOUR ROLE: Identify factual considerations, technical capabilities, and empirical evidence.\n"
        "EVIDENCE DISCIPLINE: Tag every claim as either FACT (supported by evidence), INFERENCE (logical conclusion), or ASSUMPTION.\n\n"
        f"PROBLEM: {problem}\n"
        f"CONTEXT: {context or 'None'}\n"
        f"CONSTRAINTS: {constraints or 'None'}\n"
        f"RELEVANT EVIDENCE: {evidence_text or 'No attached PDF evidence available.'}\n\n"
        "Format your output as a clear 2-3 paragraph research report highlighting factual considerations and supporting data."
    )

    try:
        # Run blocking call in thread pool
        text_res = await asyncio.to_thread(_call_gemini_api, prompt)
        if not text_res:
            return AgentOutput(
                agent_role="research",
                status="error",
                error_message="Research Agent API call returned empty text."
            )

        return AgentOutput(
            agent_role="research",
            status="success",
            summary=text_res,
            findings=[
                AgentFinding(
                    claim="Factual considerations extracted",
                    importance="high",
                    reasoning=text_res[:150],
                    evidence_type="FACT" if evidence_text else "INFERENCE"
                )
            ]
        )
    except Exception as err:
        logger.error(f"Research Agent failed: {err}")
        return AgentOutput(
            agent_role="research",
            status="error",
            error_message=str(err)
        )


async def run_risk_agent(
    problem: str,
    context: str,
    constraints: str,
    evidence_text: str
) -> AgentOutput:
    """
    Risk Agent: Identifies risks, migration traps, security concerns, hidden assumptions, and failure scenarios.
    """
    prompt = (
        "You are a specialized Risk & Failure Analysis Agent in a Multi-Agent AI system.\n"
        "YOUR ROLE: Identify risks, failure modes, security concerns, implementation traps, and hidden assumptions.\n"
        "Challenge overly optimistic conclusions.\n\n"
        f"PROBLEM: {problem}\n"
        f"CONTEXT: {context or 'None'}\n"
        f"CONSTRAINTS: {constraints or 'None'}\n"
        f"RELEVANT EVIDENCE: {evidence_text or 'None'}\n\n"
        "Format your output as a clear 2-3 paragraph risk report highlighting vulnerabilities, migration risks, and assumptions."
    )

    try:
        text_res = await asyncio.to_thread(_call_gemini_api, prompt)
        if not text_res:
            return AgentOutput(
                agent_role="risk",
                status="error",
                error_message="Risk Agent API call returned empty text."
            )

        return AgentOutput(
            agent_role="risk",
            status="success",
            summary=text_res,
            findings=[
                AgentFinding(
                    claim="Key failure scenarios identified",
                    importance="high",
                    reasoning=text_res[:150],
                    evidence_type="INFERENCE"
                )
            ]
        )
    except Exception as err:
        logger.error(f"Risk Agent failed: {err}")
        return AgentOutput(
            agent_role="risk",
            status="error",
            error_message=str(err)
        )


async def run_tradeoff_agent(
    problem: str,
    context: str,
    constraints: str,
    evidence_text: str
) -> AgentOutput:
    """
    Trade-off / Cost Agent: Analyzes practical trade-offs, financial cost, complexity, effort, and team expertise.
    """
    prompt = (
        "You are a specialized Cost & Trade-off Agent in a Multi-Agent AI system.\n"
        "YOUR ROLE: Analyze practical trade-offs, financial costs, engineering effort, complexity, and team expertise.\n"
        "Focus on key trade-offs directly relevant to the actual problem.\n\n"
        f"PROBLEM: {problem}\n"
        f"CONTEXT: {context or 'None'}\n"
        f"CONSTRAINTS: {constraints or 'None'}\n"
        f"RELEVANT EVIDENCE: {evidence_text or 'None'}\n\n"
        "Format your output as a clear 2-3 paragraph trade-off report comparing cost, complexity, performance, and operational overhead."
    )

    try:
        text_res = await asyncio.to_thread(_call_gemini_api, prompt)
        if not text_res:
            return AgentOutput(
                agent_role="tradeoff",
                status="error",
                error_message="Trade-off Agent API call returned empty text."
            )

        return AgentOutput(
            agent_role="tradeoff",
            status="success",
            summary=text_res,
            findings=[
                AgentFinding(
                    claim="Cost and complexity trade-offs analyzed",
                    importance="high",
                    reasoning=text_res[:150],
                    evidence_type="INFERENCE"
                )
            ]
        )
    except Exception as err:
        logger.error(f"Trade-off Agent failed: {err}")
        return AgentOutput(
            agent_role="tradeoff",
            status="error",
            error_message=str(err)
        )


async def run_synthesizer_agent(
    problem: str,
    context: str,
    constraints: str,
    evidence_text: str,
    agent_outputs: List[AgentOutput]
) -> str:
    """
    Synthesizer Agent: Reconciles all specialized agent outputs, resolves contradictions, and forms final decision recommendation.
    """
    agent_reports_str = ""
    for out in agent_outputs:
        if out.status == "success" and out.summary:
            agent_reports_str += f"\n--- {out.agent_role.upper()} AGENT PERSPECTIVE ---\n{out.summary}\n"

    if not agent_reports_str.strip():
        agent_reports_str = "No valid agent outputs returned."

    prompt = (
        "You are the Lead Synthesizer Agent in a Multi-Agent AI Research Team.\n"
        "YOUR ROLE: Synthesize the findings of the Research, Risk, and Trade-off Agents into a single, cohesive, decision-focused recommendation.\n"
        "RULES:\n"
        "1. Resolve any contradictions between agents (e.g. cost savings vs migration complexity).\n"
        "2. Distinguish evidence-backed facts from assumptions.\n"
        "3. Provide direct, actionable advice without conversational filler (NO 'Certainly!', NO 'In conclusion').\n"
        "4. Structure cleanly with markdown headings: Summary, Key Factors, Recommendation, and Risks & Caveats.\n\n"
        f"ORIGINAL PROBLEM: {problem}\n"
        f"CONTEXT: {context or 'None'}\n"
        f"CONSTRAINTS: {constraints or 'None'}\n"
        f"RAG EVIDENCE: {evidence_text or 'None'}\n\n"
        f"SPECIALIZED AGENT FINDINGS:\n{agent_reports_str}\n\n"
        "Synthesize the final recommendation now:"
    )

    try:
        text_res = await asyncio.to_thread(_call_gemini_api, prompt)
        if text_res:
            return text_res.strip()
    except Exception as err:
        logger.error(f"Synthesizer Agent failed: {err}")

    # Fallback if synthesis fails
    valid_summaries = [out.summary for out in agent_outputs if out.status == "success" and out.summary]
    if valid_summaries:
        return "\n\n".join(valid_summaries)
    return "Multi-agent synthesis could not be completed."


async def run_multi_agent_pipeline(
    problem: str,
    context: str = "",
    constraints: str = "",
    evidence_text: str = ""
) -> MultiAgentResult:
    """
    Orchestrates parallel execution of specialized agents (Research, Risk, Trade-off),
    collects outputs, and invokes the Synthesizer Agent.
    """
    logger.info(f"Launching Multi-Agent Research Team for query: {problem[:60]}")

    # Execute independent research agents concurrently using asyncio.gather
    results = await asyncio.gather(
        run_research_agent(problem, context, constraints, evidence_text),
        run_risk_agent(problem, context, constraints, evidence_text),
        run_tradeoff_agent(problem, context, constraints, evidence_text),
        return_exceptions=True
    )

    agent_outputs: List[AgentOutput] = []
    agents_meta: List[Dict[str, str]] = []

    for res in results:
        if isinstance(res, Exception):
            logger.error(f"Agent execution exception: {res}")
            continue
        if isinstance(res, AgentOutput):
            agent_outputs.append(res)
            agents_meta.append({
                "role": res.agent_role,
                "status": res.status
            })

    # Run Synthesizer Agent after specialized agents complete
    synthesized_text = await run_synthesizer_agent(
        problem=problem,
        context=context,
        constraints=constraints,
        evidence_text=evidence_text,
        agent_outputs=agent_outputs
    )

    return MultiAgentResult(
        multi_agent_used=True,
        agent_outputs=agent_outputs,
        synthesized_analysis=synthesized_text,
        agents_metadata=agents_meta
    )
