# KARNA — Product Requirements Document

**Product:** KARNA (Knowledge-Augmented Response & Neural Assistance)  
**Tagline:** An AI Incident Response Agent that remembers, learns, and improves from every incident.  
**Stage:** Hackathon MVP  
**Primary users:** SREs, DevOps engineers, platform engineers, and cloud operations teams

## 1. Executive Summary

KARNA is a memory-centric AI incident response agent for engineering teams. It turns completed incidents, attempted fixes, outcomes, and engineer corrections into reusable operational knowledge. When a new incident occurs, KARNA recalls the most relevant prior experience, explains the evidence behind its recommendation, and learns from the engineer’s final outcome.

Unlike a conventional chatbot or retrieval tool, KARNA makes the learning loop visible: a recommendation is tied to recalled memories, its result changes future confidence, and explicit corrections supersede weaker historical assumptions. The MVP focuses on one complete loop—analyze, recall, recommend, correct, learn, and demonstrate improvement.

## 2. Product Vision

Make every incident permanently useful. KARNA should become the operational memory an engineering organization can rely on during stressful, time-sensitive incidents.

## 3. Mission Statement

Help engineers resolve recurring incidents faster by transforming historical operational experience into transparent, continuously improving guidance.

## 4. Problem Statement

Operational knowledge is fragmented across tickets, chat threads, runbooks, documents, and individual memory. During an incident, engineers must rediscover context under pressure. This causes repeated investigations, reuse of failed fixes, dependency on senior staff, inconsistent responses, and longer MTTR.

Existing AI assistants can summarize or suggest actions, but generally do not preserve the outcome of their advice in a form that meaningfully changes future recommendations. The missing product is a trusted memory-and-learning layer for incident response.

## 5. Why This Problem Matters

Incidents directly affect reliability, revenue, customer trust, and engineer wellbeing. Recurring issues are especially wasteful because the organization often already paid the cost of learning the answer once. A system that reliably recalls proven responses—and warns against failed ones—compounds the value of every resolved incident while helping newer responders operate with historical context.

## 6. Market Opportunity

Reliability engineering teams increasingly operate complex cloud systems with limited experienced staff. Observability, incident-management, knowledge-management, and AI-assistant tools are each established categories, but their operational learning loops remain fragmented. KARNA occupies the intersection: it converts incident history into decision support rather than merely storing or searching it. The initial wedge is small teams that need faster, more consistent incident response; the long-term opportunity is an organizational intelligence layer across engineering operations.

## 7. User Personas

| Persona | Needs | Pain points | KARNA value |
|---|---|---|---|
| SRE / on-call engineer | Restore service quickly and safely | Time pressure; unknown history | Evidence-backed, ranked resolution guidance |
| DevOps / platform engineer | Diagnose infrastructure patterns | Repeated issues across services | Reusable fixes and outcomes across incidents |
| New engineer | Act confidently without tribal knowledge | Senior engineers are unavailable | Context, rationale, and historical precedent |
| Incident commander | Coordinate a reliable response | Uneven quality of recommendations | Transparent evidence and decision trail |
| Engineering manager | Improve operational maturity | Cannot see repeated learning failures | Learning, correction, and fix-success analytics |

## 8. User Journey Maps

### A. On-call incident response

1. Engineer receives an alert and opens KARNA.
2. They enter an incident title and concise description.
3. KARNA retrieves similar past incidents and displays root causes, attempted fixes, outcomes, and similarity scores.
4. KARNA proposes a ranked resolution with a confidence score and plain-language explanation.
5. Engineer inspects the evidence, follows or adapts the recommendation, and records whether it worked.
6. KARNA persists the outcome and updates future evidence/confidence.

### B. Correction and learning

1. Engineer sees an inaccurate root cause or recommendation.
2. They correct the root cause and/or proposed fix.
3. KARNA stores the correction as a high-priority learning event linked to the incident context.
4. On a subsequent similar incident, KARNA elevates the corrected answer and explains that it reflects a prior correction.

### C. Operational review

1. Manager opens Analytics.
2. They review total incidents, corrections, successful and failed fixes, and memory utilization.
3. They identify recurring failure patterns and areas where the team is building confidence.

## 9. User Stories

- As an on-call engineer, I want to enter an incident and see similar historical cases so I can avoid repeating investigation work.
- As an engineer, I want recommendations to include evidence and confidence so I can judge whether they are safe to act on.
- As an engineer, I want to record whether a fix worked or failed so future responders benefit from the result.
- As an engineer, I want to correct an incorrect root cause or fix so the system does not repeat the same mistake.
- As a new responder, I want to inspect recalled memories and historical outcomes so I can understand the recommendation.
- As a manager, I want learning analytics so I can measure whether incident knowledge is becoming more useful.
- As a demo viewer, I want to see a materially different recommendation before and after memory learning so I can verify KARNA is not static RAG.

