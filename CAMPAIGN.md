# CAMPAIGN.md — NarcoGuard Awareness (client: narco)

Status: **configured, awaiting credentials + human approval gates**
Owner: `content_engine` (with `acquisition_engine` for outreach, `investor_relations` for funding)
Branch: `feat/narco-marketing-campaign`

---

## 1. What Chatty does for NarcoGuard

Chatty is a 24/7 autonomous marketing agent (Python/FastAPI backend + Next.js
dashboard). This campaign wires NarcoGuard into **her existing mechanisms only**
— no new config formats:

| Her mechanism | How NarcoGuard uses it |
|---|---|
| `POST /api/campaigns` (`CampaignRequest`) | Register the awareness campaign (payload in §2) |
| `n8n_workflows/*.json` on disk | `narcoguard-awareness-cadence_20261009_071800.json` — weekly cadence definition (same shape her API generates) |
| `POST /api/funding/run` | Draft pilot/grant outreach package for mission-aligned leads |
| `POST /api/email/send`, `leads/{id}/email` | Send **approved** outreach email (SendGrid/Resend, once keys exist) |
| `POST /api/proposals/draft`, `/press/pitch`, `/video/script` | AI-assisted drafts grounded only in the facts below |
| `POST /api/n8n/workflows/activate` | Push the cadence workflow to n8n when `N8N_*` creds exist |
| `autonomy` loop (`/api/autonomy/start`) | **Staying OFF for this campaign** until drafts are human-approved |
| Env vars `NARCOGUARD_URL`, `NARCOGUARD_FUNDING_URL` | Product + funding links auto-appended to outbound content |

**Hard rule for this campaign: nothing is sent or posted without a human
approving the exact text.** Drafts below are pre-written so approval is fast,
and the X path stays with the manual `publish_approved_x.py` flow
(`secure-key-setup` branch) that requires typing `PUBLISH`.

## 2. Campaign registration (run once the host is up)

These payloads match `CampaignRequest` in `AUTOMATION_API_SERVER.py` exactly
(`name`, `channel`, `goal`, optional `owner`, optional `metadata`):

```bash
curl -X POST "$CHATTY/api/campaigns" -H 'Content-Type: application/json' -d '{
  "name": "NarcoGuard Awareness",
  "channel": "x",
  "goal": "public awareness of the free NarcoGuard demo app",
  "owner": "content_engine",
  "metadata": {"workflow": "narcoguard-awareness-cadence_20261009_071800.json", "review_mode": "human_approval_required"}
}'

curl -X POST "$CHATTY/api/campaigns" -H 'Content-Type: application/json' -d '{
  "name": "NarcoGuard Pilot Partner Outreach",
  "channel": "pilot-outreach",
  "goal": "funding",
  "owner": "investor_relations",
  "metadata": {"icp": "public health agencies and harm-reduction organizations", "source": "leads.json"}
}'
```

## 3. Product truth (only facts the copy may use)

Grounded in `coden607/narcoguard-pwa` README; every draft below stays inside
these lines:

- NarcoGuard is a **free** public PWA and **research concept** at
  `https://narcoguard-pwa.vercel.app`. It is **not** a validated medical device,
  not an emergency dispatch service, not a treatment program. The demo does
  **not** auto-contact 911, dispatch responders, deliver naloxone, or alert
  loved ones. **In an immediate emergency, call 911.**
- Organization follows **Maslow's hierarchy of needs**: body/basic needs →
  safety/health → recovery/connection → stability/independence → growth/goals.
  A planning aid, not a ranking of people; help is never withheld based on
  stated needs.
- Features: needs-first **Find Help** resource search with on-device matching
  (`/help`); **Angel AI** listener that suggests small next steps — chats are
  not stored (`/angel`); **emergency + CPR steps** and training with **Hero
  certification** (`/ar`, `/hero-signup`); **Good Samaritan law summaries**;
  optional **Guardian Stability planner** for daily needs, sleep, goals,
  tomorrow's task, support contact — local storage only, pause/erase anytime
  (`/stability`); emergency contacts (`/contacts`); on-screen Bluetooth
  heart-rate/oxygen readings; optional encrypted backup; install to home screen.
