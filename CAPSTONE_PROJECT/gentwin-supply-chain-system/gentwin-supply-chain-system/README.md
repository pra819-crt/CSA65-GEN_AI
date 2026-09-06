# GenTwin — Supply Chain Resilience System

Generative AI & Digital Twin-Based Supply Chain Resilience & Disruption
Management System, with sign-in for individual users and an admin role.

```
supply-chain-twin/
  backend/    FastAPI + NetworkX + Gemini + JWT auth
  frontend/   Next.js 14 + TypeScript + Tailwind + Recharts
```

## Quickstart

**1. Backend**
```bash
cd backend
python3 -m venv venv && venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env          # then edit .env: set GEMINI_API_KEY and SECRET_KEY
uvicorn app.main:app --reload --port 8000
```

**2. Frontend** (in a second terminal)
```bash
cd frontend
npm install
npm run dev
```

**3. Open** http://localhost:3000 — you'll land on the sign-in page.

## Signing in

Two ways in:

- **Create your own account** — click "Create an account" on the login
  page, pick a username and password. New accounts are always regular
  `user` role.
- **Use the seeded admin account** — username `admin`, password `Admin@123`
  (from `.env.example` — **change `DEFAULT_ADMIN_PASSWORD` before any real
  deployment**). Admins can additionally reset the network state; regular
  users can view the network, run disruption simulations, and compute
  reroutes.

## How login persistence works (by design)

Every screen behind the dashboard requires a valid session. That session
token is kept **only in the browser's memory** (React state) — it is never
written to `localStorage`, `sessionStorage`, or a cookie. This means:

- Closing the tab, refreshing the page, or reopening the app always drops
  you back to the sign-in screen.
- You (or the admin) must enter username + password again each time to get
  back into the dashboard.

This was a deliberate choice per the requirement that the system always
asks for credentials on every new visit, rather than silently
auto-logging users back in. If you'd prefer a "remember me" experience
instead (token persisted across reloads), that's a small change to
`frontend/context/AuthContext.tsx` — happy to add it if you'd rather have
that instead.

## Latest fixes & polish

- **Fixed: "network error" on Path Comparison & Rerouting.** The origin/
  destination dropdowns could silently hold onto node IDs from a
  *previous* network (e.g. right after generating a custom chain or
  resetting), causing the optimize request to fail. Selections now
  automatically re-sync to valid IDs whenever the loaded network changes.
- **Fixed: overlapping/merging names on the map.** Node labels now use
  collision detection — if two nodes sit close together (very common in a
  small custom chain, e.g. a warehouse and retailer in the same city),
  only one gets a permanent label; hovering still shows every node's full
  name and details either way. Very dense networks skip static labels
  entirely and rely on hover to avoid clutter.
- **More colorful, stylish design.** Replaced the flat light theme with a
  softly gradient page background, a colorful gradient header banner, and
  each panel (chain builder, disruption simulator, map, optimizer, impact
  analysis) now has its own accent color and tinted cards — while keeping
  text contrast and readability as the priority.



You don't have to start from the built-in sample network. On the dashboard,
click **"Get started"** under **"Use Your Own Supply Chain"**, describe your
suppliers, factories, warehouses, and routes in plain language (a couple of
sentences is enough), and click **"Build My Supply Chain."** The AI turns
that description into a network you can actually simulate against — and it
becomes your new baseline, so resetting the network returns to *your* chain,
not the demo one. Click "Use sample instead" any time to go back to the demo.

Once you have a network loaded (yours or the sample), the **Disruption
Simulator** panel automatically asks the AI for 3-4 realistic disruption
scenarios tailored to *your* specific nodes and routes — you don't have to
think one up yourself. If none of the suggestions match what you're
worried about, just type your own scenario in the text box instead; it
runs through the exact same simulation and gives you the same cost/time
comparison and mitigation recommendations either way.

## About Gemini API quota limits

Google's **free tier** for the Gemini API caps requests at a small daily
number per model (often as low as ~20/day). If you hit that limit, calls
to "Build My Supply Chain," disruption simulation, or "Suggest scenarios"
will fail with a clear message telling you the quota is exhausted and
pointing to Google's rate-limit docs — instead of crashing with a raw
error.

Two things help you get more out of a free-tier key while testing:
- **AI-suggested scenarios are on-demand, not automatic.** Clicking
  "Suggest scenarios for my network" is the only thing that spends a
  quota unit for that feature — it no longer fires automatically on
  every page load or reset.
- Consider enabling billing on your Google AI Studio / Gemini API project
  if you plan to demo this repeatedly in a single day; the paid tier's
  quota is far higher.

## What changed for user-friendliness

- **Light color theme** instead of the previous dark/navy enterprise look —
  easier to read at a glance, especially for people less used to
  dashboard-style tools.
- **Gemini 3.5 Flash** (current generation) instead of the older 2.5 Flash
  used previously.
- **Describe-your-own-chain** flow (above) so a new user doesn't need to
  understand graph/network concepts to get started — they just describe
  their business in a sentence or two.
- **AI-suggested disruptions** tailored to whatever network is loaded, so
  people aren't stuck staring at a blank text box wondering what to type.



- Login and registration forms give inline validation errors (weak password,
  username taken, wrong credentials) instead of silent failures.
- The header always shows who's signed in and their role (`user` /
  `admin`), with a one-click sign-out.
- Regular users don't see the "Reset Network State" button at all — it's
  only rendered for admins — instead of a confusing "access denied" click.
- Preset disruption scenario buttons let a new user try the system
  immediately without having to write a prompt from scratch.
- Every API error (expired session, backend unreachable, invalid route
  selection) surfaces as a plain-language message in the UI, not a raw
  stack trace.

## Security notes for going beyond a demo

- Set a strong random `SECRET_KEY` in `backend/.env` (see the comment in
  `.env.example` for a one-liner to generate one).
- Change `DEFAULT_ADMIN_PASSWORD` before deploying anywhere reachable by
  others.
- The user database is a local SQLite file (`supply_chain_twin.db`) —
  fine for a course project or demo; swap for a managed database before
  production use.
- HTTPS termination (e.g. via a reverse proxy) is assumed in front of
  this stack for any real deployment, since JWTs are sent as Bearer
  tokens over the network.

See `backend/README.md` and `frontend/README.md` for more detail on each
half.
