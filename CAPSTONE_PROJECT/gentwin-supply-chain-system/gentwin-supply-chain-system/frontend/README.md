# Supply Chain Digital Twin — Frontend

Next.js 14 (App Router) + TypeScript + Tailwind + Recharts dashboard for the
**Generative AI & Digital Twin Supply Chain Resilience System**, with
sign-in / sign-up screens gating the dashboard.

## Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local   # optional: point at a non-default backend URL
```

## Run

```bash
npm run dev
```

Open http://localhost:3000. Requires the FastAPI backend running at
`http://localhost:8000` (see `../backend/README.md`) — you'll be sent to
`/login` immediately.

## Project Layout

```
app/
  layout.tsx          # Root layout, wraps everything in AuthProvider
  page.tsx              # Dashboard page, wrapped in AuthGuard
  login/page.tsx           # Sign-in form
  register/page.tsx          # Sign-up form
  globals.css                  # Tailwind base + light, friendly theme tokens
context/
  AuthContext.tsx      # In-memory session state (see "Auth model" below)
components/
  AuthGuard.tsx         # Redirects to /login if there's no active session
  Header.tsx              # Status badge, metrics bar, user badge, sign-out,
                             admin-only reset button
  NetworkMap.tsx             # Real world map (react-simple-maps) with country
                                borders, auto-fit zoom, and node/edge overlay
  ChainBuilder.tsx             # Describe your own supply chain in plain text;
                                  AI turns it into a network you can simulate
  DisruptionConsole.tsx           # Natural language prompt + AI-suggested or
                                     preset scenarios
  ImpactMetrics.tsx                  # KPI cards + baseline/disrupted/optimized chart
  OptimizationCard.tsx                  # Route comparison table + reroute KPIs
lib/
  api.ts       # Axios client (auth endpoints + twin endpoints, token injection)
  types.ts     # Shared TypeScript types mirroring backend Pydantic schemas
```

## Auth model

Session state (JWT + user profile) lives only in `AuthContext`'s React
state — never in `localStorage`, `sessionStorage`, or a cookie. That means
every time the app is opened fresh (new tab, refresh, browser restart)
the person is sent back to `/login` and must enter their username and
password again. This matches the requirement that returning users are
always prompted to log back in, rather than being silently kept signed
in.

Regular users see the full dashboard (network map, disruption simulation,
route optimization). The "Reset Network State" button in the header only
renders for accounts with the `admin` role — the backend also rejects the
underlying request from non-admins, so this isn't just a UI-level
restriction.

## AI usage is on-demand, not automatic

Because the Gemini free tier's daily quota is small, `DisruptionConsole`
only calls `/twin/suggest-scenarios` when the person clicks "Suggest
scenarios for my network" — not automatically on page load, chain
generation, or reset. The built-in preset scenarios are always shown
immediately with zero API cost; AI-tailored ones are opt-in.

## Verified
`npm run build` completes cleanly (TypeScript strict mode, no errors) and
produces a static-optimized production build across all four routes
(`/`, `/login`, `/register`, `/_not-found`).

## Notes
- `NEXT_PUBLIC_API_BASE_URL` env var overrides the default
  `http://localhost:8000/api/v1` backend URL.
- The network map (`NetworkMap.tsx`) uses `react-simple-maps` with a real
  world atlas (country borders), so nodes and routes render on an actual
  recognizable map — not an abstract grid. It fetches a small (~100KB)
  static country-boundary file from a public CDN the first time the map
  loads (cached by the browser afterward), so an internet connection is
  needed for that one-time load, same as for the Gemini API calls.
- The map auto-fits: it zooms and centers based on whichever nodes are
  currently loaded, so a global sample network shows the whole world,
  while a custom chain confined to one city or region zooms in on it
  automatically.
