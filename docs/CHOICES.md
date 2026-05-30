# Store Intelligence Platform - Engineering Choices

This document records the implementation decisions made during the Store Intelligence Platform hiring challenge. The context was a strict 48-hour window, missing upstream dataset assets, and a requirement to deliver a backend that was testable, explainable, and cleanly structured.

## Decision 1: Database Choice

### Problem

The platform needed persistent storage for event ingestion, visitor session state, transaction records, and analytics queries. The storage choice also had to support local development, automated testing, and Docker-based startup with minimal setup friction.

### Options Considered

- PostgreSQL
- SQLite

### AI Recommendation

The AI recommendation was PostgreSQL. The reasoning was straightforward: PostgreSQL is the stronger default for production-readiness, concurrency, and analytics-heavy query workloads. It also aligns better with long-term scale and operational reliability.

### Final Choice

SQLite.

### Tradeoffs

Choosing SQLite reduced setup cost immediately. No separate database service had to be provisioned or coordinated for local development. Docker setup remained simple, and developers could run tests and spin the API up quickly without connection or orchestration issues. That mattered because challenge time was better spent implementing analytics behavior than maintaining infrastructure.

The downside is that SQLite is not the ideal long-term engine for concurrent write-heavy systems. To manage that risk, the data layer uses SQLAlchemy abstractions so migration to PostgreSQL remains straightforward.

### Why the Choice Was Made

With 48 hours available, the highest-value output was a working analytics backend with clear APIs and tests. SQLite enabled that outcome fastest, while ORM abstraction prevented lock-in.

## Decision 2: API Framework Choice

### Problem

The platform required a REST API layer capable of handling request validation, dependency injection, OpenAPI documentation, and test-friendly endpoint composition. Development speed mattered, but maintainability and clarity of contracts also mattered because the submission needed to be reviewable by engineers.

### Options Considered

- Flask
- Django
- FastAPI

### AI Recommendation

The AI recommendation was FastAPI. It best matched the need for typed request/response models, automatic OpenAPI generation, and rapid implementation without sacrificing structural quality.

### Final Choice

FastAPI.

### Tradeoffs

FastAPI provided immediate benefits for this challenge. Pydantic-based validation made input contracts explicit and safe. Dependency injection patterns simplified database session handling. Auto-generated Swagger/OpenAPI docs improved reviewability and made endpoint behavior easier to inspect quickly.

Compared with Django, FastAPI avoided unnecessary admin and templating overhead for an API-first backend. Compared with Flask, it reduced manual boilerplate for validation and schema docs. The tradeoff is that architecture discipline is still the team's responsibility, so clear service, schema, and model boundaries were enforced in code.

### Why the Choice Was Made

FastAPI was selected because it balanced delivery speed with typed, documented, and testable endpoints that reviewers could evaluate quickly.

## Decision 3: Event Schema Design

### Problem

The platform needed an event model that supports metrics, funnels, heatmaps, anomaly detection, and eventual computer vision integration. The schema had to remain stable even if upstream detection logic changes over time.

### Options Considered

1. Store raw CCTV detections directly.
2. Store normalized business events.

### AI Recommendation

The AI recommendation was to adopt an event-driven architecture with normalized business events, rather than persisting raw detections as the primary analytical contract.

### Final Choice

Normalized event-driven architecture.

Implemented event types:

- ENTRY
- EXIT
- ZONE_ENTER
- ZONE_EXIT
- ZONE_DWELL
- BILLING_QUEUE_JOIN
- BILLING_QUEUE_ABANDON
- REENTRY

### Tradeoffs

Normalized events add up-front modeling work because event semantics must be clearly defined and maintained. The payoff is strong decoupling: analytics stays independent of any CV vendor or tracking implementation, and services can be tested with synthetic inputs. A raw-detection design would have tightly coupled analytics to unstable upstream formats.

### Why the Choice Was Made

This choice enabled immediate delivery of metrics, funnels, heatmaps, and anomaly detection while preserving a clean interface for future YOLO and tracking integration.

## Decision 4: Session-Based Analytics Design

### Problem

The challenge required accurate conversion and funnel analysis, which depend on visitor-level progression rather than isolated event counts. A design was needed that could represent individual customer journeys through the store.

### Options Considered

1. Compute analytics directly from raw event streams.
2. Maintain explicit visitor sessions.

### AI Recommendation

The AI recommendation was to introduce a session abstraction as the core analytical unit.

### Final Choice

VisitorSession model.

### Tradeoffs

Maintaining explicit sessions introduces additional state management. Ingestion is no longer a simple append-only write path; session lifecycle updates must be applied as events arrive. Depending on event quality, there may also be ambiguity in boundaries (for example, re-entry behavior), which requires deterministic rules.

The advantage is substantial. Conversion rate becomes mathematically and conceptually correct because it is tied to session outcomes, not loosely inferred event totals. Funnel logic becomes clearer because each step maps to progression within a session. Metrics such as duration and abandonment are easier to compute and explain.

The session model also provides a stable unit for future enhancements, including stronger identity reconciliation and better re-entry handling.

### Why the Choice Was Made

The final decision aligned with the challenge objective and reduced analytical ambiguity. A session-first model made conversion tracking defensible and simplified service-level metric calculations.

## Decision 5: Missing Dataset Strategy

### Problem

The challenge documentation referenced CCTV clips and supporting files, but no usable dataset was available during implementation. Waiting for those assets would have blocked feature completion and test coverage.

### Options Considered

1. Wait for dataset availability.
2. Build backend using synthetic event generation.

### AI Recommendation

The AI recommendation was to proceed immediately with backend development using synthetic events and keep the pipeline integration boundary open for future real data.

### Final Choice

Synthetic event-driven development.

### Tradeoffs

Synthetic data does not validate real-world CV noise characteristics, camera artifacts, or tracker edge cases. That is a known limitation. Some operational uncertainties remain until real footage is connected.

Synthetic event generation enabled critical progress: ingestion APIs were implemented, analytics services were validated, and test scenarios became deterministic. It reduced schedule risk by removing dependency on unavailable external assets while preserving a clean integration point for real CV-derived events later.

### Why the Choice Was Made

The final decision prioritized deliverability and engineering momentum. Shipping a complete, testable backend with explicit assumptions was better than waiting for ideal inputs and submitting partial work.

## Decision 6: Architecture Choice

### Problem

The system needed an architecture that is scalable in structure, maintainable under review, and feasible to implement within the challenge timeline.

### Options Considered

- Microservices
- Modular Monolith

### AI Recommendation

The AI recommendation was Modular Monolith for this phase: preserve internal modular boundaries now and defer service decomposition until scale and team structure justify the extra operational complexity.

### Final Choice

Modular Monolith.

### Tradeoffs

Microservices offer independent deployability and fine-grained scaling, but they introduce early overhead: service contracts, distributed tracing, network boundaries, deployment coordination, and more difficult local testing. Those costs are rarely justified in a short challenge unless distributed concerns are the actual requirement.

A modular monolith keeps deployment simple while still enforcing separation of concerns. In this implementation, boundaries are clear across API routes, services, schemas, models, and database layers. That structure supports maintainability and testability without paying distributed-system tax prematurely.

The tradeoff is that independent component scaling is not as immediate as with microservices. If usage grows significantly, extraction work is still required, but explicit module boundaries make that incremental.

### Why the Choice Was Made

The final choice balanced ambition with execution reality. A modular monolith delivered fast implementation, easier testing, and low operational complexity while preserving architectural clarity.
