import json

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    receipt_printer_printer_id = fields.Many2one(
        comodel_name='receipt_printer.print.printer',
        string='Receipt Printer',
    )

    @api.constrains('receipt_printer_printer_id')
    def _check_printer_unique(self):
        for config in self:
            if config.receipt_printer_printer_id:
                other = self.search([
                    ('receipt_printer_printer_id', '=', config.receipt_printer_printer_id.id),
                    ('id', '!=', config.id),
                ], limit=1)
                if other:
                    raise ValidationError(
                        'Printer "%s" is already linked to POS "%s".'
                        % (config.receipt_printer_printer_id.name, other.name)
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


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    receipt_printer_printer_id = fields.Many2one(
        comodel_name='receipt_printer.print.printer',
        string='Receipt Printer',
        related='pos_config_id.receipt_printer_printer_id',
        readonly=False,
    )
