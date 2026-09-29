# KARNA — Technical Architecture

**KARNA** (Knowledge-Augmented Response & Neural Assistance) is an incident-response intelligence system built around a durable feedback loop: **Incident → Memory → Learning → Improved Recommendation**. This architecture is deliberately modular, demo-safe, and production-shaped without adding enterprise scope that the MVP does not need.

## 1. High-Level System Architecture

```text
Engineer
  ↓
Next.js Frontend
  ↓ HTTPS / JSON
FastAPI Backend API
  ↓
Application Services ─── Groq LLM
  ↓
Abstract Memory Service
  ↓
SQLite (memory, outcomes, corrections, analytics)
```

| Layer | Responsibility |
|---|---|
| User | Supplies incident context; validates, corrects, and closes the learning loop. |
| Frontend | Provides dashboard, analysis, evidence inspection, feedback, and analytics experiences. It never decides recommendation ranking. |
| Backend API | Validates requests, coordinates application services, returns UI-ready data, and enforces the Memory On/Off mode. |
| Application services | Analyze incidents, retrieve and rank memories, generate grounded recommendations, capture feedback, and aggregate analytics. |
| Memory service | Defines a stable contract for storing, recalling, scoring, and explaining operational memories; hides SQLite or future Hindsight implementation details. |
| SQLite | Durable source of truth for incidents, recommendations, outcomes, corrections, materialized memory records, and demo analytics. |
| Groq | Generates concise, evidence-grounded diagnosis and recommendation language. It is not the system of record or ranking authority. |

The recommendation path is intentionally split into deterministic evidence/ranking and LLM presentation. This keeps recommendation behavior inspectable, makes learning visible, and prevents a model-only answer from being mistaken for memory.

## 2. Complete Folder Structure

```text
karna/
├── frontend/
│   ├── app/
│   │   ├── dashboard/
│   │   ├── incident/
│   │   ├── memory/
│   │   ├── analytics/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── ui/
│   │   ├── incident/
│   │   ├── memory/
│   │   ├── analytics/
│   │   └── shared/
│   ├── lib/
│   │   ├── api/
│   │   ├── formatters/
│   │   └── constants/
│   ├── hooks/
│   ├── types/
│   ├── public/
│   └── tests/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   └── dependencies/
│   │   ├── core/
│   │   ├── domain/
│   │   │   ├── incidents/
│   │   │   ├── recommendations/
│   │   │   ├── learning/
│   │   │   ├── memory/
│   │   │   └── analytics/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── memory/
│   │   │   ├── providers/
│   │   │   └── ranking/
│   │   ├── llm/
│   │   ├── db/
│   │   ├── schemas/
│   │   └── main.py
│   ├── data/
│   │   ├── seed/
│   │   └── karna.sqlite
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── fixtures/
├── docs/
│   ├── PRD.md
│   ├── TECHNICAL_ARCHITECTURE.md
│   ├── demo-script.md
│   └── decisions/
├── scripts/
│   ├── seed-demo-data/
│   └── validate-demo/
├── .env.example
├── README.md
└── compose.yaml
```

| Area | Purpose |
|---|---|
| `frontend/app` | Route-level pages and layouts for the four product surfaces. |
| `frontend/components` | Reusable shadcn/ui primitives and domain-specific visual components. |
| `frontend/lib`, `hooks`, `types` | Typed API client, presentation utilities, UI state, and shared contracts. |
| `backend/api` | Thin HTTP boundary and route composition. |
| `backend/domain` | Business concepts and use cases, organized by product capability rather than framework. |
| `backend/services` | Orchestrates multi-module workflows such as analyze-and-recommend or record-feedback. |
| `backend/repositories` | Persistence access boundary; prevents SQLite details from leaking into business logic. |
| `backend/memory` | Memory contract, provider implementations, retrieval, scoring, and explainability logic. |
| `backend/llm` | Groq adapter, grounded prompt construction, response validation, and fallback behavior. |
| `backend/db` | Connection lifecycle, migrations/versioning strategy, and seed loading. |
| `backend/schemas` | Transport/request-response contracts, kept distinct from internal domain objects. |
| `data/seed` | Versioned synthetic incident source data and controlled demo scenarios. |
| `tests` | Deterministic unit, workflow integration, and demo-regression coverage. |
| `docs/decisions` | Lightweight architecture decisions, including memory-provider and scoring changes. |

