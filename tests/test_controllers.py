import json
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.tests.common import TransactionCase, tagged
from odoo.http import Response as JsonResponse


def _build_mock_request(env, method='GET', data=b'', headers=None):
    """Build a mock odoo.http.request with a real Odoo env."""
    req = MagicMock()
    req.httprequest = MagicMock()
    req.httprequest.method = method
    req.httprequest.data = data
    req.httprequest.headers = headers or {}

    # Wire up a real Odoo env so .sudo() / .search() / .create() work
    req.env = env

    # Capture make_json_response calls
    req.make_json_response.side_effect = lambda body, status=200: (
        JsonResponse(json.dumps(body), status=status, content_type='application/json')
    )
    return req


@tagged('post_install', '-at_install')
class TestReceiptPrinterControllers(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Printer = self.env['receipt_printer.print.printer']
        self.Job = self.env['receipt_printer.print.job']

        self.printer = self.Printer.create({
            'name': 'Test Printer',
            'api_key': 'test-api-key-12345',
        })
        self.other_printer = self.Printer.create({
            'name': 'Other Printer',
            'api_key': 'other-api-key-67890',
        })

    def _make_pending_jobs_request(self, api_key=None):
        """Call the pending_jobs controller method with a mocked request."""
        from odoo.addons.receipt_printer.controllers.main import ReceiptPrinterController
        ctrl = ReceiptPrinterController()

        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        req = _build_mock_request(self.env, method='GET', headers=headers)
        with patch('odoo.addons.receipt_printer.controllers.main.request', req):
            return ctrl.pending_jobs()

    def _make_ack_request(self, api_key=None, payload=None):
        """Call the ack controller method with a mocked request."""
        from odoo.addons.receipt_printer.controllers.main import ReceiptPrinterController
        ctrl = ReceiptPrinterController()

        headers = {'Content-Type': 'application/json'}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        body = json.dumps(payload or {}).encode()
        req = _build_mock_request(self.env, method='POST', data=body, headers=headers)
        with patch('odoo.addons.receipt_printer.controllers.main.request', req):
            return ctrl.ack()

    # --- pending_jobs tests ---

    def test_pending_jobs_happy_path(self):
        """Authenticated printer gets its pending jobs."""
        job = self.Job.create({
            'printer_id': self.printer.id,
            'payload': '{"text": "receipt"}',
        })
        resp = self._make_pending_jobs_request(api_key=self.printer.api_key)
        data = json.loads(resp.data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('jobs', data)
        self.assertEqual(len(data['jobs']), 1)
        self.assertEqual(data['jobs'][0]['id'], job.id)
        self.assertEqual(data['jobs'][0]['payload'], '{"text": "receipt"}')

    def test_pending_jobs_no_jobs(self):
        """Printer with no pending jobs returns empty list."""
        resp = self._make_pending_jobs_request(api_key=self.printer.api_key)
        data = json.loads(resp.data)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(data['jobs'], [])

    def test_pending_jobs_filters_by_printer(self):
        """Only jobs belonging to the authenticated printer are returned."""
        my_job = self.Job.create({
            'printer_id': self.printer.id,
            'payload': 'my job',
        })
        self.Job.create({
            'printer_id': self.other_printer.id,
            'payload': 'other job',
        })
        resp = self._make_pending_jobs_request(api_key=self.printer.api_key)
        data = json.loads(resp.data)
        self.assertEqual(len(data['jobs']), 1)
        self.assertEqual(data['jobs'][0]['id'], my_job.id)

    def test_pending_jobs_only_pending(self):
        """Only pending jobs are returned, not printed or failed ones."""
        pending = self.Job.create({
            'printer_id': self.printer.id,
            'payload': 'pending',
        })
        self.Job.create({
            'printer_id': self.printer.id,
            'payload': 'done',
            'state': 'printed',
        })
        resp = self._make_pending_jobs_request(api_key=self.printer.api_key)
        data = json.loads(resp.data)
        self.assertEqual(len(data['jobs']), 1)
        self.assertEqual(data['jobs'][0]['id'], pending.id)

    def test_pending_jobs_missing_auth(self):
        """Request without auth header returns 401."""
        resp = self._make_pending_jobs_request(api_key=None)
        data = json.loads(resp.data)
        self.assertEqual(resp.status_code, 401)

    def test_pending_jobs_invalid_auth(self):
        """Request with wrong api_key returns 401."""
        resp = self._make_pending_jobs_request(api_key='wrong-key')
        data = json.loads(resp.data)
        self.assertEqual(resp.status_code, 401)

    # --- ack tests ---

    def test_ack_printed_happy_path(self):
        """Ack a job as printed updates state and returns 200."""
        job = self.Job.create({
            'printer_id': self.printer.id,
            'payload': '{}',
        })
        resp = self._make_ack_request(
            api_key=self.printer.api_key,
            payload={'job_id': job.id, 'status': 'printed'},
        )
        self.assertEqual(resp.status_code, 200)
        job.invalidate_recordset(['state'])
        self.assertEqual(job.state, 'printed')

    def test_ack_failed_with_error_message(self):
        """Ack a job as failed with error message."""
        job = self.Job.create({
            'printer_id': self.printer.id,
            'payload': '{}',
        })
        resp = self._make_ack_request(
            api_key=self.printer.api_key,
            payload={'job_id': job.id, 'status': 'failed', 'error_message': 'Paper jam'},
        )
        self.assertEqual(resp.status_code, 200)
        job.invalidate_recordset(['state', 'error_message'])
        self.assertEqual(job.state, 'failed')
        self.assertEqual(job.error_message, 'Paper jam')

    def test_ack_wrong_printer(self):
        """Cannot ack a job belonging to another printer."""
        other_job = self.Job.create({
            'printer_id': self.other_printer.id,
            'payload': '{}',
        })
        resp = self._make_ack_request(
            api_key=self.printer.api_key,
            payload={'job_id': other_job.id, 'status': 'printed'},
        )
        self.assertIn(resp.status_code, (400, 403, 404))

    def test_ack_nonexistent_job(self):
        """Ack with nonexistent job_id returns 404."""
        resp = self._make_ack_request(
            api_key=self.printer.api_key,
            payload={'job_id': 999999, 'status': 'printed'},
        )
        self.assertIn(resp.status_code, (400, 404))

    def test_ack_missing_auth(self):
        """Ack without auth header returns 401."""
        resp = self._make_ack_request(api_key=None, payload={})
        data = json.loads(resp.data)
        self.assertEqual(resp.status_code, 401)

    def test_ack_invalid_auth(self):
        """Ack with wrong api_key returns 401."""
        resp = self._make_ack_request(api_key='wrong', payload={})
        data = json.loads(resp.data)
        self.assertEqual(resp.status_code, 401)