- Words are matched **on the device** and go to the AI provider only if the
  person taps "Let AI read my words". Guardian answers, ZIP, and contact number
  are **not** sent as analytics events.
- Resources come from public directories and may be out of date — call first or
  dial **211**. Treatment referrals: **SAMHSA National Helpline 1-800-662-4357**
  (free, confidential, 24/7).
- A public **founding Constitution** draft (not yet ratified) proposes that
  ordinary help stays free of tracking or risk scores (`/constitution`).
- Funding/roadmap: `/fund` page; outbound link via `NARCOGUARD_FUNDING_URL`
  (code default `https://gofund.me/e1a0b3f2`). Contact: narcoguard607@gmail.com.

## 4. Four-week content calendar

One educational touch per week per channel. Warm, human, harm-reduction
community voice. No medical claims, no fear-bait, no spam, no invented metrics.

| Week | Theme | X | Email/Community |
|---|---|---|---|
| 1 | Maslow framing — basic needs first | Post A1 | Community post C1 |
| 2 | Find Help + 211 resource literacy | Post A2 | Newsletter blurb N1 |
| 3 | Angel AI + Guardian Stability planner | Post A3 | Community post C2 |
| 4 | Training, Hero certification, Constitution | Post A4 | Outreach email E1 (pilot partners) |

## 5. Pre-approved drafts (human review still required)

### Week 1 — X post A1
> Addiction can flatten everything — food, sleep, safety slide while the drug
> takes the top slot. NarcoGuard is a free demo app that rebuilds from the
> bottom: basic needs first, then safety, connection, stability, goals. A
> planning aid alongside treatment, never instead of it.
> https://narcoguard-pwa.vercel.app

### Week 2 — X post A2
> Need food, a shower, naloxone, a clinic, someone to talk to? NarcoGuard's
> Find Help matches what you type — on your device — to public directories and
> widens the search when nothing is close. Listings change; call first or dial
> 211. Treatment: SAMHSA 1-800-662-4357 (free, confidential, 24/7).
> https://narcoguard-pwa.vercel.app/help

### Week 3 — X post A3
> Angel AI listens first and suggests two or three small next steps — you pick.
> The Guardian Stability planner holds today's needs, sleep, one goal, and
> tomorrow's task. Everything stays in your browser; nothing is tracked.
> https://narcoguard-pwa.vercel.app/angel · https://narcoguard-pwa.vercel.app/stability

### Week 4 — X post A4
> Learn the emergency and CPR steps, take the training, become a certified
> NarcoGuard Hero. The app also carries plain-language Good Samaritan law
> summaries — fear shouldn't cost a life. Demo, not a dispatch service; in an
> emergency, call 911. https://narcoguard-pwa.vercel.app/ar

### Community post C1 (harm-reduction communities, only where self-promo is allowed)
> We built a free, no-login demo around a simple idea: recovery starts with
> food, sleep, and safety — not willpower. NarcoGuard maps needs to real
> resources (211, clinics, naloxone), holds a daily planner in your browser
> local storage, and an AI that listens without storing chats. It's a research
> concept, not a medical device — and the emergency pages still say the only
> line that matters: call 911. Feedback from people with lived experience is
> genuinely wanted: https://narcoguard-pwa.vercel.app

### Outreach email E1 (pilot partners / grant targets from leads.json ICP)

Subject: NarcoGuard — free overdose-harm-reduction demo; supervised pilot proposal

> Hello [name],
>
> I'm writing about NarcoGuard, a free public web app (demo and research
> concept) for overdose prevention and person-led recovery support:
> https://narcoguard-pwa.vercel.app
>
> What it does today: needs-first resource search matched on-device (food,
> shelter, naloxone, treatment), step-by-step emergency and CPR guidance,
> Good Samaritan law summaries, an optional daily stability planner stored
> only in the browser, and an AI listener that suggests small next steps.
> What it is not: a medical device, a dispatch service, or a treatment
> program — it does not contact 911, dispatch responders, or deliver
> naloxone. In an immediate emergency, call 911.
>
> We are exploring a small, supervised pilot with public-health and
> harm-reduction partners and would value 20 minutes to hear whether this is
> useful or where it misses. Unknowns we state openly: no measured field
> outcomes yet, resource listings require verification, and any future
> alerting features would be opt-in, revocable, and separately reviewed.
>
> Treatment referrals we always point to: SAMHSA National Helpline
> 1-800-662-4357 (free, confidential, 24/7).
>
> With respect,
> The NarcoGuard project — narcoguard607@gmail.com