## 3. Backend Architecture

### Modules and responsibilities

| Module | Responsibilities | Collaborates with |
|---|---|---|
| Incident | Creates and retrieves incident records; normalizes title, description, category, and service context. | Memory, Recommendation, repositories |
| Memory | Stores canonical incident, outcome, correction, and recommendation memories; retrieves candidate evidence. | Ranking, repositories, Hindsight provider |
| Recommendation | Builds candidate fixes, scores them, requests grounded narrative generation, and persists recommendation snapshots. | Incident, Memory, LLM, Learning |
| Learning | Captures final applied fixes, success/failure, and corrections; updates memory evidence signals. | Recommendation, Memory, Analytics |
| Analytics | Computes or reads aggregate learning and utilization metrics. | Learning, repositories |
| LLM | Produces structured narrative only from supplied evidence; handles unavailable model fallback. | Recommendation |

### Interactions

`AnalysisService` receives a new incident. If Memory Mode is enabled, it asks the memory service for similar incident records and associated outcome/correction memories. `RecommendationService` groups those records into candidate fixes, applies ranking rules, and gives the top evidence bundle to the LLM adapter for an explainable presentation. The resulting recommendation and evidence snapshot are persisted.

`LearningService` receives outcome or correction events. It validates the link to the incident/recommendation, writes the feedback record, emits/upserts relevant memory records, and invalidates or refreshes aggregates. The next analysis retrieves this new evidence through the same memory contract.

## 4. Database Design

SQLite is the durable MVP source of truth. IDs should be stable, timestamps retained for all auditable learning events, and mutable current-state records should not overwrite feedback history.

### Incidents

- **Purpose:** Canonical record of a submitted or seeded incident.
- **Fields:** incident ID, external/display reference, title, description, normalized category, optional service/severity, source type (seeded or user), created/updated timestamps.
- **Relationships:** One incident has many recommendations, outcomes, corrections, and memory records.
- **Indexes:** created timestamp; category; normalized title/context lookup; optional service plus category.

### Recommendations

- **Purpose:** Immutable snapshot of KARNA’s proposed root cause/fix at a specific analysis time.
- **Fields:** recommendation ID, incident ID, memory mode, proposed root cause, proposed fix, rank, confidence, generated explanation, evidence summary, model/provider metadata, timestamp.
- **Relationships:** Belongs to an incident; has many linked evidence records and may have many outcomes.
- **Indexes:** incident ID plus timestamp; incident ID plus rank; memory-mode filter.

### Outcomes

- **Purpose:** Captures whether the final applied fix restored service or failed.
- **Fields:** outcome ID, incident ID, optional recommendation ID, final fix applied, status (success/failure), optional notes, recorded timestamp.
- **Relationships:** Belongs to incident and optionally recommendation; creates or enriches outcome memory.
- **Indexes:** incident ID; recommendation ID; final fix plus status; recorded timestamp.

### Corrections

- **Purpose:** Preserves engineer-authored corrections to root cause and/or recommendation.
- **Fields:** correction ID, incident ID, optional recommendation ID, prior root cause/fix, corrected root cause/fix, explanation, correction type, timestamp.
- **Relationships:** Belongs to incident and optionally recommendation; creates correction memory.
- **Indexes:** incident ID; corrected root cause; corrected fix; timestamp.

### Memory Records

