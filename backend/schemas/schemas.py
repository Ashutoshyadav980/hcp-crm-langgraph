from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import datetime

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# --- Product Schemas ---
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductOut(ProductBase):
    id: int

    class Config:
        from_attributes = True

# --- HCP Schemas ---
class HCPBase(BaseModel):
    name: str
    hospital: Optional[str] = None
    specialty: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class HCPCreate(HCPBase):
    pass

class HCPOut(HCPBase):
    id: int
    created_by: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- FollowUp Schemas ---
class FollowUpBase(BaseModel):
    action: str
    due_date: datetime.date
    status: Optional[str] = "Pending"
    notes: Optional[str] = None

class FollowUpCreate(FollowUpBase):
    pass

class FollowUpOut(FollowUpBase):
    id: int
    interaction_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- Interaction Schemas ---
class InteractionBase(BaseModel):
    hcp_id: int
    type: Optional[str] = "Meeting"
    date: datetime.date
    time: Optional[str] = None
    topics_discussed: Optional[str] = None
    materials_shared: Optional[str] = None
    sentiment: Optional[str] = None
    notes: Optional[str] = None
    summary: Optional[str] = None
    follow_up_date: Optional[datetime.date] = None

class InteractionCreate(InteractionBase):
    pass

class InteractionOut(InteractionBase):
    id: int
    user_id: int
    created_at: datetime.datetime
    hcp: Optional[HCPOut] = None
    follow_ups: List[FollowUpOut] = []

    class Config:
        from_attributes = True

# --- Chat/Agent Schemas ---
class ChatMessage(BaseModel):
    message: str
    active_interaction_id: Optional[int] = None # Send active interaction ID to enable editing it

class ChatResponse(BaseModel):
    response: str
    tool_triggered: Optional[str] = None
    extracted_data: Optional[dict] = None # Synchronize extracted form fields to React Redux store
    chat_history: List[dict] = []