## 10. Functional Requirements

### FR-1: Incident analysis

The user can submit an incident title and description. KARNA returns possible root causes, ranked recommended fixes, confidence, and supporting evidence. The result clearly indicates whether memory was used.

### FR-2: Memory recall

KARNA retrieves relevant historical incident memories, including the incident context, root cause, fixes attempted, outcomes, and corrections. Recalled memories are ranked by relevance and quality of evidence.

### FR-3: Recommendation generation

KARNA produces a concise recommendation synthesized from recalled memory. The recommendation includes: suggested action, likely root cause, confidence score, reason for selection, number/quality of supporting memories, and an explicit warning where past fixes failed.

### FR-4: Outcome tracking

For each recommendation or chosen action, users can record **worked** or **failed**, optionally adding notes. The record becomes durable memory and affects future recommendation ranking.

### FR-5: Correction learning

Users can correct the root cause and/or recommendation. KARNA stores the correction with its context and prioritizes it over contradicted, low-quality historical evidence for similar future incidents.

### FR-6: Memory Inspector

KARNA exposes the evidence behind a result: recalled memories, similarity/relevance score, prior outcomes, corrections, and contribution to the recommendation. It must make memory behavior inspectable rather than implicit.

### FR-7: Memory mode control

The analysis experience provides a demo-safe Memory On/Off control. With memory off, KARNA returns a generic, context-only recommendation. With memory on, it uses stored experience and labels the evidence used.

### FR-8: Analytics dashboard

The dashboard displays total incidents, total corrections, successful and failed fixes, most successful fixes, most failed fixes, learning growth over time, and memory utilization (for example, percentage of analyses supported by recalled memory).

### FR-9: Seeded demo experience

The MVP includes representative historical incidents and a repeatable database-timeout scenario so the full learning loop can be demonstrated reliably.

### Outcome Learning System

KARNA is not a store of past incidents; it is an outcome-aware operational learning system. For every resolved incident, KARNA retains the incident context, diagnosed root cause, recommended fix, final fix actually applied, and outcome—**Success** or **Failure**. These are durable signals that affect the quality and ordering of later recommendations.

When a new incident resembles prior experiences, KARNA weighs both semantic relevance and demonstrated effectiveness. A highly similar incident is useful, but a fix repeatedly proven to work is more valuable than an unvalidated or repeatedly failed fix. For example, if Fix A worked eight times, Fix B worked twice, and Fix C failed five times, KARNA should favor Fix A, treat Fix B as weaker supporting evidence, and either de-prioritize Fix C or surface it as a warning. The Memory Inspector must expose these signals so the ranking is understandable.

Outcome learning improves recommendation quality by grounding guidance in operational results rather than plausible text alone. It reduces MTTR by directing responders toward already validated actions and away from costly, known-bad paths. This is a fundamental differentiator from traditional retrieval-augmented generation: RAG can retrieve a document describing a fix, while KARNA learns whether that fix actually restored service in comparable situations.

**Outcome workflow:**

1. KARNA proposes one or more fixes and records the evidence used.
2. The engineer applies a fix and records the final action taken.
3. The engineer marks the result as Success or Failure, with an optional observation.
4. KARNA adds the result to organizational memory and updates the evidence available to future recommendation rankings.

### Engineer Correction Learning

Engineers must be able to correct KARNA’s understanding whenever its diagnosis or guidance is incomplete or wrong. A correction is not merely a comment; it is a first-class organizational learning event, retained with the incident context and used in future recall and ranking.

For example, KARNA may identify **Database Overload** as the likely root cause for connection-pool exhaustion. An engineer can correct it to **Connection Leak**, record the relevant fix, and confirm the result. On future incidents with similar symptoms, KARNA should increase the prominence and confidence of the corrected explanation—especially when later outcomes validate it—while retaining the original assessment as historical context rather than concealing it.

Human feedback is essential because operational environments change, incident descriptions can be ambiguous, and the engineers resolving the incident possess situational knowledge unavailable to a model. Each correction helps the organization replace tribal knowledge with durable, inspectable evidence. Over time, this creates a living memory in which advice becomes more accurate, more specific to the team’s environment, and less dependent on any one senior engineer.

**Correction workflow:**