- **Purpose:** Provider-neutral, retrievable representation of operational experience and its provenance.
- **Fields:** memory ID, memory type, source incident ID, optional source recommendation/outcome/correction ID, searchable narrative/context, root cause, fix, embedding/reference key where available, evidence quality, active/superseded state, created/updated timestamps.
- **Relationships:** References source entities; can participate in many recommendation-evidence links.
- **Indexes:** memory type; source incident ID; root cause; fix; active state; provider retrieval key. A vector index is provider-specific and intentionally outside the relational design.

### Recommendation Evidence

- **Purpose:** Preserves which memories influenced a recommendation, enabling an exact Memory Inspector view even after later learning.
- **Fields:** recommendation ID, memory ID, relevance/similarity score, outcome-weight score, correction-weight score, total contribution score, rank, selection rationale.
- **Relationships:** Join between recommendations and memory records.
- **Indexes:** recommendation ID plus rank; memory ID.

### Analytics Snapshots / Aggregates

- **Purpose:** Efficient dashboard metrics and reproducible demo views without recomputing all history on every request.
- **Fields:** metric key, dimension/category, value, calculation period, last-calculated timestamp; optionally daily learning/event rollups.
- **Relationships:** Derived from incidents, outcomes, corrections, and recommendations; not authoritative for source data.
- **Indexes:** metric key plus dimension; calculation timestamp.

## 5. Memory Architecture

### Memory types

| Type | Contents | Influence |
|---|---|---|
| Incident memory | Symptoms, title, description, category, affected context, root-cause resolution where known | Finds comparable cases and supplies context. |
| Outcome memory | Final fix applied and success/failure result | Raises proven fixes; warns against failed approaches. |
| Correction memory | Engineer correction and its prior incorrect assumption | Prioritizes human-validated explanations for matching symptoms. |
| Recommendation memory | Recommendation snapshot, confidence, and evidence at decision time | Provides traceability and enables recommendation-quality analysis. |

### Store and recall lifecycle

On incident creation, KARNA stores normalized incident context. Once guidance is produced, it stores a recommendation snapshot and exact linked evidence. When a user records an outcome or correction, it writes an immutable feedback event and produces/upserts derived memory records with provenance back to the event.

At analysis time, a provider retrieves candidate incident memories using semantic similarity when available, with category/key-term fallback for SQLite-only operation. The system expands candidates with related outcomes and corrections, removes stale or duplicate evidence, groups fixes and root causes, and passes the evidence to the ranker. Memory mode is a hard switch: off means no historical retrieval or outcome-weighted ranking.

### Hindsight compatibility

All product services depend on an `AbstractMemoryService` contract: write memory, recall candidates, enrich evidence, explain contribution, and health/capability reporting. A `SQLiteMemoryProvider` fulfills this contract for the MVP. A future `HindsightMemoryProvider` implements the identical contract, maps stable KARNA source IDs to Hindsight references, and returns normalized candidate/evidence objects. Provider choice must be configuration-driven; recommendation, learning, and frontend behavior must remain unchanged.

## 6. Recommendation Engine

```text
New incident
  → normalize context
  → recall similar incidents (Memory On only)
  → enrich with outcomes and corrections
  → group candidate root causes and fixes
  → rank candidates deterministically
  → generate grounded recommendation narrative
  → persist recommendation + evidence
  → display evidence and confidence
```

### Ranking strategy

Candidate fix score combines: relevance of supporting incidents, count of successful outcomes, success rate with minimum-evidence handling, failure penalty, validated correction boost, recency/active-state adjustment, and evidence diversity. Failed fixes remain visible in the inspector as negative evidence; they should not silently disappear. A correction may initially receive a substantial but bounded boost; repeated success validates it further.

The MVP should favor transparent bounded scoring over opaque model-derived scoring. The API returns the components used to create a ranking, not just its final position.

### Confidence scoring

