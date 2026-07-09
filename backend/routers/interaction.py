from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import datetime
from database.database import get_db
from models import models
from schemas import schemas
from auth.auth import get_current_user

router = APIRouter(prefix="/api/interactions", tags=["Interactions"])

@router.get("", response_model=List[schemas.InteractionOut])
def get_interactions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Interaction)\
        .filter(models.Interaction.user_id == current_user.id)\
        .order_by(models.Interaction.date.desc())\
        .all()

@router.post("", response_model=schemas.InteractionOut)
def create_interaction(
    interaction_data: schemas.InteractionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    new_interaction = models.Interaction(
        user_id=current_user.id,
        hcp_id=interaction_data.hcp_id,
        type=interaction_data.type,
        date=interaction_data.date,
        time=interaction_data.time,
        topics_discussed=interaction_data.topics_discussed,
        materials_shared=interaction_data.materials_shared,
        sentiment=interaction_data.sentiment,
        notes=interaction_data.notes,
        summary=interaction_data.summary,
        follow_up_date=interaction_data.follow_up_date
    )
    db.add(new_interaction)
    db.commit()
    db.refresh(new_interaction)

    if interaction_data.follow_up_date:
        follow_up = models.FollowUp(
            interaction_id=new_interaction.id,
            action=f"Follow-up regarding {interaction_data.topics_discussed or 'previous meeting'}",
            due_date=interaction_data.follow_up_date,
            status="Pending"
        )
        db.add(follow_up)
        db.commit()

    return new_interaction

@router.put("/{interaction_id}", response_model=schemas.InteractionOut)
def update_interaction(
    interaction_id: int,
    interaction_data: schemas.InteractionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    interaction = db.query(models.Interaction).filter(
        models.Interaction.id == interaction_id,
        models.Interaction.user_id == current_user.id
    ).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    interaction.hcp_id = interaction_data.hcp_id
    interaction.type = interaction_data.type
    interaction.date = interaction_data.date
    interaction.time = interaction_data.time
    interaction.topics_discussed = interaction_data.topics_discussed
    interaction.materials_shared = interaction_data.materials_shared
    interaction.sentiment = interaction_data.sentiment
    interaction.notes = interaction_data.notes
    interaction.summary = interaction_data.summary
    interaction.follow_up_date = interaction_data.follow_up_date

    db.commit()
    db.refresh(interaction)
    return interaction

@router.delete("/{interaction_id}")
def delete_interaction(
    interaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    interaction = db.query(models.Interaction).filter(
        models.Interaction.id == interaction_id,
        models.Interaction.user_id == current_user.id
    ).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")

    db.delete(interaction)
    db.commit()
    return {"detail": "Interaction deleted successfully"}


# --- Dashboard Stats Endpoint ---
@router.get("/stats/dashboard")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    user_id = current_user.id
    today = datetime.date.today()

    # 1. Total HCPs
    total_hcps = db.query(models.HCP).filter(models.HCP.created_by == user_id).count()

    # 2. Total Interactions
    total_interactions = db.query(models.Interaction).filter(models.Interaction.user_id == user_id).count()

    # 3. Today's Meetings
    todays_meetings_count = db.query(models.Interaction).filter(
        models.Interaction.user_id == user_id,
        models.Interaction.date == today
    ).count()

    # 4. Upcoming Follow-ups (due date >= today and pending status)
    upcoming_followups = db.query(models.FollowUp).join(models.Interaction).filter(
        models.Interaction.user_id == user_id,
        models.FollowUp.due_date >= today,
        models.FollowUp.status == "Pending"
    ).all()
    upcoming_followups_count = len(upcoming_followups)

    # 5. Recent Interactions List (last 5)
    recent_interactions = db.query(models.Interaction).filter(
        models.Interaction.user_id == user_id
    ).order_by(models.Interaction.date.desc(), models.Interaction.created_at.desc()).limit(5).all()

    recent_interactions_out = []
    for item in recent_interactions:
        hcp = db.query(models.HCP).filter(models.HCP.id == item.hcp_id).first()
        recent_interactions_out.append({
            "id": item.id,
            "hcp_name": hcp.name if hcp else "Unknown",
            "type": item.type,
            "date": item.date.isoformat(),
            "time": item.time,
            "topics": item.topics_discussed,
            "sentiment": item.sentiment,
            "summary": item.summary
        })

    # 6. Sentiment Breakdown
    sentiment_data = db.query(
        models.Interaction.sentiment,
        func.count(models.Interaction.id)
    ).filter(models.Interaction.user_id == user_id).group_by(models.Interaction.sentiment).all()

    sentiment_chart = [{"name": s[0] or "Neutral", "value": s[1]} for s in sentiment_data]

    # 7. Interaction Trends over last 7 days
    trends_chart = []
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        cnt = db.query(models.Interaction).filter(
            models.Interaction.user_id == user_id,
            models.Interaction.date == day
        ).count()
        trends_chart.append({
            "date": day.strftime("%b %d"),
            "meetings": cnt
        })

    # 8. Follow-up timeline
    followup_list = []
    for f in upcoming_followups:
        inter = db.query(models.Interaction).filter(models.Interaction.id == f.interaction_id).first()
        hcp = db.query(models.HCP).filter(models.HCP.id == inter.hcp_id).first() if inter else None
        followup_list.append({
            "id": f.id,
            "hcp_name": hcp.name if hcp else "Unknown",
            "action": f.action,
            "due_date": f.due_date.isoformat(),
            "status": f.status
        })

    # 9. AI Activity Summary
    # Return count of tools used or general logs (mocked based on counts for visual UI state)
    ai_actions_count = db.query(models.Interaction).filter(
        models.Interaction.user_id == user_id,
        models.Interaction.summary != None
    ).count()

    return {
        "summary": {
            "total_hcps": total_hcps,
            "total_interactions": total_interactions,
            "todays_meetings": todays_meetings_count,
            "upcoming_followups": upcoming_followups_count,
            "ai_activities": ai_actions_count
        },
        "recent_interactions": recent_interactions_out,
        "upcoming_followups_list": followup_list,
        "sentiment_chart": sentiment_chart if sentiment_chart else [{"name": "Positive", "value": 0}],
        "trends_chart": trends_chart
    }
