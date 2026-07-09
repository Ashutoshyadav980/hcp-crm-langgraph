from typing import Annotated, TypedDict, List, Optional
import os
from sqlalchemy.orm import Session
from tools.tools import (
    LogInteractionTool,
    EditInteractionTool,
    SearchHCPTool,
    InteractionHistoryTool,
    SuggestFollowupTool,
    get_llm
)
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

# --- Define Agent State ---
class AgentState(TypedDict):
    messages: List[dict]           # [{role: "user" | "assistant", content: str}]
    user_id: int
    active_interaction_id: Optional[int]
    tool_triggered: Optional[str]
    extracted_data: Optional[dict]
    response: Optional[str]

import traceback
from dotenv import load_dotenv

load_dotenv()

import re
import time

# --- Intent Classifier Helper ---
def classify_intent(text: str) -> str:
    text_lower = text.lower().strip()
    
    # 1. Edit Intent
    # Keywords: change, edit, update, modify, replace, actually, remove, set, correct
    if re.search(r'\b(change|edit|update|modify|replace|actually|remove|set|correct)\b', text_lower):
        return "edit"
        
    # 2. Search Intent
    # Keywords: search, find, look up, lookup, who is, show doctor, list doctors
    if re.search(r'\b(search|find|look\s*up|lookup|who\s+is|show\s+doctor|list\s+doctor)\b', text_lower):
        return "search"
        
    # 3. History Intent
    # Keywords: history, past, previous, timeline, last, record, log history, logs
    if re.search(r'\b(history|past|previous|timeline|last|record|logs)\b', text_lower):
        return "history"
        
    # 4. Suggest Intent
    # Keywords: suggest, recommend, follow-up, advice, tips, next step, next action
    if re.search(r'\b(suggest|recommend|follow-up|advice|tips|next\s+step|next\s+action)\b', text_lower):
        return "suggest"
        
    # 5. Log Intent
    # Keywords: met, met with, discussed, call with, phoned, emailed, visited, had meeting, dr, doctor
    if re.search(r'\b(met|discussed|call|phoned|emailed|visited|meeting|dr\.|dr\b|doctor)\b', text_lower):
        return "log"
        
    return "general"


# --- Graph Nodes ---
def intent_detector(state: AgentState) -> AgentState:
    last_msg = state["messages"][-1]["content"]
    start_time = time.perf_counter()
    intent = classify_intent(last_msg)
    elapsed = (time.perf_counter() - start_time) * 1000
    print(f"\n[TIMER] Intent classification took: {elapsed:.2f}ms (Intent: '{intent}')")
    state["tool_triggered"] = intent
    return state

def log_node(state: AgentState, db: Session) -> AgentState:
    last_msg = state["messages"][-1]["content"]
    result = LogInteractionTool(state["user_id"], db, last_msg)
    state["response"] = result["message"]
    state["extracted_data"] = result["extracted_data"]
    state["active_interaction_id"] = result["extracted_data"].get("id")
    return state

def edit_node(state: AgentState, db: Session) -> AgentState:
    last_msg = state["messages"][-1]["content"]
    active_id = state.get("active_interaction_id")
    result = EditInteractionTool(state["user_id"], db, active_id, last_msg)
    state["response"] = result["message"]
    if result["success"]:
        state["extracted_data"] = result["extracted_data"]
        state["active_interaction_id"] = result["extracted_data"].get("id")
    return state

def search_node(state: AgentState, db: Session) -> AgentState:
    last_msg = state["messages"][-1]["content"]
    # Clean query text
    query = last_msg.replace("search for", "").replace("find", "").replace("look up", "").replace("search", "").strip()
    result = SearchHCPTool(state["user_id"], db, query)
    state["response"] = result["message"]
    return state