1. An engineer reviews KARNA’s root-cause hypothesis and recommendation.
2. They edit the incorrect root cause, proposed fix, or both, and optionally describe why.
3. KARNA stores the correction against the incident and marks it as corrective evidence.
4. The engineer records the final outcome after applying the corrected action.
5. On a later similar incident, KARNA recalls the correction, ranks the corrected explanation appropriately, and states that the recommendation reflects prior engineer feedback.

### Memory Inspector

Memory Inspector is KARNA’s transparency layer and one of its primary trust features. For every memory-backed recommendation, users can inspect exactly which experiences influenced it, rather than accepting a black-box answer. The inspector must show recalled incident identifiers and summaries, similarity scores, root causes, fixes, historical outcomes, correction markers, and the reason each memory affected the final ranking.

An illustrative inspector view may show:

| Recalled incident | Similarity | Root cause | Fix | Outcome |
|---|---:|---|---|---|
| INC-034 | 92% | Connection Leak | Patch Leak | Success |
| INC-017 | 88% | Connection Leak | Restart Pool | Failure |

It should then make recommendation ranking legible: **Patch Leak** has 7 successes and 0 failures, whereas **Restart Pool** has 2 successes and 5 failures. A responder can therefore see why the first is recommended and why the second is treated cautiously. Similarity alone must not be represented as proof; the inspector distinguishes relevance from outcome strength and flags conflicting evidence.

By exposing this chain from recalled memory to outcome-weighted recommendation, Memory Inspector proves that KARNA is genuinely memory-driven. It provides users and judges with a concrete answer to “Why did KARNA say this?” and makes it clear that the system is more than a chatbot with a persuasive explanation.

### Memory Impact Demonstration

The core hackathon demonstration must make the causal chain visible: **Memory → Learning → Improvement**. It uses the same recognizable incident—**“Database Connection Pool Exhausted”**—across four deliberate states.

1. **Scenario A: Memory Off.** The user submits the incident with memory disabled. KARNA gives cautious, generic troubleshooting guidance such as checking pool limits, database connectivity, and query load. It has no organizational evidence to prefer a specific fix.
2. **Scenario B: Memory On.** The user submits the identical incident with memory enabled. KARNA recalls comparable historical incidents, shows their outcomes, recommends the most successful fix, and reports confidence derived from relevance and outcome history.
3. **Scenario C: Engineer Correction.** The engineer corrects KARNA’s root cause, for example from Database Overload to Connection Leak, records the proper resolution, and stores a successful outcome.
4. **Scenario D: Same Incident Again.** KARNA analyzes the same or similar incident. It now recalls the correction, elevates the corrected explanation and fix, and explains the improved recommendation using the new evidence.

The presentation should avoid hidden state changes or narration-only claims. Judges must be able to see the recalled memories, the recorded correction, and the changed follow-up recommendation in the UI. This contrast is the central product story: without memory KARNA is generic; with memory it is contextual; after feedback it is demonstrably better.

### Why KARNA Is Different From Traditional RAG

Traditional RAG retrieves relevant documents or passages and uses them as context for a generated answer. It is valuable for discovery, but retrieval by itself does not reliably track whether an action worked, recognize that a recommendation failed repeatedly, or modify future behavior after a human correction.

KARNA uses retrieval as one component of a broader learning system. It stores operational memory, records the result of applied fixes, learns from engineer corrections, and uses those signals to improve recommendation ranking over time. Its value is therefore not simply finding a prior incident; it is turning accumulated incident experience into evidence-weighted guidance. In short: traditional RAG answers from retrieved knowledge, while KARNA improves from operational outcomes.

## 11. Non-Functional Requirements

- **Responsiveness:** An analysis result should feel interactive; target under 5 seconds for the MVP under normal demo conditions.
- **Reliability:** Persisted incidents, outcomes, and corrections survive application restart.
- **Explainability:** Every memory-backed recommendation includes inspectable evidence.
- **Safety:** KARNA presents suggestions as decision support, never as autonomous remediation; it flags low confidence and conflicting evidence.
- **Usability:** A first-time engineer can complete analysis, outcome recording, and correction without training.
- **Privacy posture:** The MVP uses local/demo data only; no external production-system integrations.
- **Accessibility:** Keyboard-operable core flows, clear contrast, readable confidence labels, and non-color-only status indicators.

## 12. Success Metrics

### Hackathon success

- Demonstrate all four required scenarios without manual data editing during the presentation.
- Show a recommendation that visibly changes after a correction.
- Make evidence and historical outcomes visible in one click.
- Earn judge comprehension of the memory → learning → improvement loop within two minutes.

