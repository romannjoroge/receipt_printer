# receipt_printer

An Odoo module that sends receipts directly to a USB thermal printer via a local
print agent, bypassing the browser print dialog. Inspired by the "Odoo Direct
Print" App Store module.

This repo contains the **Odoo module only**. The local print agent (the small
Python/USB process that actually talks to the printer) is a separate project —
see [Related Projects](#related-projects) below.

See [AGENT.md](./AGENT.md) for the full functional spec and build plan if you're
using a coding agent to develop this.

## How It Works

1. A receipt is triggered in Odoo (POS order, or a manual test print).
2. Odoo creates a `receipt_printer.print.job` record queued for a specific
   `receipt_printer.print.printer`.
3. The local print agent polls `GET /receipt_printer/pending_jobs`, gets the job,
   and prints it via ESC/POS over USB.
4. The agent calls `POST /receipt_printer/ack` to mark the job printed or failed.

## Requirements

- Odoo **19.0**
- Python 3.10+ (matching your Odoo version's requirement)
- A local Odoo development environment already able to run `odoo-bin`
- (Separately, on the machine with the printer) the print agent, `python-escpos`,
  and USB permissions configured — not covered here

## Installation

1. Clone/copy this module into your Odoo `addons` path:
   ```bash
   cp -r pos_direct_print /path/to/odoo/addons/
   ```
2. Update the apps list and install:
   ```bash
   odoo-bin -c odoo.conf -u base -d your_db --stop-after-init
   ```
   Then install `receipt_printer` from the Apps menu (search with Developer
   Mode's "Update Apps List" first if it doesn't appear), or via CLI:
   ```bash
   odoo-bin -c odoo.conf -i pos_direct_print -d your_db --stop-after-init
   ```

## Configuration

1. Go to **Receipt Printer → Printers** and create a printer record.
   - `identifier`: the printer's USB vendor:product ID (find via `lsusb` on
     Linux/Mac or Device Manager on Windows).
   - Save, then copy the generated `api_key` — the local agent needs this to
     authenticate.
2. (POS only) On **Point of Sale → Configuration**, set the printer on the POS
   config you want to use direct printing.
3. Use the **Test Print** button on the printer form to queue a test job, then
   confirm your local agent picks it up and prints it.

## Running Tests

This module is built test-first; run the suite before and after any change.

```bash
odoo-bin -c odoo.conf -i pos_direct_print --test-enable --stop-after-init -d test_db
```

To run a single test file/class during development, use Odoo's `--test-tags`:

```bash
odoo-bin -c odoo.conf -i receipt_printer --test-enable \
  --test-tags /receipt_printer:TestDirectPrintJob --stop-after-init -d test_db
```

```bash
cd "C:\Program Files\Odoo 19.0e.20260702\server\"
"..\python\python.exe" odoo-bin -c odoo.conf --addons-path="odoo\addons,C:\Odoo\jani" -d receipt_printer -i receipt_printer -u receipt_printer --test-enable --stop-after-init --log-level=test
```

Check the log output for `FAIL`/`ERROR` — Odoo test runs don't always exit
non-zero in older versions, so don't rely on exit code alone.

## Project Structure

```
receipt_printer/
    __manifest__.py
    models/            # direct.print.printer, direct.print.job, pos.config extension
    controllers/        # HTTP routes for the local agent
    security/            # access rights
    views/                # backend UI
    static/src/js/        # POS frontend override
    tests/                # TDD test suite
```

## API Routes (for agent developers)

| Route | Method | Purpose |
|---|---|---|
| `/receipt_printer/pending_jobs` | GET | Returns pending jobs for the authenticated printer |
| `/receipt_printer/ack` | POST | Marks a job as printed or failed |

Both routes require the printer's `api_key`. See `controllers/main.py` for
exact request/response shapes.

## Related Projects

- **Local print agent** — polls the routes above and sends ESC/POS commands to
  the USB printer. Separate repo/script, not included here.

## Status

Early development. See commit history for TDD progress by phase (printer
model → job model → controllers → POS integration).

## License

**LGPL-3**