Confidence is a calibrated evidence signal, not a claim of truth. It is derived from candidate score, number of independent supporting incidents, outcome consistency, correction support, and match quality. Suggested labels are Low, Medium, and High, accompanied by a reason such as “High: 7 successful outcomes across 5 similar incidents.” Low confidence is mandatory when memory is absent, sparse, conflicting, or weakly similar.

The Groq response may explain a result but may not increase the deterministic confidence score. If generation is unavailable, the backend returns the ranked structured evidence and a template-based explanation.

## 7. Learning Engine

```text
Engineer records outcome or correction
  → validate linked incident/recommendation
  → append durable feedback event
  → create/update outcome or correction memory
  → refresh aggregate learning signals
  → future recall includes new evidence
  → future ranking changes transparently
```

### Outcome flow

The engineer selects Success or Failure and records the final fix applied. The system treats the applied action—not merely the originally recommended action—as the learning signal. If a different action succeeded, it becomes positive evidence for that action and the original recommendation remains traceable.

### Correction flow

The engineer corrects a root cause, a fix, or both. KARNA preserves the prior recommendation, stores the corrected assertion with explanation and context, and marks the correction as human-authored evidence. Future similar incidents receive an appropriate correction boost. A correction is not assumed universally correct: similarity, later outcomes, and contradictory feedback still govern its influence.

### Learning invariants

- Feedback is append-only and attributable to an incident.
- Past recommendation snapshots remain reproducible.
- Outcome success and failure both influence future ranking.
- Corrections are distinguishable from model-generated assertions.
- The system can explain exactly what changed between two recommendation runs.

## 8. API Architecture

The API is versioned under a consistent prefix (for example, `/api/v1`) and returns typed JSON envelopes with request correlation IDs and user-safe error messages. No authentication scope is included in the MVP.

| Endpoint | Purpose | Request | Response |
|---|---|---|---|
| `POST /incidents/analyze` | Create/accept an incident and return a recommendation. | Title, description, optional category/context, Memory On/Off. | Incident reference, ranked causes/fixes, confidence, explanation, evidence summary, inspector reference. |
| `POST /incidents/{id}/outcomes` | Record final action and success/failure. | Optional recommendation reference, final fix, status, notes. | Stored outcome, affected learning summary, updated metric cues. |
| `POST /incidents/{id}/corrections` | Record an engineer correction. | Optional recommendation reference, corrected cause/fix, explanation. | Stored correction, memory update summary, expected future influence. |
| `GET /incidents/{id}` | Retrieve incident history and its analysis timeline. | Incident ID. | Incident, recommendations, outcomes, corrections. |
| `GET /recommendations/{id}/memory-inspector` | Return exact evidence used for one recommendation. | Recommendation ID. | Recalled incidents/memories, similarity and contribution scores, outcome history, ranking explanation. |
| `GET /memory/inspect` | Search/browse active memories for diagnostic/demo use. | Optional category, type, query, pagination. | Memory summaries, source provenance, lifecycle state. |
| `GET /analytics/overview` | Supply dashboard KPIs and chart series. | Optional time/category filters. | Totals, success/failure leaderboards, growth/utilization metrics. |
| `GET /health` | Report application, database, memory provider, and LLM availability. | None. | Component health and active provider. |

The analysis response deliberately includes a compact evidence summary; the full inspector data remains a separate endpoint to keep the main experience fast and readable.

## 9. Frontend Architecture

### Dashboard

The landing dashboard presents the product promise before navigation: total learned incidents, corrections captured, memory utilization, and most-proven fixes. It links directly to Analyze Incident and Analytics. Components include KPI cards, learning-growth sparkline, successful/failed fix lists, and a recent-learning feed.

### Incident Analysis

This is the main work surface. A left/top input panel captures title and description, with a conspicuous Memory On/Off toggle. The result area displays likely root cause, recommendation, confidence, outcome history, and evidence count. A right/bottom evidence rail previews recalled incidents and opens the inspector. An action panel records final outcome or correction after the engineer acts.

### Memory Inspector

