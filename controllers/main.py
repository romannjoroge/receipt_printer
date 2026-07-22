import json

from odoo import http, fields
from odoo.http import request


def _authenticate_printer():
    """Authenticate the request using the Authorization header.

    Returns the authenticated printer record or None.
    """
    auth_header = request.httprequest.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    api_key = auth_header[7:].strip()
    if not api_key:
        return None
    Printer = request.env['receipt_printer.print.printer'].sudo()
    return Printer.search([('api_key', '=', api_key)], limit=1) or None


class ReceiptPrinterController(http.Controller):

    @http.route('/receipt_printer/pending_jobs', type='http', auth='none',
                methods=['GET'], csrf=False)
    def pending_jobs(self, **kwargs):
        printer = _authenticate_printer()
        if not printer:
            return request.make_json_response({'error': 'Unauthorized'}, status=401)

        # Update last_seen
        printer.sudo().write({'last_seen': fields.Datetime.now()})

        jobs = request.env['receipt_printer.print.job'].sudo().search([
            ('printer_id', '=', printer.id),
            ('state', '=', 'pending'),
        ])
        job_list = [{'id': j.id, 'payload': j.payload} for j in jobs]
        return request.make_json_response({'jobs': job_list})

    @http.route('/receipt_printer/ack', type='http', auth='none',
                methods=['POST'], csrf=False)
    def ack(self, **kwargs):
        printer = _authenticate_printer()
        if not printer:
            return request.make_json_response({'error': 'Unauthorized'}, status=401)

        try:
            body = json.loads(request.httprequest.data)
        except (json.JSONDecodeError, ValueError):
            return request.make_json_response(
                {'error': 'Invalid JSON'}, status=400
            )

        job_id = body.get('job_id')
        status = body.get('status')
        error_message = body.get('error_message', '')

        if not job_id or status not in ('printed', 'failed'):
            return request.make_json_response(
                {'error': 'Invalid payload'}, status=400
            )

        Job = request.env['receipt_printer.print.job'].sudo()
        job = Job.search([
            ('id', '=', job_id),
            ('printer_id', '=', printer.id),
        ], limit=1)
        if not job:
            return request.make_json_response(
                {'error': 'Job not found'}, status=404
            )

        if status == 'printed':
            job.action_mark_printed()
        else:
            job.action_mark_failed(error_message)

        return request.make_json_response({'status': 'ok'})

    @http.route('/receipt_printer/create_job', type='json', auth='user',
                methods=['POST'], csrf=False)
    def create_job(self, printer_id=None, payload=None, **kwargs):
        if not printer_id or not payload:
            return {'error': 'Missing printer_id or payload'}
        printer = request.env['receipt_printer.print.printer'].browse(printer_id)
        if not printer.exists():
            return {'error': 'Printer not found'}
        job = request.env['receipt_printer.print.job'].create({
            'printer_id': printer.id,
            'payload': payload,
        })
        return {'job_id': job.id}
