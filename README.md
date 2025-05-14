# Getting Started

First, run the development server:

Frontend

```bash
cd frontend
npm run dev
```

Backend (use venv)

```bash
(create venv with your prefered way)

conda create -n chatsphere python==3.12 -y

conda activate chatsphere

cd backend

uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

Wait for the below given message to appear in backend terminal, then
navigate to localhost:300 in your browser to use the app.