### Press pitch angle (for `/press/pitch` generation, not yet sent)
Angle: *"What if basic needs came first?"* — a Maslow-grounded, privacy-first
take on overdose-harm-reduction tooling, led by a public constitution draft.
Factual public-health tone; no outcome claims; why-now = free, no-login demo +
open governance experiment.

## 6. Messaging guardrails (checked before any send)

- ✅ Always: "demo and research concept", "not a medical device / dispatch
  service", "call 911 in an emergency" on any overdose-safety content.
- ✅ SAMHSA 1-800-662-4357 and 211 mentioned where resources are discussed.
- ❌ Never: claims it detects/reverses overdose, saved lives, clinical
  validation, partnerships, or metrics. No fear-bait. No "guaranteed recovery".
- ❌ Never: mass-DM or scraped-list blasting; outreach only to the curated
  mission-aligned leads in `leads.json`; one follow-up max, respect no-replies.
- ❌ No medical advice; copy stays product-descriptive + referral signposting.

## 7. Credentials checklist for Steve

For Chatty to actually run this campaign end-to-end:

1. **AI generation** (drafts/briefs): any one of `NVIDIA_API_KEY`,
   `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `XAI_API_KEY`, `MISTRAL_API_KEY`,
   `DEEPSEEK_API_KEY`.
2. **Outbound email**: `SENDGRID_API_KEY` + verified sender
   (`SENDGRID_FROM_EMAIL`), or `RESEND_API_KEY` + verified domain
   (`RESEND_FROM_EMAIL`). Chatty does not currently speak Brevo — either
   provision one of these, or add a Brevo sender as a small follow-up. **Brevo
   approval step when that lands: allowlist server IP `43.106.103.81`** so
   Brevo accepts SMTP/API sends from the host.
3. **X/Twitter**: the 5 X credentials stored via `configure_x_keys.py`
   (`secure-key-setup` branch). Keep using `publish_approved_x.py` —
   human-typed `PUBLISH` — for this sensitive topic. Chatty's
   `TWITTER_API_KEY`-gated autopost stays off for narco.
4. **n8n**: `N8N_BASE_URL` + `N8N_API_KEY` (+ optional `N8N_PROJECT_ID`) to
   activate the cadence workflow remotely.
5. **State persistence**: `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` with a
   `chatty_state` table (id text, payload jsonb) so campaign state survives
   restarts.
6. **Product links**: `NARCOGUARD_URL` (default
   https://narcoguard-pwa.vercel.app), `NARCOGUARD_FUNDING_URL` (or
   `GOFUNDME_URL`).
7. **Ops notifications**: `AUTOMATION_NOTIFY_EMAIL` (or `ADMIN_EMAIL`) and
   `FUNDING_NOTIFY_EMAIL`.

## 8. Runbook (after credentials are present)

```bash
# 1. Register campaigns (payloads in §2)
# 2. Activate the cadence workflow in n8n
curl -X POST "$CHATTY/api/n8n/workflows/activate" \
  -H 'Content-Type: application/json' \
  -d '{"name": "NarcoGuard Awareness Cadence"}'

# 3. Draft (not send) the funding/pilot package
curl -X POST "$CHATTY/api/funding/run" -H 'Content-Type: application/json' \
  -d '{"send_now": false, "notify_email": "$ADMIN_EMAIL"}'

# 4. Keep autonomy OFF until a human approves Week 1 copy; then:
curl -X POST "$CHATTY/api/autonomy/start"
```

## 9. What she will do once live

Weekly: pull the next cadence slot → assemble the pre-approved draft → queue
for human approval → on approval, post via the manual X flow / send via
SendGrid-Resend → log to collab feed + Supabase. Monthly: regenerate one
pilot-partner funding package (`send_now: false`) for review. Continuously:
append `NARCOGUARD_URL` + funding link to outbound content, track responses in
the dashboard, and surface pending integrations in `/api/integrations/status`.
