# Setup Guide — Maintenance Prédictive Industrielle

## Requirements

| Tool | Minimum version | Check |
|---|---|---|
| **Python** | 3.10+ | `python --version` |
| **Node.js** | 18+ | `node --version` |
| **npm** | 9+ | `npm --version` |

---

## Backend (FastAPI)

All commands are run from the **project root**.

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate the virtual environment

**Windows (PowerShell)**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (CMD)**
```cmd
.\.venv\Scripts\activate.bat
```

**macOS / Linux**
```bash
source .venv/bin/activate
```

> Your prompt should now show `(.venv)` to confirm it is active.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the API

```bash
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at **http://127.0.0.1:8000**.  
Interactive docs: **http://127.0.0.1:8000/docs**

---

## Frontend (React / Vite dashboard)

All commands are run from the **`dashboard/`** directory.

### 5. Install Node modules

```bash
cd dashboard
npm install
```

### 6. Start the dev server

```bash
npm run dev
```

The dashboard will be available at **http://localhost:5173**.

> Make sure the API is running first — the dashboard calls it on startup.