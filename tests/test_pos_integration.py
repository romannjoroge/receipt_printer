import json

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestReceiptPrinterPosIntegration(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Printer = self.env['receipt_printer.print.printer']
        self.Job = self.env['receipt_printer.print.job']
        self.printer = self.Printer.create({'name': 'POS Printer'})

    def test_pos_config_has_printer_field(self):
        """pos.config has a receipt_printer_printer_id field."""
        field = self.env['pos.config']._fields.get('receipt_printer_printer_id')
        self.assertTrue(field, "receipt_printer_printer_id field not found on pos.config")
        self.assertEqual(field.comodel_name, 'receipt_printer.print.printer')

    def test_action_print_receipt_creates_job(self):
        """action_print_receipt creates a print job with correct payload."""
        # Use a new record with only the required fields to avoid POS setup
        pos_config = self.env['pos.config'].new({
            'receipt_printer_printer_id': self.printer.id,
        })
        order_data = {
            'orderlines': [
                {'product_name': 'Coffee', 'qty': 1, 'price': 3.50},
            ],
            'total': 3.50,
        }
        pos_config.action_print_receipt(order_data)

        jobs = self.Job.search([
            ('printer_id', '=', self.printer.id),
        ])
        self.assertEqual(len(jobs), 1)
        payload = json.loads(jobs[0].payload)
        self.assertIn('orderlines', payload)
        self.assertEqual(payload['total'], 3.50)
        self.assertEqual(jobs[0].state, 'pending')

    def test_action_print_receipt_no_printer(self):
        """action_print_receipt does nothing if no printer configured."""
        pos_config = self.env['pos.config'].new({
            'receipt_printer_printer_id': False,
        })
        pos_config.action_print_receipt({'total': 1.0})
        jobs = self.Job.search([])
        self.assertEqual(len(jobs), 0)