### Product signals

- Memory utilization rate: share of analyses with relevant recalled evidence.
- Recommendation adoption rate: share of recommendations selected or followed.
- Fix success rate: worked outcomes divided by recorded outcomes.
- Learning lift: increase in corrected/proven recommendation ranking for repeat scenarios.
- Correction rate: corrections per analyzed incident, interpreted as a source of learning rather than pure failure.
- Time-to-guidance: time from incident input to actionable, evidence-backed response.

## 13. MVP Scope

The MVP includes a single-user local experience with incident intake, seeded and newly created memory, semantic or relevance-based recall, recommendation generation, outcome capture, corrections, Memory Inspector, memory on/off comparison, and a compact analytics dashboard.

The product must prioritize a polished and deterministic end-to-end story over breadth. It need not ingest real enterprise systems to prove the core product thesis.

## 14. Out of Scope

- Jira, Slack, PagerDuty, or documentation integrations
- Authentication, authorization, RBAC, multi-tenancy, billing, or enterprise provisioning
- Autonomous changes to infrastructure or production systems
- Full incident command workflows, alerts, paging, or chat collaboration
- Complex causal graphs and cross-service topology inference
- Advanced enterprise retention, audit, compliance, and deployment controls

## 15. Stretch Goals

- Natural-language follow-up questions grounded in the selected incident memory
- Feedback quality weighting based on repeated validation
- Contradiction detection between memories
- Memory timeline showing how confidence evolved
- Runbook import with source attribution
- Lightweight service and severity filters
- Recommendation comparison view showing “before learning” vs. “after learning”

## 16. System Constraints

KARNA uses a Next.js/TypeScript/Tailwind frontend, FastAPI/Python backend, SQLite persistence, Groq for LLM generation, and Hindsight Memory behind a future-compatible memory abstraction. The hackathon implementation must operate on constrained time and demo-safe data. It should degrade gracefully to a context-only recommendation when memory is unavailable and should never imply certainty unsupported by evidence.

## 17. Competitive Analysis

| Alternative | Strength | Limitation KARNA addresses |
|---|---|---|
| Search over tickets/docs | Finds documents | Requires human synthesis; does not learn outcomes |
| Traditional runbooks | Provides standardized steps | Static and often detached from real incident results |
| Generic AI chatbot | Flexible explanation | Weak durable operational memory and feedback loop |
| Incident-management platforms | Coordinate response | Usually do not transform outcomes/corrections into transparent guidance |
| Basic RAG | Retrieves relevant text | Does not explicitly weigh success, failure, and corrections over time |

KARNA differentiates through outcome-aware memory, correction-first learning, and a visible evidence chain.

## 18. Risks

- Incorrect recommendations could reduce trust or create unsafe actions.
- Sparse or poor-quality memory can create misleading confidence.
- LLM output can hallucinate beyond the recalled evidence.
- A generic demo may be mistaken for a simple chatbot.
- Learning may be imperceptible if scenarios are not designed for contrast.
- Feedback can be contradictory or inaccurate.

## 19. Risk Mitigation Strategies

- Display confidence, evidence count, and historical success/failure signals beside each recommendation.
- Use explicit low-confidence states and avoid prescriptive language where evidence is weak.
- Ground recommendation generation in recalled memory and show sources in the inspector.
- Keep the MVP decision-support-only; require a human to act and record outcome.
- Seed a controlled repeat scenario with an unambiguous correction and measurable recommendation change.
- Preserve conflicting memories and favor validated corrections/outcomes instead of silently deleting history.

## 20. Hackathon Winning Strategy

Lead with the sharpest insight: incident tools record what happened, but KARNA makes the experience change the next decision. Make memory tangible, not a backend claim. The UI should put three artifacts side by side: recalled experience, the resulting recommendation, and the learning event that changes the next recommendation.

Optimize the pitch around a single relatable incident—database connection-pool exhaustion or timeout—and show that a failed historical remedy is actively de-prioritized. Use polished, legible explanations instead of excessive technical architecture. Demonstrate that the core value collapses with memory off, then immediately prove improvement after correction.

## 21. Demo Strategy

