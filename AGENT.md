# AGENT.md — Odoo Direct Print Module

## Project Summary

Build a custom Odoo module (`receipt_printer`) in this directory that lets Odoo send receipts to a
USB thermal printer via a local print agent, bypassing the browser's print dialog.
The module is the **server side only** — it exposes models, a UI, and HTTP routes
that a separate local Python agent (built elsewhere, not part of this repo) polls
for print jobs. Do not build the agent itself as part of this task; only build the
Odoo module that the agent talks to.

Inspiration: the existing "Odoo Direct Print" module on the Odoo App Store. Use it
as a reference for expected behavior, not as code to copy.

## Development Method: Test-Driven Development

This is a hard requirement, not a suggestion. For every piece of functionality:

1. Write a failing test first that describes the desired behavior.
2. Run it and confirm it fails for the expected reason (not a typo/import error).
3. Write the minimum code to make it pass.
4. Run the full test suite and confirm nothing else broke.
5. Refactor if needed, keeping tests green.
6. Only then move to the next piece of functionality.

Never write model/controller code before its test exists. If you find yourself
writing implementation code first, stop, delete it, and write the test first
instead. Commit after each red-green-refactor cycle so the history shows the TDD
process.

Use Odoo's `odoo.tests.common.TransactionCase` (or `HttpCase` for controller/route
tests) as the test framework. Tests live under `tests/`. I will run the tests and communicate any issues

Aim for tests covering: model field constraints/defaults, business logic (job
state transitions), access rights (a user without rights cannot read/write
printers or jobs), and controller routes (status codes, payload shape, auth
failures, correct filtering of jobs by printer).

## Scope

### 1. `receipt_printer.print.printer` model
- Fields: `name`, `connection_type` (selection, default/only option for now:
  `usb`, but field must support adding more later), `identifier` (e.g. USB
  vendor:product id or serial, freeform char for now), `api_key` (used by the
  agent to authenticate — see Security), `active` (bool, default True),
  `last_seen` (datetime, updated when the agent polls), `state` (computed or
  stored: `online`/`offline`, derived from `last_seen` being within e.g. the
  last 60 seconds).
- Form view: all fields editable, plus a **"Test Print"** button that creates a
  `receipt_printer.print.job` with a canned test payload targeting this printer.
- List view: name, connection_type, identifier, state, last_seen.
- Test coverage: creating a printer, `last_seen`/`state` logic, the test-print
  button creates exactly one job with expected payload shape.

### 2. `receipt_printer.print.job` model
- Fields: `printer_id` (many2one, required), `payload` (text/JSON, the receipt
  content), `state` (selection: `pending`, `sent`, `printed`, `failed`,
  default `pending`), `error_message` (char, optional), `create_date`
  (built-in), `printed_date` (datetime, set on success).
- List view: printer, state, create_date, printed_date, short error preview.
- Method `action_mark_printed()` and `action_mark_failed(message)` that
  transition state and set timestamps — these are what the controller calls.
- Test coverage: valid state transitions, invalid transitions rejected (e.g.
  can't go from `printed` back to `pending` via these methods), error_message
  is stored and visible on failure.

### 3. Security
- `ir.model.access.csv` for both models: base access for internal users.
- Route authentication: printers each have an `api_key`. The agent must send
  it (e.g. `Authorization: Bearer <key>` or a header) when calling routes.
  Requests with a missing/invalid key return 401 and must NOT reveal whether
  the printer identifier exists.
- Test coverage: user without printer access rights cannot read/write via ORM;
  routes reject missing/invalid api_key; routes accept valid api_key.

### 4. Controller routes
- `GET /receipt_printer/pending_jobs` — query param or header identifies the
  printer (by id + api_key). Returns pending jobs for that printer only, as
  JSON: `{"jobs": [{"id": ..., "payload": ...}, ...]}`. Must not return jobs
  belonging to other printers.
- `POST /receipt_printer/ack` — body: `{"job_id": ..., "status": "printed"|"failed",
  "error_message": "..."}` (error_message optional, required if status is
  failed). Calls the model methods above. Returns 200 with a small
  confirmation JSON, or an appropriate 4xx if job_id doesn't exist or doesn't
  belong to the authenticated printer.
- These routes are `type="http"`, `auth="none"` (auth handled manually via
  api_key, not Odoo session), CSRF disabled (agent isn't a browser session).
- Test coverage: happy path for both routes, wrong/missing api_key, job
  belonging to a different printer is not returned/ack-able, malformed
  payloads return sensible errors rather than 500s.

### 5. POS integration
- Build this last, after the above is fully tested — it's the highest-risk,
  most Odoo-version-specific part.
- Override the POS receipt print action (OWL component) so that, when a
  printer is configured for the POS config, it creates a `receipt_printer.print.job`
  via RPC instead of (or in addition to, behind a setting) opening the
  browser print dialog.
- Add a `receipt_printer_printer_id` (many2one) field on `pos.config` so each POS
  can be linked to a printer.
- Test coverage: at minimum a Python-side test that the RPC-callable method
  used by the frontend creates a correctly-shaped job from a sample order.
  Full JS/OWL testing is lower priority than the Python coverage above — note
  any JS test gaps in your summary rather than skipping silently.

## Module Structure (expected)

```
receipt_printer/
    __manifest__.py
    __init__.py
    models/
        __init__.py
        receipt_printer_printer.py
        receipt_printer_job.py
        pos_config.py
    controllers/
        __init__.py
        main.py
    security/
        ir.model.access.csv
    views/
        receipt_printer_printer_views.xml
        receipt_printer_job_views.xml
        pos_config_views.xml
        menus.xml
    static/src/js/  (POS override, added in the last phase)
    tests/
        __init__.py
        test_printer.py
        test_job.py
        test_security.py
        test_controllers.py
        test_pos_integration.py
```

## Build Order

Work in this order; do not start a phase until the previous phase's tests pass:

1. `receipt_printer.print.printer` model + tests + security + basic views.
2. `receipt_printer.print.job` model + tests + views.
3. Controller routes + tests (auth, filtering, ack flow).
4. Test Print button wired end-to-end (create job → confirm route returns it →
   simulate ack → confirm state updates) + test.
5. POS integration (`pos.config` field, RPC method, JS override) + tests.

## Constraints & Conventions

- Target Odoo version: **19.0**.
- Follow standard Odoo module conventions (manifest structure, naming, view
  inheritance) — don't invent nonstandard patterns.
- Keep the module installable and its tests runnable at every commit; don't
  leave the tree in a broken state between phases.
- No external dependencies beyond what ships with Odoo unless explicitly
  approved — this module should stay lightweight since the "real" printing
  logic lives in the separate agent, not here.
- After each phase, summarize: what was built, what tests were written, test
  results, and any deviations from this spec with reasoning.

## Out of Scope (do not build)

- The local print agent itself (Python/USB/ESC-POS code) — separate project.
- Network/Bluetooth printer support — structure fields to allow it later, but
  don't implement it now.
- Multi-database / multi-company edge cases beyond Odoo's defaults.