from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database.database import get_db
from models import models
from schemas import schemas
from auth.auth import get_current_user

router = APIRouter(prefix="/api/hcps", tags=["HCPs"])

@router.get("", response_model=List[schemas.HCPOut])
def get_hcps(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.HCP).filter(models.HCP.created_by == current_user.id).all()

@router.get("/{hcp_id}", response_model=schemas.HCPOut)
def get_hcp(
    hcp_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    hcp = db.query(models.HCP).filter(models.HCP.id == hcp_id, models.HCP.created_by == current_user.id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    return hcp

@router.post("", response_model=schemas.HCPOut)
def create_hcp(
    hcp_data: schemas.HCPCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    new_hcp = models.HCP(
        name=hcp_data.name,
        hospital=hcp_data.hospital,
        specialty=hcp_data.specialty,
        phone=hcp_data.phone,
        email=hcp_data.email,
        created_by=current_user.id
    )
    db.add(new_hcp)
    db.commit()
    db.refresh(new_hcp)
    return new_hcp

@router.put("/{hcp_id}", response_model=schemas.HCPOut)
def update_hcp(
    hcp_id: int,
    hcp_data: schemas.HCPCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    hcp = db.query(models.HCP).filter(models.HCP.id == hcp_id, models.HCP.created_by == current_user.id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    
    hcp.name = hcp_data.name
    hcp.hospital = hcp_data.hospital
    hcp.specialty = hcp_data.specialty
    hcp.phone = hcp_data.phone
    hcp.email = hcp_data.email
    
    db.commit()
    db.refresh(hcp)
    return hcp

@router.delete("/{hcp_id}")
def delete_hcp(
    hcp_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    hcp = db.query(models.HCP).filter(models.HCP.id == hcp_id, models.HCP.created_by == current_user.id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    
    db.delete(hcp)
    db.commit()
    return {"detail": "HCP deleted successfully"}
