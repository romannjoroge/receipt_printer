import json

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    receipt_printer_printer_id = fields.Many2one(
        comodel_name='receipt_printer.print.printer',
        string='Receipt Printer',
    )

    def action_print_receipt(self, order_data):
        """Create a print job for the given order data."""
        self.ensure_one()
        if not self.receipt_printer_printer_id:
            return
        self.env['receipt_printer.print.job'].create({
            'printer_id': self.receipt_printer_printer_id.id,
            'payload': json.dumps(order_data),
        })
