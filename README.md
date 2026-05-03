# Elector AI Production Build Plan

## Summary
Build Elector AI as both:
- A preserved single-file Flask demo for Phases 1-6.
- A structured production app with `backend/`, `frontend/`, and `mobile/` for Phases 7-10.

The production version will use Flask + SocketIO + SQLite + React/Vite, with ChatGPT-style streaming chat, local auth, chat memory, English/Tamil UI, admin dashboard, voice controls, mock live-election endpoints, and Cloud Run-ready deployment files.

## Key Changes
- Replace legacy Gemini setup with the current `google-genai` SDK and default model `gemini-2.5-flash`, based on Google’s current Gemini API guidance and model docs:
  - https://ai.google.dev/gemini-api/docs/libraries
  - https://firebase.google.com/docs/vertex-ai/gemini-models
- Add dual AI mode:
  - `gemini_api`: uses `GEMINI_API_KEY`.
  - `vertex_ai`: uses `PROJECT_ID=project-7eb55a30-5579-43cc-8d1`, `GOOGLE_CLOUD_LOCATION`, and Vertex auth.
- Add backend architecture:
  - Flask app factory.
  - SocketIO streaming endpoint.
  - SQLite models for users, sessions, chats, messages, election data, and admin role.
  - REST endpoints for auth, chat history, language preference, admin summaries, and mock live election data.
- Add frontend architecture:
  - React/Vite ChatGPT-style UI.
  - Sidebar chat history.
  - Streaming assistant messages.
  - Gemini/Vertex mode toggle.
  - English/Tamil language toggle.
  - Election guide, timeline, quiz, live election cards, admin dashboard, and voice assistant controls.
- Keep a `single_file_app.py` version that serves embedded HTML through Flask for the earlier hackathon demo path.

## Public Interfaces
- Backend routes:
  - `POST /api/auth/signup`
  - `POST /api/auth/login`
  - `POST /api/auth/logout`
  - `GET /api/auth/me`
  - `GET /api/chats`
  - `POST /api/chats`
  - `GET /api/chats/<chat_id>/messages`
  - `GET /api/elections/live`
  - `GET /api/admin/users`
  - `GET /api/admin/chats`
- SocketIO events:
  - Client emits `chat:send` with `chat_id`, `message`, `mode`, and `language`.
  - Server emits `chat:chunk`, `chat:done`, and `chat:error`.
- Environment template:
  - `SECRET_KEY`
  - `GEMINI_API_KEY`
  - `GEMINI_MODEL=gemini-2.5-flash`
  - `PROJECT_ID=project-7eb55a30-5579-43cc-8d1`
  - `GOOGLE_CLOUD_LOCATION=global`
  - `DATABASE_URL=sqlite:///elector_ai.db`
  - `FLASK_ENV=development`
  - `ADMIN_EMAIL`

## Project Structure
```text
Elector-main/
  app.py
  single_file_app.py
  requirements.txt
  .env.example
  README.md
  Dockerfile
  .dockerignore
  backend/
    app/
      __init__.py
      config.py
      extensions.py
      models.py
      auth.py
      chat.py
      ai.py
      elections.py
      admin.py
      sockets.py
    run.py
  frontend/
    package.json
    vite.config.js
    index.html
    src/
      App.jsx
      main.jsx
      api/
      components/
      pages/
      styles/
      i18n/
  mobile/
    README.md
    app.json
    src/
      screens/
      services/
  instance/
    .gitkeep
  elector-ai.zip
```

## Test Plan
- Backend:
  - Import/app factory smoke test.
  - SQLite initialization test.
  - Signup/login/logout flow.
  - Chat persistence test.
  - Mock election data endpoint test.
  - Gemini mode error handling when API key is missing.
  - Vertex mode error handling when GCP credentials are missing.
- Frontend:
  - `npm run build`.
  - Verify login, signup, chat streaming UI, mode toggle, language toggle, quiz, timeline, voice buttons, and admin page render.
- Runtime:
  - Start Flask backend.
  - Start React frontend.
  - Confirm SocketIO connects and streams chunks.
  - Build ZIP excluding `.venv`, `.venv-1`, `.env`, database files, caches, and `node_modules`.

## Assumptions
- Use React/Vite plus the single-file Flask demo, per your selected “Both versions” choice.
- Live election data will be API-ready mock data for now, with a clean backend contract for future real data.
- Authentication will be local SQLite auth with hashed passwords and session cookies.
- Voice support will use browser Web Speech APIs where available, with graceful fallback text controls.
- The ZIP will be generated as `elector-ai.zip` in the repo root after implementation.
