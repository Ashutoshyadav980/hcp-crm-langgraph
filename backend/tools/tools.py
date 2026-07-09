import os
import json
import datetime
import traceback
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from models.models import HCP, Interaction, FollowUp, Product
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# Load environment variables relative to this file's location
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

import time

_llm_instance = None

def get_llm():
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance
        
    api_key = os.getenv("GROQ_API_KEY")
    print(f"\n[DEBUG] --- Groq LLM Initialization ---")
    print(f"[DEBUG] GROQ_API_KEY env key present: {bool(api_key)}")
    if not api_key or api_key == "YOUR_GROQ_API_KEY":
        print("[ERROR] GROQ_API_KEY is not configured in .env file.")
        raise ValueError("GROQ_API_KEY environment variable is missing or set to placeholder in .env")
    try:
        _llm_instance = ChatGroq(
            groq_api_key=api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.1
        )
        print("[DEBUG] ChatGroq successfully initialized and cached.")
        return _llm_instance
    except Exception as e:
        print("[ERROR] Failed to initialize ChatGroq:")
        traceback.print_exc()
        raise e

def clean_json_content(content: str) -> str:
    content = content.strip()
    if content.startswith("```"):
        # Remove first line (e.g. ```json or ```)
        lines = content.splitlines()
        if len(lines) > 1 and lines[0].startswith("```"):
            lines = lines[1:]
        # Remove closing codeblock
        if len(lines) > 0 and lines[-1].strip() == "```":
            lines = lines[:-1]
        content = "\n".join(lines)
    return content.strip().strip("`").strip()

def validate_extracted_json(data: dict) -> dict:
    required_fields = ["hcp_name", "hospital", "specialty", "type", "date", "time", "topics_discussed", "materials_shared", "sentiment", "notes", "summary"]
    
    if not isinstance(data, dict):
        raise TypeError(f"Extracted JSON must be a dictionary. Got: {type(data)}")
        
    for field in required_fields:
        if field not in data:
            data[field] = ""
            
    # Normalize HCP name (remove title wrappers if present and prefix with Dr. if missing)
    hcp_name = str(data["hcp_name"]).strip()
    if hcp_name and not hcp_name.lower().startswith("dr.") and not hcp_name.lower().startswith("dr "):
        data["hcp_name"] = "Dr. " + hcp_name
            
    # Validate date
    if data.get("date"):
        try:
            datetime.datetime.strptime(str(data["date"]), "%Y-%m-%d")
        except ValueError:
            data["date"] = datetime.date.today().isoformat()
    else:
        data["date"] = datetime.date.today().isoformat()
        
    # Resolve relative words in follow_up_date to absolute YYYY-MM-DD format
    if data.get("follow_up_date"):
        follow_up_str = str(data["follow_up_date"]).lower().strip()
        today = datetime.date.today()
        if "next tuesday" in follow_up_str:
            days_ahead = 1 - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            data["follow_up_date"] = (today + datetime.timedelta(days=days_ahead)).isoformat()
        elif "next friday" in follow_up_str:
            days_ahead = 4 - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            data["follow_up_date"] = (today + datetime.timedelta(days=days_ahead)).isoformat()
        elif "10 days" in follow_up_str:
            data["follow_up_date"] = (today + datetime.timedelta(days=10)).isoformat()
        else:
            try:
                datetime.datetime.strptime(str(data["follow_up_date"]), "%Y-%m-%d")
            except ValueError:
                # If date format is not matching, default to 7 days
                data["follow_up_date"] = (today + datetime.timedelta(days=7)).isoformat()
    return data

