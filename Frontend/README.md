# Finace Frontend

Next.js 15 UI for the Finace compliance platform (landing + dashboard).

## Stack

- Next.js App Router, Tailwind, Framer Motion, Recharts  
- **Redux Toolkit** (`auth`, `reports`, `chatSessions`)  
- Auth cookies: `finace_token`, `finace_user`  
- API base: `NEXT_PUBLIC_API_BASE_URL` → Node gateway (`/api/v1`)

## Main routes

| Route | Purpose |
|-------|---------|
| `/` | Marketing landing (auth-aware nav) |
| `/login` | Company / evaluator sign-in |
| `/dashboard/workflow` | Compliance Studio (chat + SHAP + recents) |
| `/dashboard/evaluator` | Evaluator console |
| Report detail pages | Health header + explainability panel |

## Run locally

```bash
npm install
npm run dev
```

`.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:5000/api/v1
NEXT_PUBLIC_RBI_DOCS_DRIVE_URL=
```

Open `http://localhost:3000`. Requires Node API (`:5000`) and Python RAG (`:8000`) for full chat/analysis.

## Deploy on Vercel

1. Connect the `Frontend/` directory (or monorepo root with root dir = `Frontend`).
2. Set environment variables:

```env
NEXT_PUBLIC_API_BASE_URL=https://finace.sambhav-mani-tripathi.tech/api/v1
NEXT_PUBLIC_RBI_DOCS_DRIVE_URL=https://drive.google.com/...
```

3. Deploy. The frontend calls the **Node API on EC2** — not Python RAG directly.

## Notes

- Compliance Studio sends **full conversation context** on every follow-up.  
- Chat sessions persist via `/api/v1/chats` (sidebar Recents).  
- XAI UI: `components/reports/ExplainabilityPanel.tsx`.  
- **Analyze** tab: `components/reports/AnalyzeTrustDashboard.tsx` — trust index + charts from session scores/XAI.

See repo root [SESSION_HISTORY.md](../SESSION_HISTORY.md) and [setup.md](../setup.md) for full system reference.
