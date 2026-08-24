## Features

- **Reservations** - booking, check-in/check-out, cancellation, and mid-stay room reassignment billed pro-rata against the actual nights spent in each room. No re-rate, no swap fee.
- Charges and payments are derived live from the underlying rows via SQL `SUM()` rather than manually-incremented running totals, so an interrupted request can't silently desync a guest's balance from what they actually owe.
- Front desk can initiate a charge void, but an admin has to authenticate at the moment of the void — supervisor override, not a rubber stamp. Voided charges stay on record (struck through, not deleted) with who voided them and when.
- Housekeeping runs on a task board with a pre-checkout inspection gate. Payment and final checkout are blocked until the room passes inspection.
- Check-in/out time tracking compares scheduled vs. actual time, computed server-side against a configurable grace period, timezone-correct.
- **Role-based access control** - JWT auth with router-level default authentication (every route requires login even if a per-endpoint role check is forgotten), plus per-endpoint role requirements on top.