The inspector is a route or side panel driven by a recommendation ID. It renders the immutable evidence snapshot from the analysis run, rather than re-running retrieval. Its component hierarchy includes a recommendation summary, ranking rationale, memory cards/table, outcome badges, correction callouts, and warning/contradiction states.

### Learning Analytics

Analytics uses overview data only; it does not duplicate decision logic in the browser. It renders KPI cards, learning growth, memory utilization, successful/failed fix rankings, correction volume, and category breakdowns. Filters should remain limited to time window and incident category for MVP clarity.

### Data flow and interaction model

Typed frontend API functions call the backend. Route/page state owns submitted incident and latest recommendation ID; the inspector reads that ID to retrieve stable evidence. Optimistic UI is appropriate for low-risk feedback acknowledgement, but dashboard/recommendation data should refresh from server-confirmed persistence. Each mode and confidence state must be visually explicit, including a meaningful empty/low-evidence state.

## 10. Memory Inspector Design

Memory Inspector should open from “View evidence” directly beside the recommendation. It must be visually distinctive because it is the clearest proof of KARNA’s central claim.

```text
┌──────────────── Recommendation Evidence ────────────────┐
│ Recommended: Patch connection leak     Confidence: High  │
│ Why: 7 successes, 0 failures across similar incidents    │
├──────────────── Ranking rationale ───────────────────────┤
│ 1. Patch leak       92 score  | 7 success | 0 failure    │
│ 2. Restart pool     41 score  | 2 success | 5 failure    │
├──────────────── Recalled memories ───────────────────────┤
│ INC-034 · Similarity 92% · Connection Leak               │
│ Fix: Patch Leak · Outcome: Success · [view details]      │
│ INC-017 · Similarity 88% · Connection Leak               │
│ Fix: Restart Pool · Outcome: Failure · [view details]    │
├──────────────── Learning signal ─────────────────────────┤
│ Engineer correction: “Connection Leak” superseded        │
│ “Database Overload” in INC-034                            │
└──────────────────────────────────────────────────────────┘
```

The top section answers “what should I do?” The ranking section answers “why this over alternatives?” The memory list answers “what did KARNA remember?” Each memory card shows incident reference, similarity score, root cause, historical fix, outcome, correction status, and contribution rationale. Scores use text and labels alongside color; failure evidence is prominent, not hidden. A compact compare mode can show Memory Off’s generic answer beside Memory On’s evidence-backed one for the demo.

## 11. Analytics Dashboard

| Metric | Definition | Product use |
|---|---|---|
| Total incidents | Count of stored incident records | Shows memory corpus growth. |
| Total corrections | Count of engineer correction events | Shows active organizational teaching. |
| Most successful fixes | Fixes ranked by successful outcomes, with sample size | Identifies proven operational actions. |
| Most failed fixes | Fixes ranked by failures, with sample size | Surfaces actions to avoid or investigate. |
| Learning growth | New outcome/correction-backed memories over time | Makes compounding knowledge visible. |
| Memory utilization | Analyses with at least one relevant recalled memory divided by total analyses | Shows whether memory participates in decisions. |
| Recommendation success rate | Successful recorded outcomes divided by recorded outcomes | Tracks practical utility, with sufficient-sample caveat. |

The primary layout is a KPI row, a learning-growth trend, two ranked fix panels (proven versus failed), and a memory-utilization panel. Every metric needs its definition available in a tooltip or detail state to avoid misleading interpretation.

## 12. Demo Dataset Architecture

The seed dataset contains 120 synthetic incidents distributed across six categories: Database Issues, Memory Leaks, CrashLoopBackOff, Config Errors, DNS Failures, and High Latency. Each category should contain approximately 20 incidents, with varied titles, symptoms, services, severities, likely causes, actions, and dated outcomes.

Every seed incident includes canonical incident context, resolved root cause, one or more candidate/recommended fixes, final action applied, outcome, and a limited number of corrections. The data must include both repeats and believable variation, so retrieval is not based on identical text. It should also include controlled contradictory evidence—such as a restart that occasionally works but fails often—so outcome-aware ranking is visible.

