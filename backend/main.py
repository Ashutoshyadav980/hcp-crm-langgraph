from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from database.database import engine, Base, SessionLocal
from models import models
from routers import auth, hcp, interaction, chat

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Healthcare CRM HCP Interaction API",
    description="FastAPI Backend for AI-First CRM Interaction Module using LangGraph and Groq",
    version="1.0.0"
)

# CORS Middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(hcp.router)
app.include_router(interaction.router)
app.include_router(chat.router)


# --- Database Auto-Seeding ---
def seed_database():
    db = SessionLocal()
    try:
        # Check if products exist, if not, add them
        if db.query(models.Product).count() == 0:
            products = [
                models.Product(name="Product X", description="A premium drug for cardiovascular conditions and hypertension control."),
                models.Product(name="Product Y", description="An advanced medication for migraine prevention and chronic neurological therapy."),
                models.Product(name="Product Z", description="A clinical oncology compound for targeted cancer treatment studies.")
            ]
            db.bulk_save_objects(products)
            db.commit()
            print("Successfully seeded database with default Products.")

        # Check if users exist. If not, seed a default admin/sales user
        if db.query(models.User).count() == 0:
            from auth.auth import get_password_hash
            default_user = models.User(
                email="sales@hcp-crm.com",
                hashed_password=get_password_hash("sales123"),
                full_name="Alex Sales Rep"
            )
            db.add(default_user)
            db.commit()
            db.refresh(default_user)
            print("Successfully seeded default Sales Representative user.")

            # Seed default HCPs for this default user
            hcp1 = models.HCP(
                name="Dr. Robert Smith",
                hospital="Grace Hospital",
                specialty="Cardiology",
                phone="+1 (555) 019-2834",
                email="robert.smith@gracehospital.org",
                created_by=default_user.id
            )
            hcp2 = models.HCP(
                name="Dr. Sarah Jenkins",
                hospital="City Health Clinic",
                specialty="Neurology",
                phone="+1 (555) 014-9988",
                email="sjenkins@cityhealth.org",
                created_by=default_user.id
            )
            hcp3 = models.HCP(
                name="Dr. James Anderson",
                hospital="Mercy Hospital",
                specialty="General Medicine",
                phone="+1 (555) 012-3456",
                email="james.anderson@mercy.com",
                created_by=default_user.id
            )
            db.add_all([hcp1, hcp2, hcp3])
            db.commit()
            print("Successfully seeded default HCP profiles.")

    except Exception as e:
        print("Database seeding failed:", e)
    finally:
        db.close()

# Run database seed on startup
@app.on_event("startup")
def on_startup():
    seed_database()

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Healthcare CRM API",
        "endpoints": {
            "auth": "/api/auth",
            "hcps": "/api/hcps",
            "interactions": "/api/interactions",
            "chat": "/api/chat"
        }
    }
