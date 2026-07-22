from odoo import _, models, fields, api
from odoo.exceptions import ValidationError


class ReceiptPrinterJob(models.Model):
    _name = 'receipt_printer.print.job'
    _description = 'Receipt Print Job'

    printer_id = fields.Many2one(
        comodel_name='receipt_printer.print.printer',
        required=True,
        ondelete='cascade',
    )
    payload = fields.Text(required=True)
    receipt_image = fields.Image("Receipt Image", max_width=400, max_height=600)
    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('printed', 'Printed'),
            ('failed', 'Failed'),
        ],
        default='pending',
        required=True,
    )
    error_message = fields.Char()
    printed_date = fields.Datetime(readonly=True)

    def action_mark_printed(self):
        for job in self:
            if job.state not in ('pending', 'sent'):
                raise ValidationError(
                    _('Cannot mark a %s job as printed.') % job.state
                )
            job.write({
                'state': 'printed',
                'printed_date': fields.Datetime.now(),
                'error_message': False,
            })

    def action_mark_failed(self, message=''):
        for job in self:
            if job.state not in ('pending', 'sent'):
                raise ValidationError(
                    _('Cannot mark a %s job as failed.') % job.state
                )
            job.write({
                'state': 'failed',
                'error_message': message,
            })