# --- LLM Functions ---
def extract_interaction_with_llm(text: str) -> dict:
    print(f"\n[DEBUG] --- Extraction: extract_interaction_with_llm ---")
    print(f"[DEBUG] Input User text:\n\"{text}\"")
    
    llm = get_llm()
    if not llm:
        raise ValueError("Failed to get LLM instance in extract_interaction_with_llm.")
        
    prompt = f"""
    You are an AI assistant for a healthcare CRM. Extract HCP interaction details from the text below.
    Return ONLY a raw JSON object with these fields, no markdown backticks, no wrap, no explanation:
    - hcp_name: Name of doctor (e.g. "Dr. Robert Smith"). If no doctor name is mentioned, extract the name, starting with "Dr. "
    - hospital: Hospital name if mentioned (default: "General Hospital")
    - specialty: Doctor specialty if mentioned (default: "General Practice")
    - type: "Meeting", "Call", "Email" (default: "Meeting")
    - date: YYYY-MM-DD format (default: today's date: {datetime.date.today().isoformat()})
    - time: Time of meeting, e.g. "07:36 PM" (default: current time)
    - topics_discussed: What was discussed (e.g. "Product X efficacy")
    - materials_shared: What was shared or requested (e.g. "Brochures", "10 samples")
    - sentiment: "Positive", "Neutral", "Negative" (default: "Positive")
    - follow_up_date: YYYY-MM-DD format. Calculate from expressions relative to today's date (today is {datetime.date.today().isoformat()}, today weekday is {datetime.date.today().strftime('%A')}). E.g., "next Tuesday" or "next Friday" or "after 10 days". If no follow-up date is mentioned in the text, return empty string or null.
    - notes: Extra details.
    - summary: Concise 1-2 sentence overview of the interaction.

    Text: "{text}"
    """
    
    try:
        messages = [
            SystemMessage(content="You are a JSON extractor. You return ONLY valid JSON."),
            HumanMessage(content=prompt)
        ]
        print("[DEBUG] Invoking Groq (llama-3.3-70b-versatile) API...")
        start_time = time.perf_counter()
        res = llm.invoke(messages)
        elapsed = (time.perf_counter() - start_time) * 1000
        print(f"[TIMER] Groq LLM response elapsed: {elapsed:.2f}ms")
        content = res.content.strip()
        print(f"[DEBUG] Raw response from Groq API (status: 200):\n{content}")
        
        # Clean markdown wraps
        clean_content = clean_json_content(content)
        print(f"[DEBUG] Cleaned JSON content:\n{clean_content}")
        
        extracted_data = json.loads(clean_content)
        print("[DEBUG] JSON parsed successfully.")
        
        validated_data = validate_extracted_json(extracted_data)
        print("[DEBUG] Validated extracted data successfully.")
        return validated_data
    except Exception as e:
        print("[ERROR] Exception in extract_interaction_with_llm:")
        traceback.print_exc()
        raise e

def edit_interaction_with_llm(original: dict, edit_text: str) -> dict:
    print(f"\n[DEBUG] --- Edit: edit_interaction_with_llm ---")
    print(f"[DEBUG] Original JSON:\n{json.dumps(original, indent=2)}")
    print(f"[DEBUG] User edit instruction: '{edit_text}'")
    
    llm = get_llm()
    if not llm:
        raise ValueError("Failed to get LLM instance in edit_interaction_with_llm.")
        
    prompt = f"""
    You are an AI assistant for a healthcare CRM. You need to update an existing interaction JSON based on a natural language instruction.
    Update ONLY the fields mentioned. Keep all other fields exactly as they are.
    Return ONLY the updated raw JSON object, no explanation.

    Original JSON:
    {json.dumps(original, indent=2)}

    Instruction: "{edit_text}"
    Current date: {datetime.date.today().isoformat()} (weekday: {datetime.date.today().strftime('%A')})
    """
    
    try:
        messages = [
            SystemMessage(content="You update structured JSON records based on text edits. Return ONLY JSON."),
            HumanMessage(content=prompt)
        ]
        print("[DEBUG] Invoking Groq (llama-3.3-70b-versatile) API...")
        start_time = time.perf_counter()
        res = llm.invoke(messages)
        elapsed = (time.perf_counter() - start_time) * 1000
        print(f"[TIMER] Groq LLM response elapsed: {elapsed:.2f}ms")
        content = res.content.strip()
        print(f"[DEBUG] Raw response from Groq API (status: 200):\n{content}")
        
        # Clean markdown wraps
        clean_content = clean_json_content(content)
        print(f"[DEBUG] Cleaned JSON content:\n{clean_content}")
        
        updated_data = json.loads(clean_content)
        print("[DEBUG] JSON parsed successfully.")
        
        validated_data = validate_extracted_json(updated_data)
        print("[DEBUG] Validated updated data successfully.")
        return validated_data
    except Exception as e:
        print("[ERROR] Exception in edit_interaction_with_llm:")
        traceback.print_exc()
        raise e

