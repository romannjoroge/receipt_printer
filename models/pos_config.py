import base64
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
        """Create a print job for the given order data.

        ``order_data`` can be either a dict (structured order data) or a
        base64-encoded JPEG string (the rendered receipt image).
        """
        self.ensure_one()
        if not self.receipt_printer_printer_id:
            return

        vals = {
            'printer_id': self.receipt_printer_printer_id.id,
            'pos_config_id': self.id,
        }

        if isinstance(order_data, str):
            # It's a base64 receipt image from the POS
            vals['payload'] = order_data
            # Strip data:image prefix if present
            image_data = order_data
            if ',' in image_data and image_data.startswith('data:'):
                image_data = image_data.split(',', 1)[1]
            vals['receipt_image'] = image_data
        else:
            vals['payload'] = json.dumps(order_data)

        self.env['receipt_printer.print.job'].create(vals)

    @api.model
    def _load_pos_data_fields(self, config):
        fields = super()._load_pos_data_fields(config)
        if fields:
            fields.append('receipt_printer_printer_id')
        return fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    receipt_printer_printer_id = fields.Many2one(
        comodel_name='receipt_printer.print.printer',
        string='Receipt Printer',
        related='pos_config_id.receipt_printer_printer_id',
        readonly=False,
    )
