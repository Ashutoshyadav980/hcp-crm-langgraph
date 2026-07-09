from typing import Annotated, TypedDict, List, Optional
import os
import json
from sqlalchemy.orm import Session
import datetime
from tools.tools import (
    LogInteractionTool,
    EditInteractionTool,
    SearchHCPTool,
    InteractionHistoryTool,
    SuggestFollowupTool,
    get_llm
)
from models.models import HCP, Interaction, FollowUp
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
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables relative to this file's location
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

import re
import time

# --- Intent Classifier Helper ---
def classify_intent_with_llm(text: str, chat_history: List[dict] = None) -> tuple[str, float]:
    text_lower = text.lower().strip()
    
    # 0. Fast-path confirmation check (Yes/No response for pending tasks)
    if text_lower in ["yes", "y", "sure", "ok", "okay", "please", "do it", "create it", "yes please", "yes, please", "yes, please do", "please do"]:
        if chat_history:
            last_assistant_msg = next((m for m in reversed(chat_history) if m.get("role") == "assistant"), None)
            if last_assistant_msg and "Would you like me to create this follow-up task?" in last_assistant_msg.get("content", ""):
                return "confirm", 1.0
                
    # Fast-path basic greetings
    if text_lower in ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]:
        return "general", 1.0
        
    llm = get_llm()
    if not llm:
        return "general", 1.0
        
    history_context = ""
    if chat_history:
        # Keep last 3 messages for context
        for msg in chat_history[-3:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_context += f"{role}: {content}\n"
            
    prompt = f"""
    You are an intent classifier for a Healthcare CRM AI Co-pilot.
    Analyze the user's message and determine the correct intent and confidence (0.0 to 1.0).
    
    Intents:
    - log: Logging a new doctor visit/interaction. User describes a completed interaction (e.g. "I met Dr. John...", "called Dr. Sunita about X", "discussed CardioPlus with John"). The presence of "Dr." alone is NOT a log. It must describe a meeting or communication.
    - search_interaction: Retrieving, listing, summarizing, or viewing past interaction history/logs with a doctor (e.g. "Show my interaction with John", "Give summary of today's meeting with Dr. John", "what did we discuss last time?", "summary of john").
    - search_hcp: Searching/looking up Healthcare Professional (HCP) profile info (specialty, contact, list of doctors) (e.g. "Who is Dr. John?", "Find cardiologists at Apollo", "search doctor John").
    - edit: Editing or updating details of a logged interaction (e.g. "change name to jon", "actually it was at 3pm", "update date").
    - suggest: Requesting follow-up recommendations, next steps, or next actions (e.g. "suggest follow up", "recommend next action", "what should I do next?").
    - confirm: Affirmation/Yes confirming a pending suggestion (e.g. "yes", "sure", "please do"). ONLY use this if the assistant's last message asked a question/proposal like "Would you like me to create this task?".
    - general: General conversation, greetings, general AI questions, or general questions about medical topics (e.g. "Which doctor is best?", "how are you", "what is cardiology?").
    
    IMPORTANT ROUTING RULE:
    If the user's message is completely unclear, gibberish, a code, random characters/letters/numbers (e.g. "xyz123abc999"), or you cannot confidently classify it under one of the CRM intents above, you MUST set the confidence score to less than 0.5.
    
    Context of last conversation turns:
    {history_context}
    
    User Message: "{text}"
    
    Return ONLY a raw JSON object with:
    - intent: "log" | "search_interaction" | "search_hcp" | "edit" | "suggest" | "confirm" | "general"
    - confidence: float between 0.0 and 1.0
    - reason: short explanation
    """
    
    try:
        messages = [
            SystemMessage(content="You are a strict JSON classifier. You return ONLY a valid JSON object."),
            HumanMessage(content=prompt)
        ]
        res = llm.invoke(messages)
        content = res.content.strip()
        
        # Clean markdown wraps if any
        if content.startswith("```"):
            lines = content.splitlines()
            if len(lines) > 1 and lines[0].startswith("```"):
                lines = lines[1:]
            if len(lines) > 0 and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()
            
        data = json.loads(content)
        intent = data.get("intent", "general")
        confidence = float(data.get("confidence", 0.8))
        return intent, confidence
    except Exception as e:
        print(f"[ERROR] LLM Intent classification failed: {e}")
        return "general", 1.0


# --- Graph Nodes ---
def intent_detector(state: AgentState, db: Session) -> AgentState:
    last_msg = state["messages"][-1]["content"]
    chat_history = state["messages"][:-1]
    
    start_time = time.perf_counter()
    intent, confidence = classify_intent_with_llm(last_msg, chat_history)
    elapsed = (time.perf_counter() - start_time) * 1000
    print(f"\n[TIMER] LLM Intent classification took: {elapsed:.2f}ms (Intent: '{intent}', Confidence: {confidence})")
    
    if confidence < 0.65:
        state["tool_triggered"] = "clarify"
        state["response"] = "I'm not completely sure what you'd like to do. Could you clarify if you want to log a visit, search doctor history, update an interaction, or get follow-up suggestions?"
    else:
        state["tool_triggered"] = intent
    
    # Load and Hydrate active interaction details if active_interaction_id is provided
    active_id = state.get("active_interaction_id")
    if active_id and not state.get("extracted_data"):
        interaction = db.query(Interaction).filter(Interaction.id == active_id, Interaction.user_id == state["user_id"]).first()
        if interaction:
            hcp = db.query(HCP).filter(HCP.id == interaction.hcp_id).first()
            state["extracted_data"] = {
                "id": interaction.id,
                "hcp_id": interaction.hcp_id,
                "hcp_name": hcp.name if hcp else "Unknown",
                "hospital": hcp.hospital if hcp else "",
                "specialty": hcp.specialty if hcp else "",
                "type": interaction.type,
                "date": interaction.date.isoformat() if interaction.date else "",
                "time": interaction.time,
                "topics_discussed": interaction.topics_discussed,
                "materials_shared": interaction.materials_shared,
                "sentiment": interaction.sentiment,
                "notes": interaction.notes,
                "summary": interaction.summary,
                "follow_up_date": interaction.follow_up_date.isoformat() if interaction.follow_up_date else ""
            }
    return state

def log_node(state: AgentState, db: Session) -> AgentState:
    last_msg = state["messages"][-1]["content"]
    result = LogInteractionTool(state["user_id"], db, last_msg)
    state["response"] = result["message"]
    state["extracted_data"] = result.get("extracted_data")
    if result["success"] and result.get("extracted_data"):
        state["active_interaction_id"] = result["extracted_data"].get("id")
    return state

def edit_node(state: AgentState, db: Session) -> AgentState:
    last_msg = state["messages"][-1]["content"]
    active_id = state.get("active_interaction_id")
    result = EditInteractionTool(state["user_id"], db, active_id, last_msg)
    state["response"] = result["message"]
    if result["success"] and result.get("extracted_data"):
        state["extracted_data"] = result["extracted_data"]
        state["active_interaction_id"] = result["extracted_data"].get("id")
    return state

def search_node(state: AgentState, db: Session) -> AgentState:
    last_msg = state["messages"][-1]["content"]
    query = last_msg.lower()
    
    # Remove search prefixes
    for prefix in ["search for", "find doctor", "find hcp", "find dr", "find", "look up", "lookup", "who is dr.", "who is dr", "who is", "show doctor", "list doctors"]:
        if prefix in query:
            query = query.replace(prefix, "")
            
    # Clean titles and spaces
    query = query.replace("dr.", "").replace("dr ", "").strip("?.").strip()
    
    result = SearchHCPTool(state["user_id"], db, query)
    state["response"] = result["message"]
    return state

def history_node(state: AgentState, db: Session) -> AgentState:
    last_msg = state["messages"][-1]["content"]
    last_msg_lower = last_msg.lower()
    
    # Extract name query from last_msg first for summary matching
    hcp_name_query = None
    for phrase in [
        "show my interactions with", "show my interaction with", 
        "show interactions with", "show interaction with", 
        "get interactions with", "get interaction with",
        "list interactions with", "list interaction with",
        "interactions with", "interaction with", 
        "history of", "history with", 
        "records of", "records with",
        "give summary of today's meeting with",
        "give summary of today's interaction with",
        "give summary of meeting with",
        "give summary of interaction with",
        "give summary of",
        "summary of today's meeting with",
        "summary of today's interaction with",
        "summary of the meeting with",
        "summary of the interaction with",
        "summary of meeting with",
        "summary of interaction with",
        "summary of",
        "summary with",
        "summarize today's meeting with",
        "summarize today's interaction with",
        "summarize meeting with",
        "summarize interaction with",
        "summarize"
    ]:
        if phrase in last_msg_lower:
            hcp_name_query = last_msg_lower.split(phrase)[-1].strip()
            hcp_name_query = hcp_name_query.strip("?.").strip()
            break
            
    # Clean titles from query
    if hcp_name_query:
        hcp_name_query = hcp_name_query.replace("dr.", "").replace("dr ", "").strip()
        # Exclude generic words that are NOT doctor names
        if hcp_name_query.lower() in [
            "today's interaction", "todays interaction", "today's meeting", "todays meeting",
            "the meeting", "the interaction", "interaction", "meeting", "today", "yesterday",
            "recent", "this meeting", "this interaction"
        ]:
            hcp_name_query = None
        
    # Check if user specifically requested a summary of the active/recent interaction
    if "summary" in last_msg_lower or "summarize" in last_msg_lower:
        active_id = state.get("active_interaction_id")
        interaction = None
        
        # If a name query was successfully extracted, find the HCP and their latest interaction!
        if hcp_name_query and hcp_name_query != "":
            hcp = db.query(HCP).filter(
                HCP.created_by == state["user_id"],
                HCP.name.ilike(f"%{hcp_name_query}%")
            ).first()
            if hcp:
                interaction = db.query(Interaction).filter(
                    Interaction.hcp_id == hcp.id,
                    Interaction.user_id == state["user_id"]
                ).order_by(Interaction.date.desc()).first()
            else:
                state["response"] = f"No interaction found for Dr. {hcp_name_query}."
                return state
                
        if not interaction and active_id:
            interaction = db.query(Interaction).filter(Interaction.id == active_id, Interaction.user_id == state["user_id"]).first()
            
        if not interaction:
            # Fallback to the latest interaction logged by this user
            interaction = db.query(Interaction).filter(Interaction.user_id == state["user_id"]).order_by(Interaction.created_at.desc()).first()
            
        if interaction:
            hcp = db.query(HCP).filter(HCP.id == interaction.hcp_id).first()
            hcp_name = hcp.name if hcp else "Unknown Doctor"
            date_str = interaction.date.isoformat() if interaction.date else "Unknown Date"
            summary_text = interaction.summary or "No summary available."
            follow_up_date_str = interaction.follow_up_date.isoformat() if interaction.follow_up_date else "No follow-up scheduled"
            
            state["response"] = f"Here is the summary of the interaction with **{hcp_name}** on **{date_str}**:\n" \
                                f"* **Summary**: {summary_text}\n" \
                                f"* **Follow-up**: Scheduled on {follow_up_date_str}."
            return state
        else:
            state["response"] = "No previous interactions found. Please log your first HCP interaction."
            return state

    # Normal history list extraction flow
    active_hcp_id = None
    if not hcp_name_query and state.get("extracted_data") and state["extracted_data"].get("hcp_id"):
        active_hcp_id = state["extracted_data"]["hcp_id"]
        
    result = InteractionHistoryTool(state["user_id"], db, hcp_id=active_hcp_id, hcp_name_query=hcp_name_query)
    state["response"] = result["message"]
    return state

def parse_pending_followup_from_history(messages: List[dict]) -> Optional[dict]:
    # Search backwards for the last assistant message containing the follow-up suggestion
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            if "Would you like me to create this follow-up task?" in content:
                try:
                    action = None
                    due_date = None
                    
                    # Parse Action
                    action_match = re.search(r'Next Recommended Action\*\*:\s*(.+)', content)
                    if action_match:
                        action = action_match.group(1).strip()
                        
                    # Parse Date
                    date_match = re.search(r'Follow up on or before \*\*(\d{4}-\d{2}-\d{2})\*\*', content)
                    if date_match:
                        due_date = date_match.group(1).strip()
                        
                    if action and due_date:
                        return {
                            "action": action,
                            "due_date": due_date
                        }
                except Exception as e:
                    print(f"[DEBUG] Error parsing pending followup: {e}")
                    return None
    return None

def suggest_node(state: AgentState, db: Session) -> AgentState:
    active_id = state.get("active_interaction_id")
    last_msg = state["messages"][-1]["content"]
    
    # Check if the user is confirming a pending follow-up task
    intent = state.get("tool_triggered")
    if intent == "confirm" or last_msg.lower().strip() in ["yes", "y", "sure", "ok", "okay", "please", "do it", "create it"]:
        pending = parse_pending_followup_from_history(state["messages"][:-1])
        if pending and active_id:
            try:
                # Check if it already exists to avoid duplicates
                existing = db.query(FollowUp).filter(
                    FollowUp.interaction_id == active_id,
                    FollowUp.action == pending["action"]
                ).first()
                
                if not existing:
                    follow_up = FollowUp(
                        interaction_id=active_id,
                        action=pending["action"],
                        due_date=datetime.date.fromisoformat(pending["due_date"]),
                        status="Pending",
                        notes="Confirmed and created by AI CRM Assistant."
                    )
                    db.add(follow_up)
                    db.commit()
                    db.refresh(follow_up)
                    print(f"[DEBUG] Confirmed and logged new FollowUp task: (ID: {follow_up.id})")
                
                state["response"] = f"Great! I have successfully created the follow-up task:\n- **Action**: {pending['action']}\n- **Due Date**: {pending['due_date']}"
                return state
            except Exception as e:
                print(f"[ERROR] Failed to save confirmed follow-up: {e}")
                state["response"] = "Sorry, I encountered an error saving the follow-up task to the database."
                return state

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
    if tool == "confirm":
        return "suggest"
    if tool == "clarify":
        return "clarify"
    if tool == "search_interaction":
        return "history"
    if tool == "search_hcp":
        return "search"
    if tool in ["log", "edit", "suggest", "general"]:
        return tool
    return "general"


# --- Compile the LangGraph ---
def build_agent_graph(db: Session):
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("intent_detector", lambda state: intent_detector(state, db))
    
    # We wrap database session inside closure node functions
    workflow.add_node("log", lambda state: log_node(state, db))
    workflow.add_node("edit", lambda state: edit_node(state, db))
    workflow.add_node("search", lambda state: search_node(state, db))
    workflow.add_node("history", lambda state: history_node(state, db))
    workflow.add_node("suggest", lambda state: suggest_node(state, db))
    workflow.add_node("general", general_node)
    workflow.add_node("clarify", lambda state: state)

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
            "general": "general",
            "clarify": "clarify"
        }
    )

    # Add Normal Edges to End
    workflow.add_edge("log", END)
    workflow.add_edge("edit", END)
    workflow.add_edge("search", END)
    workflow.add_edge("history", END)
    workflow.add_edge("suggest", END)
    workflow.add_edge("general", END)
    workflow.add_edge("clarify", END)

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