# --- 1. LogInteractionTool ---
def LogInteractionTool(user_id: int, db: Session, text: str) -> dict:
    print(f"\n[DEBUG] === LangGraph Tool Selected: LogInteractionTool ===")
    
    # 1. Extract details using LLM
    extracted = extract_interaction_with_llm(text)
    
    # 2. Database Operations (Search/Create HCP, save Interaction & FollowUp)
    db_start = time.perf_counter()
    hcp_name = extracted.get("hcp_name", "").strip()
    
    # Strict validation of Doctor/HCP Name
    clean_hcp_name = hcp_name.replace("Dr.", "").replace("Dr", "").strip()
    if not clean_hcp_name or clean_hcp_name.lower() in ["unknown", "u", "none", "null", "placeholder", ""]:
        db_elapsed = (time.perf_counter() - db_start) * 1000
        print(f"[TIMER] Database operations (invalid doctor name abort) took: {db_elapsed:.2f}ms")
        return {
            "success": False,
            "message": "I couldn't find the doctor's name in your message. Could you please specify which HCP you met?",
            "extracted_data": None
        }
        
    hcp = db.query(HCP).filter(HCP.name == hcp_name, HCP.created_by == user_id).first()
    if not hcp:
        hcp = HCP(
            name=hcp_name,
            hospital=extracted.get("hospital", "General Hospital"),
            specialty=extracted.get("specialty", "General Practice"),
            created_by=user_id
        )
        db.add(hcp)
        db.commit()
        db.refresh(hcp)
        print(f"[DEBUG] Created new HCP profile: '{hcp_name}' (ID: {hcp.id})")
    else:
        print(f"[DEBUG] Found existing HCP profile: '{hcp_name}' (ID: {hcp.id})")
        
    # 3. Parse dates
    try:
        date_obj = datetime.datetime.strptime(extracted.get("date"), "%Y-%m-%d").date()
    except Exception:
        date_obj = datetime.date.today()
        
    follow_up_date_obj = None
    if extracted.get("follow_up_date"):
        try:
            follow_up_date_obj = datetime.datetime.strptime(extracted.get("follow_up_date"), "%Y-%m-%d").date()
        except Exception:
            pass

    # 4. Create and save Interaction
    interaction = Interaction(
        user_id=user_id,
        hcp_id=hcp.id,
        type=extracted.get("type", "Meeting"),
        date=date_obj,
        time=extracted.get("time", "12:00 PM"),
        topics_discussed=extracted.get("topics_discussed", ""),
        materials_shared=extracted.get("materials_shared", ""),
        sentiment=extracted.get("sentiment", "Positive"),
        notes=extracted.get("notes", ""),
        summary=extracted.get("summary", ""),
        follow_up_date=follow_up_date_obj
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    print(f"[DEBUG] Logged new Interaction: (ID: {interaction.id})")

    # 5. Add follow-up record if requested
    if follow_up_date_obj:
        follow_up = FollowUp(
            interaction_id=interaction.id,
            action=f"Follow-up regarding {extracted.get('topics_discussed', 'previous discussion')}",
            due_date=follow_up_date_obj,
            status="Pending"
        )
        db.add(follow_up)
        db.commit()
        print(f"[DEBUG] Logged new FollowUp task: (ID: {follow_up.id}, due: {extracted.get('follow_up_date')})")
    db_elapsed = (time.perf_counter() - db_start) * 1000
    print(f"[TIMER] Database operations took: {db_elapsed:.2f}ms")

    # Form synchronization payload (include generated ids)
    extracted["id"] = interaction.id
    extracted["hcp_id"] = hcp.id
    extracted["hospital"] = hcp.hospital
    extracted["specialty"] = hcp.specialty

    return {
        "success": True,
        "message": f"**Interaction logged successfully!** Saved meeting with {hcp_name}.",
        "extracted_data": extracted
    }


# --- 2. EditInteractionTool ---
def EditInteractionTool(user_id: int, db: Session, active_interaction_id: int, edit_text: str) -> dict:
    print(f"\n[DEBUG] === LangGraph Tool Selected: EditInteractionTool ===")
    # 1. Fetch current interaction details (Database Operations)
    db_start = time.perf_counter()
    if not active_interaction_id:
        # Fallback to the most recent interaction for this user
        last_interaction = db.query(Interaction).filter(Interaction.user_id == user_id).order_by(Interaction.created_at.desc()).first()
        if last_interaction:
            active_interaction_id = last_interaction.id
        else:
            return {
                "success": False,
                "message": "No active interaction to edit. Please log a new interaction first.",
                "extracted_data": {}
            }
        
    interaction = db.query(Interaction).filter(Interaction.id == active_interaction_id, Interaction.user_id == user_id).first()
    if not interaction:
        return {
            "success": False,
            "message": f"Interaction with ID {active_interaction_id} not found.",
            "extracted_data": {}
        }
        
    hcp = db.query(HCP).filter(HCP.id == interaction.hcp_id).first()
    db_elapsed = (time.perf_counter() - db_start) * 1000
    print(f"[TIMER] Database read operations took: {db_elapsed:.2f}ms")
    
    current_json = {
        "hcp_name": hcp.name if hcp else "Unknown",
        "hospital": hcp.hospital if hcp else "",
        "specialty": hcp.specialty if hcp else "",
        "type": interaction.type,
        "date": interaction.date.isoformat() if interaction.date else "",
        "time": interaction.time,
        "topics_discussed": interaction.topics_discussed,
        "materials_shared": interaction.materials_shared,
        "sentiment": interaction.sentiment,
        "follow_up_date": interaction.follow_up_date.isoformat() if interaction.follow_up_date else "",
        "notes": interaction.notes,
        "summary": interaction.summary
    }

    # 2. Get updated fields using LLM
    updated_json = edit_interaction_with_llm(current_json, edit_text)

    # 3. Apply updates to Database
    db_write_start = time.perf_counter()
    # If HCP name changed, we may update the HCP name
    if hcp and updated_json.get("hcp_name") and updated_json.get("hcp_name") != hcp.name:
        hcp.name = updated_json.get("hcp_name")
    if hcp and updated_json.get("hospital") and updated_json.get("hospital") != hcp.hospital:
        hcp.hospital = updated_json.get("hospital")
    if hcp and updated_json.get("specialty") and updated_json.get("specialty") != hcp.specialty:
        hcp.specialty = updated_json.get("specialty")
        
    interaction.type = updated_json.get("type", interaction.type)
    interaction.time = updated_json.get("time", interaction.time)
    interaction.topics_discussed = updated_json.get("topics_discussed", interaction.topics_discussed)
    interaction.materials_shared = updated_json.get("materials_shared", interaction.materials_shared)
    interaction.sentiment = updated_json.get("sentiment", interaction.sentiment)
    interaction.notes = updated_json.get("notes", interaction.notes)
    interaction.summary = updated_json.get("summary", interaction.summary)

    if updated_json.get("date"):
        try:
            interaction.date = datetime.datetime.strptime(updated_json.get("date"), "%Y-%m-%d").date()
        except Exception:
            pass

    if updated_json.get("follow_up_date"):
        try:
            interaction.follow_up_date = datetime.datetime.strptime(updated_json.get("follow_up_date"), "%Y-%m-%d").date()
            # Update associated follow up task
            follow_up = db.query(FollowUp).filter(FollowUp.interaction_id == interaction.id).first()
            if follow_up:
                follow_up.due_date = interaction.follow_up_date
                db.add(follow_up)
            else:
                follow_up = FollowUp(
                    interaction_id=interaction.id,
                    action=f"Follow-up regarding {interaction.topics_discussed}",
                    due_date=interaction.follow_up_date
                )
                db.add(follow_up)
        except Exception:
            pass
            
    db.commit()
    db.refresh(interaction)
    db_write_elapsed = (time.perf_counter() - db_write_start) * 1000
    print(f"[TIMER] Database write operations took: {db_write_elapsed:.2f}ms")

    updated_json["id"] = interaction.id
    updated_json["hcp_id"] = interaction.hcp_id

    return {
        "success": True,
        "message": "**Interaction updated successfully!** Affected fields have been updated.",
        "extracted_data": updated_json
    }


def SearchHCPTool(user_id: int, db: Session, query: str) -> dict:
    print(f"\n[DEBUG] === LangGraph Tool Selected: SearchHCPTool ===")
    print(f"[DEBUG] Search Query: '{query}'")
    db_start = time.perf_counter()
    hcps = db.query(HCP).filter(
        HCP.created_by == user_id,
        (HCP.name.ilike(f"%{query}%") | HCP.hospital.ilike(f"%{query}%") | HCP.specialty.ilike(f"%{query}%"))
    ).all()

    if not hcps:
        db_elapsed = (time.perf_counter() - db_start) * 1000
        print(f"[TIMER] Database operations took: {db_elapsed:.2f}ms")
        return {
            "success": True,
            "message": f"No HCP found matching '{query}'.",
            "results": []
        }

    results = []
    for hcp in hcps:
        # Get count of previous interactions
        count = db.query(Interaction).filter(Interaction.hcp_id == hcp.id).count()
        results.append({
            "id": hcp.id,
            "name": hcp.name,
            "hospital": hcp.hospital,
            "specialty": hcp.specialty,
            "phone": hcp.phone,
            "email": hcp.email,
            "total_interactions": count
        })

    msg = f"Found {len(results)} matching HCPs:\n"
    for r in results:
        msg += f"- **{r['name']}** ({r['specialty']} at {r['hospital']}) - {r['total_interactions']} past interactions\n"

    db_elapsed = (time.perf_counter() - db_start) * 1000
    print(f"[TIMER] Database operations took: {db_elapsed:.2f}ms")
    return {
        "success": True,
        "message": msg,
        "results": results
    }


# --- 4. InteractionHistoryTool ---
def InteractionHistoryTool(user_id: int, db: Session, hcp_id: int = None, hcp_name_query: str = None) -> dict:
    print(f"\n[DEBUG] === LangGraph Tool Selected: InteractionHistoryTool ===")
    print(f"[DEBUG] Target HCP ID: {hcp_id}, Name Query: '{hcp_name_query}'")
    db_start = time.perf_counter()
    
    target_hcp_name = "Unknown Doctor"
    if hcp_name_query:
        hcp = db.query(HCP).filter(
            HCP.created_by == user_id,
            HCP.name.ilike(f"%{hcp_name_query}%")
        ).first()
        if hcp:
            hcp_id = hcp.id
            target_hcp_name = hcp.name
        else:
            db_elapsed = (time.perf_counter() - db_start) * 1000
            print(f"[TIMER] Database operations took: {db_elapsed:.2f}ms")
            clean_query = hcp_name_query.replace("Dr.", "").replace("Dr", "").strip()
            return {
                "success": False,
                "message": f"No interaction found for Dr. {clean_query}.",
                "history": []
            }
            
    query = db.query(Interaction).filter(Interaction.user_id == user_id)
    if hcp_id:
        query = query.filter(Interaction.hcp_id == hcp_id)
        if target_hcp_name == "Unknown Doctor":
            hcp = db.query(HCP).filter(HCP.id == hcp_id).first()
            if hcp:
                target_hcp_name = hcp.name
    
    interactions = query.order_by(Interaction.date.desc()).limit(5).all()

    if not interactions:
        db_elapsed = (time.perf_counter() - db_start) * 1000
        print(f"[TIMER] Database operations took: {db_elapsed:.2f}ms")
        display_name = target_hcp_name if target_hcp_name != "Unknown Doctor" else (hcp_name_query if hcp_name_query else "John")
        
        # Clean display name formatting
        display_name_clean = display_name.replace("Dr.", "").replace("Dr", "").strip()
        return {
            "success": False,
            "message": f"No interaction found for Dr. {display_name_clean}.",
            "history": []
        }

    history_list = []
    msg = "**Recent Interaction History:**\n\n"
    for idx, item in enumerate(interactions):
        hcp = db.query(HCP).filter(HCP.id == item.hcp_id).first()
        hcp_name = hcp.name if hcp else "Unknown Doctor"
        date_str = item.date.isoformat() if item.date else "Unknown Date"
        
        history_list.append({
            "id": item.id,
            "hcp_name": hcp_name,
            "date": date_str,
            "topics": item.topics_discussed,
            "sentiment": item.sentiment,
            "summary": item.summary
        })
        msg += f"{idx + 1}. **{date_str}** with **{hcp_name}**:\n"
        msg += f"   - *Topics*: {item.topics_discussed}\n"
        msg += f"   - *Sentiment*: {item.sentiment}\n"
        msg += f"   - *Summary*: {item.summary}\n\n"

    db_elapsed = (time.perf_counter() - db_start) * 1000
    print(f"[TIMER] Database operations took: {db_elapsed:.2f}ms")
    return {
        "success": True,
        "message": msg,
        "history": history_list
    }


def SuggestFollowupTool(user_id: int, db: Session, active_interaction_id: int, query_text: str = "") -> dict:
    print(f"\n[DEBUG] === LangGraph Tool Selected: SuggestFollowupTool ===")
    print(f"[DEBUG] Active Interaction ID: {active_interaction_id}")
    print(f"[DEBUG] Query Text: '{query_text}'")
    
    db_start = time.perf_counter()
    
    # 1. Fallback to latest interaction if active_interaction_id is not provided
    if not active_interaction_id:
        last_interaction = db.query(Interaction).filter(Interaction.user_id == user_id).order_by(Interaction.created_at.desc()).first()
        if last_interaction:
            active_interaction_id = last_interaction.id
            print(f"[DEBUG] SuggestFollowupTool fallback selected last interaction ID: {active_interaction_id}")
        else:
            db_elapsed = (time.perf_counter() - db_start) * 1000
            print(f"[TIMER] Database operations took: {db_elapsed:.2f}ms")
            return {
                "success": False,
                "message": "No previous interactions found. Please log your first HCP interaction.",
                "suggestions": {}
            }
            
    interaction = db.query(Interaction).filter(Interaction.id == active_interaction_id, Interaction.user_id == user_id).first()
    if not interaction:
        # Fallback to the latest interaction if selected ID is invalid or deleted
        last_interaction = db.query(Interaction).filter(Interaction.user_id == user_id).order_by(Interaction.created_at.desc()).first()
        if last_interaction:
            interaction = last_interaction
            active_interaction_id = last_interaction.id
            print(f"[DEBUG] SuggestFollowupTool fallback selected last interaction ID: {active_interaction_id}")
        else:
            db_elapsed = (time.perf_counter() - db_start) * 1000
            print(f"[TIMER] Database operations took: {db_elapsed:.2f}ms")
            return {
                "success": False,
                "message": "No previous interactions found. Please log your first HCP interaction.",
                "suggestions": {}
            }

    hcp = db.query(HCP).filter(HCP.id == interaction.hcp_id).first()
    hcp_name = hcp.name if hcp else "the doctor"

    # Return extracted data for form synchronization
    extracted_form = {
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

    # 2. Check if a follow-up already exists in the database
    follow_up = db.query(FollowUp).filter(FollowUp.interaction_id == interaction.id).first()
    
    if follow_up:
        db_elapsed = (time.perf_counter() - db_start) * 1000
        print(f"[TIMER] Database operations (fetched existing follow-up) took: {db_elapsed:.2f}ms")
        
        msg = f"**Follow-up Details**\n\n"
        msg += f"- **Doctor**: {hcp_name}\n"
        msg += f"- **Date**: {follow_up.due_date.isoformat()}\n"
        msg += f"- **Action**: {follow_up.action}\n"
        msg += f"- **Status**: {follow_up.status}\n"
        
        return {
            "success": True,
            "message": msg,
            "extracted_data": extracted_form,
            "suggestions": {
                "active_interaction_id": active_interaction_id,
                "action": follow_up.action,
                "due_date": follow_up.due_date.isoformat(),
                "status": follow_up.status
            }
        }

    # 3. If no follow-up exists, only generate recommendations if query explicitly requests suggestions
    query_lower = query_text.lower()
    is_requesting_suggestions = any(word in query_lower for word in ["suggest", "recommend", "next action", "next step", "what should i do", "what do i do"])
    
    if is_requesting_suggestions:
        # Custom recommendation engine logic based on products & sentiment
        topics = (interaction.topics_discussed or "").lower()
        sentiment = (interaction.sentiment or "").lower()

        suggested_action = "Schedule follow-up phone call to gather feedback."
        suggested_materials = "Clinical trial whitepaper"
        days_to_followup = 14

        if "product x" in topics or "prodo-x" in topics:
            suggested_materials = "Product X Efficacy Brochure & Dosage Guide"
            suggested_action = f"Provide sample kits of Product X to {hcp_name}'s clinic."
        elif "product y" in topics:
            suggested_materials = "Product Y Safety Profiles & Comparative Studies"
            suggested_action = f"Schedule a follow-up presentation on Product Y side effects."

        if sentiment == "negative":
            suggested_action = f"Escalate concerns regarding product pricing/efficacy. Schedule an in-person meeting with {hcp_name} and the regional sales manager."
            days_to_followup = 5
        elif sentiment == "neutral":
            suggested_action = f"Send follow-up email with additional clinical trial documentation and check in after 10 days."
            days_to_followup = 10
        else: # Positive
            suggested_action = f"Arrange a follow-up lunch meeting to discuss clinic-wide deployment and patient selection."
            days_to_followup = 14

        due_date = datetime.date.today() + datetime.timedelta(days=days_to_followup)

        msg = f"**AI Recommendations for {hcp_name}:**\n\n"
        msg += f"1. **Next Recommended Action**: {suggested_action}\n"
        msg += f"2. **Suggested Materials to Send**: {suggested_materials}\n"
        msg += f"3. **Suggested Timeline**: Follow up on or before **{due_date.isoformat()}** ({days_to_followup} days from today).\n\n"
        msg += "Would you like me to create this follow-up task?"

        db_elapsed = (time.perf_counter() - db_start) * 1000
        print(f"[TIMER] Database operations (suggested new follow-up) took: {db_elapsed:.2f}ms")
        
        return {
            "success": True,
            "message": msg,
            "extracted_data": extracted_form,
            "suggestions": {
                "active_interaction_id": active_interaction_id,
                "action": suggested_action,
                "materials": suggested_materials,
                "due_date": due_date.isoformat(),
                "days_to_followup": days_to_followup
            }
        }
    else:
        db_elapsed = (time.perf_counter() - db_start) * 1000
        print(f"[TIMER] Database operations (no suggestions requested) took: {db_elapsed:.2f}ms")
        
        return {
            "success": True,
            "message": "No follow-up has been scheduled for this interaction yet. Ask me to 'Suggest follow-up' if you need recommendations.",
            "extracted_data": extracted_form,
            "suggestions": {
                "active_interaction_id": active_interaction_id
            }
        }
