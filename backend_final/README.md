
Refactored backend (v2)
- Manual caching added to admin report methods:
  - admin_report_summary
  - admin_report_occupancy
  - admin_report_revenue
  - admin_report_reservations_by_lot
- Cache invalidation occurs on create/update/delete of lots and on book/release actions.
- Cache object imported from backend.extensions (per your confirmation).
