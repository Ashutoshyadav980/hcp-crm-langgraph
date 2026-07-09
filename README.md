# HCP Connect - AI-First Healthcare CRM Interaction Module

A production-ready full-stack AI-first CRM designed for pharmaceutical sales representatives to log and manage interactions with Healthcare Professionals (HCPs) using natural language. Instead of manually filling forms, representatives speak or type their session notes, and a LangGraph-powered AI agent automatically classifies intent, routes to appropriate database tools, parses structured details, and synchronizes the frontend form.

---

## Technical Stack
- **Frontend**: React (Vite) + Redux Toolkit + React Router + Tailwind CSS (Google Fonts Inter, Lucide React, Recharts visualization)
- **Backend**: Python FastAPI + Uvicorn + SQLAlchemy
- **AI Co-pilot**: LangGraph State Workflow + Groq (`gemma2-9b-it`)
- **Database**: SQLite (default setup-free local runner), MySQL, or PostgreSQL

---

## Project Structure
```text
ai-project/
├── backend/
│   ├── agent_graph/
│   │   └── agent.py         # LangGraph workflow, state schemas, and conditional routing
│   ├── auth/
│   │   └── auth.py          # JWT, bcrypt password hashing, and user dependencies
│   ├── database/
│   │   └── database.py      # SQLAlchemy session lifecycle supporting multiple SQL engines
│   ├── models/
│   │   └── models.py        # Relational models: User, HCP, Interaction, FollowUp, Product
│   ├── routers/
│   │   ├── auth.py          # Register, login, logout, me profile endpoints
│   │   ├── hcp.py           # HCP profile CRUD
│   │   ├── interaction.py   # Interactions CRUD & complex dashboard statistics
│   │   └── chat.py          # LangGraph agent entrypoint
│   ├── schemas/
│   │   └── schemas.py       # Pydantic validation schemas
│   ├── tools/
│   │   └── tools.py         # LangGraph tools (Log, Edit, Search, History, Suggest)
│   ├── .env                 # Local variables
│   ├── main.py              # Application entrypoint & auto-seeding engine
│   └── requirements.txt     # Python libraries
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx         # Analytics charts, metrics, recent activities, and tasks
│   │   │   ├── InteractionModule.jsx # Split-screen locked form & AI chat module
│   │   │   ├── Login.jsx
│   │   │   └── Register.jsx
│   │   ├── redux/
│   │   │   ├── authSlice.js
│   │   │   ├── interactionSlice.js
│   │   │   └── store.js
│   │   ├── api.js           # Central Axios endpoint settings
│   │   ├── App.jsx          # Client route definitions
│   │   ├── index.css        # Tailwind directive and base styling
│   │   └── main.jsx         # DOM Mounting entrypoint
│   ├── index.html
│   ├── tailwind.config.js
│   └── package.json
└── README.md
```

---

## 5 LangGraph Tools Implemented
1. **LogInteractionTool**: Automatically extracts the doctor's name, hospital, specialty, products discussed, sentiment, materials shared, and follow-up duration from unstructured text. It automatically creates the HCP profile if it doesn't exist, saves the interaction to the database, and returns the fields to sync the React form.
2. **EditInteractionTool**: Enables representatives to modify saved interactions in real-time using natural language statements (e.g. *"Actually he was negative and remove brochures"*). Updates only the affected database fields and synchronization states.
3. **SearchHCPTool**: Queries registered doctor profiles by name, specialty, or hospital, and displays their profile summary and touchpoint history.
4. **InteractionHistoryTool**: Returns a chronological list of recent meetings with the active doctor to keep sales reps informed.
5. **SuggestFollowupTool**: Processes discussion topics, products discussed, and doctor sentiment to suggest relevant next steps, tailored documents to send, sample kits to distribute, and recommended due dates.

---

## Getting Started Locally

### Prerequisites
- Node.js (v18+)
- Python (3.11 or 3.12)
- Groq API Key (Optional. If not provided, a robust mock parser fallback in the backend handles all prompts for instant out-of-the-box evaluation).

### 1. Set Up the Backend
1. Open a terminal and navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Create a virtual environment and install packages:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Mac/Linux:
   source .venv/bin/activate

   pip install -r requirements.txt
   ```
3. Copy/configure environment variables (we pre-created a default `.env` file supporting SQLite):
   ```bash
   cp .env.example .env
   # Open .env and write your GROQ_API_KEY if testing live LLM routing.
   ```
4. Run the backend server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
The backend database will automatically initialize a local `crm.db` database and seed it with initial products and doctor profiles on startup.

### 2. Set Up the Frontend
1. Open a new terminal and navigate to the frontend folder:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Run the Vite development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to: `http://localhost:5173/`

---

## Seeded Test Credentials
The database has been seeded with a default sales representative account. Use these credentials to log in:
- **Email**: `sales@hcp-crm.com`
- **Password**: `sales123`

---

## Live User Flow Evaluation
Once logged in, go to the **Log HCP Interaction** page and click the suggestion chips to trigger the exact assignment prompts:
1. Click **1. Log New Interaction** to submit:
   > *"Today I met Dr. Robert Smith at Grace Hospital. We discussed Product X efficiency. Sentiment was positive, and I shared the brochures. Follow up in 10 days."*
   - *Observation*: The structured form on the left instantly populates with all details.
2. Click **2. Edit Interaction (Changes)** to submit:
   > *"Actually change the follow-up date to next Friday and remove brochures."*
   - *Observation*: The form details on the left dynamically update (follow-up date changes, brochures are cleared).
3. Click **3. Suggest Follow-up Actions**:
   - *Observation*: The assistant suggests customized recommendations based on Product X.
4. Click **4. Show History** or **5. Search HCP Profile** to verify the other built-in tools.