The database-timeout scenario is a reserved demo cluster. Before correction, it contains enough historical evidence to distinguish generic and memory-backed answers. A scripted correction introduces “Connection Leak” and a successful “Patch Leak” outcome. Re-analyzing a deliberately similar incident then shows the corrected cause and fix rise in ranking. Seed data must be versioned, resettable, and deterministic, ensuring a reliable demo reset.

## 13. Development Order

### Phase A — Foundation and demo data

Establish frontend/backend shells, SQLite persistence boundary, domain contracts, and the 120-incident deterministic seed dataset. Build the local reset/health path first. If time is constrained, keep categories but reduce data variation only after preserving the database-timeout demonstration cluster.

### Phase B — The memory-to-recommendation vertical slice

Build incident submission, Memory On/Off behavior, SQLite fallback retrieval, deterministic candidate ranking, and a plain structured recommendation. Do not begin with LLM polish. This phase must independently prove generic versus memory-backed output.

### Phase C — Learning loop and inspector

Add outcome capture, correction capture, memory updates, immutable evidence snapshots, and Memory Inspector. This is the highest-value phase: it enables the before/after proof. If time runs short, prioritize correction plus repeat analysis over broad analytics.

### Phase D — LLM narrative and product polish

Integrate Groq as a grounded narrative layer, add confidence/explanation UX, loading/error states, and dashboard overview metrics. Retain deterministic fallback outputs for reliability.

### Phase E — Analytics, validation, and presentation

Finish analytics, test the four-scene demo after a reset, calibrate seed-data ranking, and prepare a concise demo script. Stretch items such as rich filters, follow-up chat, or Hindsight provider swap belong only after the required story is stable.

## 14. Risk Analysis

| Risk type | Risk | Mitigation |
|---|---|---|
| Technical | Groq latency/outage disrupts demo | Keep deterministic evidence/ranking response and template narrative fallback. |
| Technical | Retrieval quality is weak with lightweight SQLite fallback | Use normalized categories/keywords, curated varied seed data, and provider abstraction for later semantic retrieval. |
| Architecture | Memory-provider details leak into product services | Enforce the abstract memory contract and normalized evidence objects from the start. |
| Architecture | Analytics diverge from source history | Compute from authoritative events or refresh aggregates after every learning event; label aggregates as derived. |
| Memory | Sparse, contradictory, or stale evidence creates false confidence | Apply sample-aware scoring, failure penalties, recency/active-state signals, conflict flags, and low-confidence states. |
| Memory | Corrections overfit a single incident | Give corrections bounded initial influence and validate with later outcomes/relevance. |
| Demo | Judges see an AI chatbot rather than learning | Put Memory On/Off, Inspector, correction action, and changed repeat recommendation on-screen. |
| Demo | Stateful demo starts in wrong condition | Provide a deterministic reset and rehearse the entire flow from a clean seed. |

## 15. Hackathon Winning Strategy

KARNA should be presented as a learning system, not a search interface. Traditional RAG retrieves relevant text; it does not inherently know which fixes restored service, which failed, or how engineer corrections should change future decisions. KARNA’s memory layer preserves all three signals and its recommendation engine treats them as ranking evidence.

The winning sequence is visual and causal: first show an incident with Memory Off and generic guidance; then enable memory and show historical cases, outcomes, and a specific proven fix; capture a human correction; and finally submit the same incident again to show a changed, evidence-cited recommendation. Open Memory Inspector at least once to expose exact recalled incident IDs, similarity, outcomes, and ranking contributions.

The judge should leave with one simple conclusion: every incident makes KARNA more useful for the next one. The product earns innovation through outcome-aware operational memory, technical depth through provider abstraction and explainable ranking, user trust through inspection, and real-world value through less repeated investigation and faster restoration.
