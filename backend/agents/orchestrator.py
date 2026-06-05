"""
LangGraph Orchestrator — runs the full analysis pipeline.

Graph:
  START → ingest → embed → rule_scores → llm_analysis → build_result → END
"""

from typing import TypedDict, Optional, Dict
from langgraph.graph import StateGraph, END
from loguru import logger
import json


class AnalysisState(TypedDict):
    repo_id:         str
    owner:           str
    name:            str
    repo_data:       Optional[Dict]
    collection_name: Optional[str]
    rule_scores:     Optional[Dict]
    llm_result:      Optional[Dict]
    final:           Optional[Dict]
    error:           Optional[str]


def node_ingest(state: AnalysisState) -> AnalysisState:
    import asyncio
    from agents.ingestion_agent import IngestionAgent
    try:
        repo_data = asyncio.run(IngestionAgent().run(state["owner"], state["name"]))
        logger.info(f"Ingest done: {len(repo_data.get('code_files', []))} files")
        return {**state, "repo_data": repo_data}
    except Exception as e:
        logger.error(f"Ingest error: {e}")
        return {**state, "error": str(e)}


def node_embed(state: AnalysisState) -> AnalysisState:
    if state.get("error"):
        return state
    try:
        from agents.embedding_agent import EmbeddingAgent
        name = EmbeddingAgent().run(state["repo_data"], state["repo_id"])
        logger.info(f"Embed done: {name}")
        return {**state, "collection_name": name}
    except Exception as e:
        logger.error(f"Embed error: {e}")
        return {**state, "error": str(e), "collection_name": None}


def node_rule_scores(state: AnalysisState) -> AnalysisState:
    try:
        from tasks.analysis_tasks import _rule_scores
        scores = _rule_scores(state["repo_data"])
        logger.info(f"Rules done: overall={scores['overall']}")
        return {**state, "rule_scores": scores}
    except Exception as e:
        logger.error(f"Rule score error: {e}")
        return {**state, "rule_scores": {
            "overall": 50, "recruiter": 45,
            "code_quality": 50, "documentation": 50,
            "testing": 50, "devops": 50, "architecture": 50,
            "summary": "Analysis completed.",
            "strengths": [], "weaknesses": [], "missing_practices": [],
        }}


def node_llm_analysis(state: AnalysisState) -> AnalysisState:
    try:
        from tasks.analysis_tasks import _llm_analysis
        result = _llm_analysis(state["repo_data"], state["rule_scores"])
        logger.info("LLM done")
        return {**state, "llm_result": result}
    except Exception as e:
        logger.error(f"LLM error: {e}")
        from tasks.analysis_tasks import _fallback_result
        return {**state, "llm_result": _fallback_result(state["rule_scores"], state["repo_data"])}


def node_build_result(state: AnalysisState) -> AnalysisState:
    llm = state.get("llm_result") or {}
    scores = llm.get("scores") or state.get("rule_scores") or {}
    return {**state, "final": {
        "scores":             scores,
        "recruiter_feedback": llm.get("recruiter_feedback"),
        "mentor_roadmap":     llm.get("mentor_roadmap"),
        "collection_name":    state.get("collection_name"),
    }}


def _route_after_embed(state: AnalysisState) -> str:
    return "build_result" if state.get("error") else "rule_scores"


_graph = None

def get_graph():
    global _graph
    if _graph is None:
        g = StateGraph(AnalysisState)
        g.add_node("ingest",       node_ingest)
        g.add_node("embed",        node_embed)
        g.add_node("rule_scores",  node_rule_scores)
        g.add_node("llm_analysis", node_llm_analysis)
        g.add_node("build_result", node_build_result)
        g.set_entry_point("ingest")
        g.add_edge("ingest", "embed")
        g.add_conditional_edges("embed", _route_after_embed, {
            "rule_scores":  "rule_scores",
            "build_result": "build_result",
        })
        g.add_edge("rule_scores",  "llm_analysis")
        g.add_edge("llm_analysis", "build_result")
        g.add_edge("build_result", END)
        _graph = g.compile()
    return _graph


def run_graph(repo_id: str, owner: str, name: str) -> dict:
    """Run the full LangGraph pipeline."""
    final_state = get_graph().invoke({
        "repo_id": repo_id, "owner": owner, "name": name,
        "repo_data": None, "collection_name": None,
        "rule_scores": None, "llm_result": None,
        "final": None, "error": None,
    })
    return final_state.get("final") or {}