def history_node(state: AgentState, db: Session) -> AgentState:
    # If active interaction exists, we can show history for that doctor
    active_hcp_id = None
    if state.get("extracted_data") and state["extracted_data"].get("hcp_id"):
        active_hcp_id = state["extracted_data"]["hcp_id"]
    result = InteractionHistoryTool(state["user_id"], db, active_hcp_id)
    state["response"] = result["message"]
    return state

def suggest_node(state: AgentState, db: Session) -> AgentState:
    active_id = state.get("active_interaction_id")
    last_msg = state["messages"][-1]["content"]
    result = SuggestFollowupTool(state["user_id"], db, active_id, last_msg)
    state["response"] = result["message"]
    if result["success"]:
        state["active_interaction_id"] = result["suggestions"].get("active_interaction_id")
        state["extracted_data"] = result.get("extracted_data")
    return state

def general_node(state: AgentState) -> AgentState:
    last_msg = state["messages"][-1]["content"]
    llm = get_llm()
    if llm:
        try:
            messages = [
                SystemMessage(content="You are a helpful AI assistant for a Healthcare CRM module. Guide the user on logging doctor visits, search HCPs, retrieve history, edit details, or request suggestions."),
                HumanMessage(content=last_msg)
            ]
            res = llm.invoke(messages)
            state["response"] = res.content
        except Exception:
            state["response"] = "Hi! I am your AI CRM Assistant. I can help you log interactions, edit records, search HCPs, view histories, or suggest follow-up actions. How can I help you today?"
    else:
        state["response"] = "Hi! I am your AI CRM Assistant. I can help you log interactions, edit records, search HCPs, view histories, or suggest follow-up actions. How can I help you today?"
    return state


# --- Router for Conditional Edges ---
def route_intent(state: AgentState) -> str:
    tool = state.get("tool_triggered")
    if tool in ["log", "edit", "search", "history", "suggest", "general"]:
        return tool
    return "general"


# --- Compile the LangGraph ---
def build_agent_graph(db: Session):
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("intent_detector", intent_detector)
    
    # We wrap database session inside closure node functions
    workflow.add_node("log", lambda state: log_node(state, db))
    workflow.add_node("edit", lambda state: edit_node(state, db))
    workflow.add_node("search", lambda state: search_node(state, db))
    workflow.add_node("history", lambda state: history_node(state, db))
    workflow.add_node("suggest", lambda state: suggest_node(state, db))
    workflow.add_node("general", general_node)

    # Set Entry Point
    workflow.set_entry_point("intent_detector")

    # Add Conditional Edges
    workflow.add_conditional_edges(
        "intent_detector",
        route_intent,
        {
            "log": "log",
            "edit": "edit",
            "search": "search",
            "history": "history",
            "suggest": "suggest",
            "general": "general"
        }
    )

    # Add Normal Edges to End
    workflow.add_edge("log", END)
    workflow.add_edge("edit", END)
    workflow.add_edge("search", END)
    workflow.add_edge("history", END)
    workflow.add_edge("suggest", END)
    workflow.add_edge("general", END)

    return workflow.compile()


# --- Main Call Entrypoint ---
def run_crm_agent(user_id: int, message: str, db: Session, active_interaction_id: Optional[int] = None, chat_history: List[dict] = None) -> dict:
    history = chat_history or []
    full_messages = history + [{"role": "user", "content": message}]
    
    # Initialize state
    initial_state = {
        "messages": full_messages,
        "user_id": user_id,
        "active_interaction_id": active_interaction_id,
        "tool_triggered": None,
        "extracted_data": None,
        "response": None
    }
    
    graph = build_agent_graph(db)
    final_state = graph.invoke(initial_state)
    
    new_history = full_messages + [{"role": "assistant", "content": final_state["response"]}]
    
    return {
        "response": final_state["response"],
        "tool_triggered": final_state["tool_triggered"],
        "extracted_data": final_state["extracted_data"],
        "active_interaction_id": final_state["active_interaction_id"],
        "chat_history": new_history
    }
