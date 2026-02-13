# AutoPlanner(Working in Progress)

Quickly parse user's natural language/pasted text into structured schedules and sync to user's calendar via Google Calendar API.

# This is a Vibe Coding project.
This project is coding by AI.

## How to Run
1) Install dependencies
```bash
pip install -r requirements.txt
```
2) Prepare Google OAuth (Web application client, recommended)
- Enable Google Calendar API in Google Cloud Console
- Create OAuth client (Type: Web application)
- Place the client JSON in the project root directory (e.g., `webclient.json`), or set the path environment variable
- Configure authorization callback (example)
  - `http://localhost:8000/oauth/google/callback`
3) Configure environment variables (example)
```
GOOGLE_OAUTH_CLIENT_JSON_PATH=./webclient.json
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8000/oauth/google/callback
GOOGLE_OAUTH_SCOPES=https://www.googleapis.com/auth/calendar.events
```
4) Migrate database
```bash
python manage.py migrate
```
5) Start development server
```bash
python manage.py runserver
```
