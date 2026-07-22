from odoo import fields
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestReceiptPrinterJob(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Printer = self.env['receipt_printer.print.printer']
        self.Job = self.env['receipt_printer.print.job']
        self.printer = self.Printer.create({'name': 'Test Printer'})

    def test_create_job(self):
        """A job can be created with required fields."""
        job = self.Job.create({
            'printer_id': self.printer.id,
            'payload': '{"text": "Hello"}',
        })
        self.assertEqual(job.printer_id, self.printer)
        self.assertEqual(job.payload, '{"text": "Hello"}')
        self.assertEqual(job.state, 'pending')
        self.assertFalse(job.error_message)
        self.assertFalse(job.printed_date)

    def test_mark_printed_from_pending(self):
        """A pending job can be marked as printed."""
        job = self.Job.create({
            'printer_id': self.printer.id,
            'payload': '{}',
        })
        job.action_mark_printed()
        self.assertEqual(job.state, 'printed')
        self.assertTrue(job.printed_date)

    def test_mark_printed_from_sent(self):
        """A sent job can be marked as printed."""
        job = self.Job.create({
            'printer_id': self.printer.id,
            'payload': '{}',
        })
        job.write({'state': 'sent'})
        job.action_mark_printed()
        self.assertEqual(job.state, 'printed')
        self.assertTrue(job.printed_date)

    def test_mark_printed_from_printed_raises(self):
        """Cannot mark an already printed job as printed."""
        job = self.Job.create({
            'printer_id': self.printer.id,
            'payload': '{}',
        })
        job.action_mark_printed()
        with self.assertRaises(ValidationError):
            job.action_mark_printed()

    def test_mark_printed_from_failed_raises(self):
        """Cannot mark a failed job as printed."""
        job = self.Job.create({
            'printer_id': self.printer.id,
            'payload': '{}',
        })
        job.action_mark_failed('Paper jam')
        with self.assertRaises(ValidationError):
            job.action_mark_printed()

    def test_mark_failed_from_pending(self):
        """A pending job can be marked as failed."""
        job = self.Job.create({
            'printer_id': self.printer.id,
            'payload': '{}',
        })
        job.action_mark_failed('Connection timeout')
        self.assertEqual(job.state, 'failed')
        self.assertEqual(job.error_message, 'Connection timeout')

    def test_mark_failed_from_sent(self):
        """A sent job can be marked as failed."""
        job = self.Job.create({
            'printer_id': self.printer.id,
            'payload': '{}',
        })
        job.write({'state': 'sent'})
        job.action_mark_failed('Printer offline')
        self.assertEqual(job.state, 'failed')
        self.assertEqual(job.error_message, 'Printer offline')

    def test_mark_failed_from_failed_raises(self):
        """Cannot mark an already failed job as failed."""
        job = self.Job.create({
            'printer_id': self.printer.id,
            'payload': '{}',
        })
        job.action_mark_failed('Error 1')
        with self.assertRaises(ValidationError):
            job.action_mark_failed('Error 2')

    def test_mark_failed_from_printed_raises(self):
        """Cannot mark a printed job as failed."""
        job = self.Job.create({
            'printer_id': self.printer.id,
            'payload': '{}',
        })
        job.action_mark_printed()
        with self.assertRaises(ValidationError):
            job.action_mark_failed('Should not work')
