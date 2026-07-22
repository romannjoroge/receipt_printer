import json

from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestReceiptPrinterControllers(HttpCase):

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

    def _url(self, path):
        return f'/web{path}'

    def _auth_headers(self, api_key):
        return {'Authorization': f'Bearer {api_key}'}

    # --- pending_jobs tests ---

    def test_pending_jobs_happy_path(self):
        """Authenticated printer gets its pending jobs."""
        job = self.Job.create({
            'printer_id': self.printer.id,
            'payload': '{"text": "receipt"}',
        })
        resp = self.url_open(
            self._url('/receipt_printer/pending_jobs'),
            headers=self._auth_headers(self.printer.api_key),
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.text)
        self.assertIn('jobs', data)
        self.assertEqual(len(data['jobs']), 1)
        self.assertEqual(data['jobs'][0]['id'], job.id)
        self.assertEqual(data['jobs'][0]['payload'], '{"text": "receipt"}')

    def test_pending_jobs_no_jobs(self):
        """Printer with no pending jobs returns empty list."""
        resp = self.url_open(
            self._url('/receipt_printer/pending_jobs'),
            headers=self._auth_headers(self.printer.api_key),
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.text)
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
        resp = self.url_open(
            self._url('/receipt_printer/pending_jobs'),
            headers=self._auth_headers(self.printer.api_key),
        )
        data = json.loads(resp.text)
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
        resp = self.url_open(
            self._url('/receipt_printer/pending_jobs'),
            headers=self._auth_headers(self.printer.api_key),
        )
        data = json.loads(resp.text)
        self.assertEqual(len(data['jobs']), 1)
        self.assertEqual(data['jobs'][0]['id'], pending.id)

    def test_pending_jobs_missing_auth(self):
        """Request without auth header returns 401."""
        resp = self.url_open(
            self._url('/receipt_printer/pending_jobs'),
            expect_errors=True,
        )
        self.assertEqual(resp.status_code, 401)

    def test_pending_jobs_invalid_auth(self):
        """Request with wrong api_key returns 401."""
        resp = self.url_open(
            self._url('/receipt_printer/pending_jobs'),
            headers={'Authorization': 'Bearer wrong-key'},
            expect_errors=True,
        )
        self.assertEqual(resp.status_code, 401)

    # --- ack tests ---

    def test_ack_printed_happy_path(self):
        """Ack a job as printed updates state and returns 200."""
        job = self.Job.create({
            'printer_id': self.printer.id,
            'payload': '{}',
        })
        payload = json.dumps({
            'job_id': job.id,
            'status': 'printed',
        })
        resp = self.url_open(
            self._url('/receipt_printer/ack'),
            data=payload,
            headers={
                **self._auth_headers(self.printer.api_key),
                'Content-Type': 'application/json',
            },
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
        payload = json.dumps({
            'job_id': job.id,
            'status': 'failed',
            'error_message': 'Paper jam',
        })
        resp = self.url_open(
            self._url('/receipt_printer/ack'),
            data=payload,
            headers={
                **self._auth_headers(self.printer.api_key),
                'Content-Type': 'application/json',
            },
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
        payload = json.dumps({
            'job_id': other_job.id,
            'status': 'printed',
        })
        resp = self.url_open(
            self._url('/receipt_printer/ack'),
            data=payload,
            headers={
                **self._auth_headers(self.printer.api_key),
                'Content-Type': 'application/json',
            },
            expect_errors=True,
        )
        self.assertIn(resp.status_code, (400, 403, 404))

    def test_ack_nonexistent_job(self):
        """Ack with nonexistent job_id returns 404."""
        payload = json.dumps({
            'job_id': 999999,
            'status': 'printed',
        })
        resp = self.url_open(
            self._url('/receipt_printer/ack'),
            data=payload,
            headers={
                **self._auth_headers(self.printer.api_key),
                'Content-Type': 'application/json',
            },
            expect_errors=True,
        )
        self.assertIn(resp.status_code, (400, 404))

    def test_ack_missing_auth(self):
        """Ack without auth header returns 401."""
        resp = self.url_open(
            self._url('/receipt_printer/ack'),
            data='{}',
            expect_errors=True,
        )
        self.assertEqual(resp.status_code, 401)

    def test_ack_invalid_auth(self):
        """Ack with wrong api_key returns 401."""
        resp = self.url_open(
            self._url('/receipt_printer/ack'),
            data='{}',
            headers={'Authorization': 'Bearer wrong'},
            expect_errors=True,
        )
        self.assertEqual(resp.status_code, 401)
