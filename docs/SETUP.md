# Local Setup

## Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # fill in real values, or leave defaults for Dell-only dev

# Start Postgres + Redis (or point at existing instances)
docker compose up -d db redis

# Apply schema
psql "$DATABASE_URL" -f migrations/001_init.sql

# Run the API
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive OpenAPI docs.

Trigger a manual ingestion run without waiting for the scheduler:

```bash
curl -X POST http://localhost:8000/api/v1/ingest/dell
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000`. Set `NEXT_PUBLIC_API_BASE_URL` in
`frontend/.env.local` if the backend isn't on `localhost:8000`.

## Environment variables (backend/.env.example)

| Variable | Required | Notes |
|---|---|---|
| `DATABASE_URL` | yes | Postgres connection string |
| `REDIS_URL` | yes | Redis connection string |
| `CISCO_CLIENT_ID` / `CISCO_CLIENT_SECRET` | for Cisco adapter | DevNet OAuth2 app |
| `DELL_CSAF_BASE_URL` | no | defaults to public Dell CSAF endpoint |
| `INGESTION_INTERVAL_HOURS` | no | default `6` |

## Tests

```bash
cd backend
pytest
```
