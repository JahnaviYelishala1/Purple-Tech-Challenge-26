# Final Compliance Report

## Status Summary

- Re-entry support: Implemented with a lightweight time-window approach using session history and `REENTRY_WINDOW_MINUTES`.
- Exit support: Implemented and active through the `EXIT` camera role; exit events close sessions and update duration metrics.
- Confidence propagation: Implemented with detector confidence first, tracker confidence second, and a fallback only when needed.

## What Changed

- Added `REENTRY_WINDOW_MINUTES` to application settings.
- Promoted the configured exit camera role in `config/camera_roles.json`.
- Reclassified arrival events to `REENTRY` when a visitor returns within the re-entry window.
- Updated funnel and pipeline-status aggregation so `REENTRY` remains entry-like for analytics.
- Propagated real confidence values through detector event payloads.
- Added regression tests for re-entry, exit closure, and confidence source precedence.

## Remaining Limitations

- Re-entry is time-window based, not identity-model based.
- Group or party tracking is not implemented.
- The CV pipeline remains intentionally lightweight and uses YOLOv8 plus tracking heuristics.

## Estimated Challenge Compliance

- Estimated compliance: high.
- Main scored behaviors now covered: entry, exit, re-entry, billing correlation, session closure, funnel continuity, and confidence propagation.
- Residual risk: dataset-specific edge cases outside the implemented lightweight heuristics.