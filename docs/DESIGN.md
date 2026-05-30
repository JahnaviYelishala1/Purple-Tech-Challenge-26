# Store Intelligence Platform Design

## 1. Problem Statement

The goal of the Store Intelligence Platform is to turn raw retail activity into structured operational insight. A store produces events such as entry, zone movement, queue join activity, and transaction completion. Those events are only valuable if they can be turned into metrics that answer practical questions: how many visitors entered, how many reached the billing queue, where visitors dwell, whether conversion is healthy, and which stores are showing abnormal behavior. The challenge also implies that the system should be approachable within a short engineering window, which means the solution needs to prioritize a clean backend architecture, deterministic analytics, and a testable implementation over premature complexity.

## 2. System Architecture

The system is organized as a layered FastAPI application. HTTP routes live in `app/api/` and only handle request validation, dependency injection, and response mapping. All domain logic is kept in `app/services/`, which prevents analytics rules from being spread across route handlers. Data persistence is handled by SQLAlchemy ORM models in `app/models/`, while Pydantic schemas in `app/schemas/` define strict request and response contracts. Cross-cutting concerns such as configuration, logging, and middleware live in `app/core/`. Database engine and initialization logic live in `app/db/`.

The submission includes a draw.io architecture diagram at [docs/store-intelligence-architecture.drawio](docs/store-intelligence-architecture.drawio). It documents the execution path from CCTV cameras through YOLOv8, tracking, event publication, FastAPI, SQLite, analytics, and the Streamlit dashboard.

This structure is intentionally simple but scalable. It allows new analytics capabilities to be added as new services and routes without changing the established boundaries. It also makes the codebase easier to test, because service logic can be exercised without a live HTTP server.

## 3. Event Driven Design

The system is event driven at the business layer. Event ingestion is the primary entry point for store activity. Each valid event is persisted, and then downstream services react to the event type. Entry events can open a visitor session, exit events can close one, and transaction events can mark a session as converted. This keeps the data model normalized and makes metrics deterministic.

The event-driven approach is useful because the same raw event stream can power multiple analytics views. A single `ENTRY` event contributes to session lifecycle tracking, funnel analytics, and anomaly detection. A `ZONE_DWELL` event contributes to heatmaps and can influence anomaly thresholds. This design keeps the ingestion path thin while allowing the analytics layer to derive multiple insights from the same source of truth.

## 4. Database Design

The current implementation uses SQLite for local development and challenge delivery. The database includes tables for events, visitor sessions, transactions, and store-level metadata. The ORM layer uses SQLAlchemy 2.0 `Mapped` syntax and includes indexes on commonly queried dimensions such as store ID, visitor ID, event type, and timestamp. Those indexes support the exact access patterns needed by the analytics endpoints.

SQLite is an acceptable choice here because it minimizes setup friction and makes it easy to run the app in a local container or test fixture. The schema and service layers were written to avoid SQLite-specific logic so the storage backend can be replaced later if needed.

## 5. Session Lifecycle

Session is the unit of analysis for conversion and funnel behavior. A session begins on an entry event and ends on an exit event. If a visitor enters the store multiple times, the system treats the active open session as the current one. Transactions can mark the most recent session as converted when they correspond to the same store. This model is aligned with retail funnel analysis because it allows the platform to compute time-based metrics such as dwell duration, conversion rate, and active visitors.

The service layer enforces session behavior instead of the API layer. That keeps the rules reusable across ingestion endpoints and later batch jobs.

## 6. Analytics Layer

The analytics layer is implemented as dedicated services for metrics, funnel, heatmap, and anomalies. Each service reads the canonical data in the database and computes a store-level response shape. Metrics calculates unique visitors, active visitors, conversion rate, and average session duration. Funnel computes the stage progression from entry to purchase. Heatmap aggregates zone visit and dwell behavior. Anomalies flags operational patterns such as queue spikes, dead zones, and conversion drops.

The dashboard also exposes a CCTV pipeline status section so the submission can visually prove that the camera feed, YOLO detection, tracking IDs, event publisher, and analytics stack are connected end to end.

These services are intentionally deterministic. They do not require machine learning to produce meaningful challenge results, which makes them easy to validate in tests and easy to explain in an interview.

## 7. API Layer

The API layer exposes thin FastAPI endpoints that call the services and return typed Pydantic responses. The endpoints are grouped by concern: events, transactions, metrics, funnel, heatmap, and anomalies. FastAPI was chosen because it provides automatic validation, interactive Swagger documentation, and a simple dependency model. Those features reduce boilerplate and help the project look polished under time pressure.

The API layer also keeps failure handling consistent by translating database exceptions into HTTP 500 responses and leaving the business logic in services.

## 8. Structured Logging

The application uses centralized structured JSON logging. Request middleware generates a trace ID for each request and logs method, path, status code, and latency. This makes debugging easier without introducing a separate observability stack. JSON logs are especially useful in Docker because they remain machine-readable and can be ingested into any future log collection system.

## 9. Testing Strategy

Testing is built around pytest and isolated in-memory SQLite fixtures. Each test gets its own session and dependency override, which keeps the test suite deterministic. The tests cover ingestion idempotency, session behavior, metrics, funnels, heatmaps, anomalies, and schema validation. This gives strong confidence in the service layer without depending on external infrastructure.

## 10. AI-Assisted Decisions

AI was used as an implementation accelerator, not as the source of truth for architecture. It helped translate the challenge requirements into concrete FastAPI routes, SQLAlchemy models, Pydantic schemas, and pytest scaffolding. AI also helped draft the initial logging and middleware structure and quickly generate repetitive test cases.

AI assistance was especially useful in API design. It helped keep route handlers thin, standardize request dependency injection, and maintain consistent response models. In test generation, AI accelerated the creation of coverage for ingestion, funnel, anomaly, and metrics behavior, which saved time on repetitive fixture setup.

Some AI suggestions were accepted directly when they aligned with the project goals: layered architecture, thin route handlers, service-based analytics, and isolated test fixtures. Other suggestions were overridden when they conflicted with the challenge constraints or with engineering judgment. For example, the implementation stayed on SQLite rather than switching to PostgreSQL because the goal at this stage is to deliver a reliable, self-contained challenge submission. The project also avoided introducing unnecessary infrastructure such as Redis or Kafka, because those tools would increase complexity without improving the scoring criteria.

Engineering judgment also overrode AI where the dataset was unclear. Instead of jumping into a full CV pipeline, the implementation focused on backend analytics first because the challenge is clearly stronger when the backend scoring section is complete. The result is a practical, verifiable backend foundation that can support a future dashboard or CV pipeline once the dataset is better understood.

## 11. Submission Packaging

- Dashboard screenshots belong in `docs/screenshots/`
- Large demo videos should stay out of the repository and remain excluded by `.gitignore`
- The demo runner prints a compact operational summary that is useful for the recorded walkthrough
