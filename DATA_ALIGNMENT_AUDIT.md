# Data Alignment Audit

## Scope

Audit of the dashboard-facing value chain across:
- [dashboard/app.py](dashboard/app.py)
- [app/services/heatmap_service.py](app/services/heatmap_service.py)
- [app/services/funnel_service.py](app/services/funnel_service.py)
- [app/services/metrics_service.py](app/services/metrics_service.py)
- [app/services/anomaly_service.py](app/services/anomaly_service.py)
- [config/camera_roles.json](config/camera_roles.json)
- [app/db/demo_seed.py](app/db/demo_seed.py)
- [pipeline/mock_event_generator.py](pipeline/mock_event_generator.py)

## Value Trace Table

| Current Value | Source | Real Dataset Match? |
| --- | --- | --- |
| `Store Entry` | Dashboard label in [dashboard/app.py](dashboard/app.py) backed by the `ENTRY` event stage from [app/services/funnel_service.py](app/services/funnel_service.py) | YES |
| `Zone Engagement` | Dashboard label in [dashboard/app.py](dashboard/app.py) backed by `ZONE_ENTER` / `ZONE_DWELL` counts from [app/services/funnel_service.py](app/services/funnel_service.py) | YES |
| `Billing Queue` | Dashboard label in [dashboard/app.py](dashboard/app.py) backed by `BILLING_QUEUE_JOIN` from [app/services/funnel_service.py](app/services/funnel_service.py) | YES |
| `Completed Purchase` | Dashboard label in [dashboard/app.py](dashboard/app.py) backed by converted sessions from [app/services/metrics_service.py](app/services/metrics_service.py) and [app/services/funnel_service.py](app/services/funnel_service.py) | YES |
| `Zone A` / `Zone B` | Generic zone labels rendered by [dashboard/app.py](dashboard/app.py) from heatmap `zone_id` values | YES |
| `Billing Area` | Generic billing-zone label rendered by [dashboard/app.py](dashboard/app.py) from heatmap `zone_id` values | YES |
| `Queue Congestion` | Alert label in [dashboard/app.py](dashboard/app.py) backed by `QUEUE_SPIKE` from [app/services/anomaly_service.py](app/services/anomaly_service.py) | YES |
| `Low Engagement Zone` | Alert label in [dashboard/app.py](dashboard/app.py) backed by `DEAD_ZONE` from [app/services/anomaly_service.py](app/services/anomaly_service.py) | YES |
| `Conversion Dip` | Alert label in [dashboard/app.py](dashboard/app.py) backed by `CONVERSION_DROP` from [app/services/anomaly_service.py](app/services/anomaly_service.py) | YES |
| `electronics` | Former seeded/demo zone label in [app/db/demo_seed.py](app/db/demo_seed.py) and [pipeline/mock_event_generator.py](pipeline/mock_event_generator.py) | NO |
| `grocery` | Former seeded/demo zone label in [app/db/demo_seed.py](app/db/demo_seed.py) and [pipeline/mock_event_generator.py](pipeline/mock_event_generator.py) | NO |
| `Billing Interest` | Former dashboard funnel label in [dashboard/app.py](dashboard/app.py) | NO |

## Source Findings

- The dashboard metrics are all sourced from API responses, not hardcoded numeric values.
- Funnel counts come from actual event types and converted sessions.
- Heatmap values come from persisted `zone_id` fields on events.
- Anomalies are derived from current store events and sessions.
- Camera-role behavior is controlled by [config/camera_roles.json](config/camera_roles.json), which currently exposes `ZONE`, `ENTRANCE`, `EXIT`, and `BILLING` roles.

## Removed Demo Labels

- `electronics`
- `grocery`
- `aisle-a`
- `aisle-b`
- `aisle-c`
- `Billing Interest`

## Removed Seeded Values

- Demo heatmap categories in [app/db/demo_seed.py](app/db/demo_seed.py) were replaced with generic zone names.
- Demo event generator labels in [pipeline/mock_event_generator.py](pipeline/mock_event_generator.py) were replaced with generic zone names.
- The dashboard funnel label `Billing Interest` was replaced with `Billing Queue`.

## Remaining Assumptions

- The actual CCTV dataset does not expose business-grade merchandising names in configuration, so `Zone A` and `Zone B` are used as generic placeholders instead of fake retail categories.
- `Billing Area` is the business-facing label used for billing-zone analytics.
- If the dataset later exposes true semantic zone names, only the generic display mapping should need to change.
- The dashboard does not invent new analytics values; it only re-labels existing event-derived metrics.
