import uuid

from odoo import models, fields, api


class ReceiptPrinterPrinter(models.Model):
    _name = 'receipt_printer.print.printer'
    _description = 'Receipt Printer'

    name = fields.Char(required=True)
    connection_type = fields.Selection(
        selection=[('usb', 'USB')],
        default='usb',
        required=True,
    )
    identifier = fields.Char(
        help='USB vendor:product ID or serial number',
    )
    api_key = fields.Char(
        default=lambda self: str(uuid.uuid4()),
        copy=False,
        groups='receipt_printer.group_printer_user',
    )
    active = fields.Boolean(default=True)
    last_seen = fields.Datetime()
    state = fields.Selection(
        selection=[('online', 'Online'), ('offline', 'Offline')],
        compute='_compute_state',
        store=True,
    )

    def action_test_print(self):
        self.ensure_one()
        import json
        self.env['receipt_printer.print.job'].create({
            'printer_id': self.id,
            'payload': json.dumps({'type': 'test', 'text': 'Test print from Odoo'}),
        })

    @api.depends('last_seen')
    def _compute_state(self):
        for record in self:
            if record.last_seen:
                from datetime import timedelta, datetime
                threshold = datetime.now() - timedelta(seconds=60)
                if fields.Datetime.from_string(record.last_seen) >= threshold:
                    record.state = 'online'
                else:
                    record.state = 'offline'
            else:
                record.state = 'offline'