1. **Frame the problem:** “Teams solve the same incident repeatedly because knowledge dies in tickets and people.”
2. **Scenario 1 — Memory Off:** Enter “Database timeout.” Show a cautious generic recommendation such as investigate connectivity, pool limits, and query load. State that it lacks organizational experience.
3. **Scenario 2 — Memory On:** Run the same incident. Show matched incidents, prior root cause, proven fix, success rate, and a specific recommendation. Open Memory Inspector.
4. **Scenario 3 — Correction:** Correct the diagnosis/fix (for example, identify an undersized connection pool rather than a network issue) and mark the corrected action as worked.
5. **Scenario 4 — Improvement:** Submit the same or highly similar incident again. Show the corrected fix ranked first, a higher/evidence-adjusted confidence, and an explanation that cites the newly stored correction/outcome.
6. **Close with analytics:** Show one more incident, one more durable lesson, and a measurable growth signal.

The demo’s visual refrain is: **Memory → Learning → Improvement → Organizational Intelligence.**

## 22. Future Roadmap

### Phase 1: Validate the loop

Improve retrieval quality, evidence ranking, correction UX, and analytics using local or synthetic incidents.

### Phase 2: Connect organizational knowledge

Add carefully scoped read-only ingestion from incident records, runbooks, and collaboration systems with provenance and approvals.

### Phase 3: Operational intelligence

Add team-level memory governance, service context, contradiction review, feedback quality signals, and recurring-pattern insights.

### Phase 4: Enterprise readiness

Introduce authentication, permissions, auditability, retention controls, deployment options, and integration governance.

## 23. Acceptance Criteria

- A user can submit a title and description and receive root-cause hypotheses, fixes, confidence, and evidence.
- With Memory On, the result displays at least one relevant historical memory when suitable seed data exists.
- With Memory Off, the same input produces a generic response with no recalled historical evidence.
- A user can see recalled memories, relevance scores, outcomes, and selection rationale in Memory Inspector.
- A user can mark a fix worked or failed, and the outcome persists.
- A user can correct a root cause and/or fix, and the correction persists.
- Repeating a corrected scenario changes the ranking/explanation in a way attributable to the correction or recorded outcome.
- Analytics reflect newly recorded incidents, outcomes, and corrections.
- The four demo scenarios run end to end from the application UI.

## 24. Technical Assumptions

- Frontend: Next.js, TypeScript, Tailwind CSS.
- Backend: FastAPI and Python.
- Persistence: SQLite for hackathon-scale durable data.
- Memory: Hindsight Memory, accessed through an abstraction that permits future replacement or augmentation.
- Generation: Groq-hosted LLM.
- Data: seeded, synthetic incident data for the MVP; no production connections required.

## 25. Business Impact

KARNA can reduce duplicated investigation effort, lower time-to-guidance, improve consistency across responders, and reduce dependence on scarce senior expertise. For managers, it makes operational learning measurable. For teams, it converts incident resolution from a one-time cost into a compounding knowledge asset. The most credible early ROI measure is reduced time spent searching for prior context on recurring incidents, followed by improving fix-success and MTTR trends.

## 26. Architecture Recommendations

Structure the product around separable layers: a responsive incident workspace; an application service that orchestrates analysis and feedback; a memory abstraction responsible for storing, retrieving, and ranking experience; durable local persistence; and an LLM generation layer constrained by retrieved evidence. Treat outcomes and corrections as first-class memory signals, not free-text annotations. Preserve provenance from recommendation back to its recalled memories so the inspector and trust model remain intact. This modular approach protects the MVP from lock-in while keeping memory—not the model prompt—the central engine.

## 27. Product Differentiators

- **Outcome-aware memory:** successful fixes gain support; failed fixes become cautionary evidence.
- **Correction-first learning:** engineers directly teach KARNA when it is wrong.
- **Inspectable intelligence:** users see what was recalled and why it mattered.
- **Demonstrable learning:** repeated input produces improved output after feedback.
- **Operational focus:** recommendations are designed for incident decisions, not general conversation.
- **Memory abstraction:** the product is built around a durable learning capability rather than a single retrieval implementation.

## 28. Expected Judge Reactions and Evaluation Criteria Mapping

| Criterion | What judges should observe | Proof in demo |
|---|---|---|
| Innovation | AI that changes from operational experience | Before/after correction recommendation |
| Memory-centric design | Memory is necessary to the product’s value | Explicit Memory Off vs. Memory On contrast |
| Learning from experience | Outcomes and corrections alter later behavior | Recorded correction is cited in repeat analysis |
| Technical depth | Clear memory abstraction, relevance ranking, persistence, grounded generation | Architecture view and Memory Inspector |
| User experience | Calm, fast, interpretable incident workflow | One-screen analysis and evidence inspection |
| Real-world impact | Less repeated work, faster response, knowledge democratization | Relatable recurring database incident and metrics |

The intended judge takeaway: **“This is not an AI wrapper around search. It is a credible system for turning every incident into better future engineering decisions.”**
