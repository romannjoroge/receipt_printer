import json

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestReceiptPrinterPosIntegration(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Printer = self.env['receipt_printer.print.printer']
        self.Job = self.env['receipt_printer.print.job']
        self.PosConfig = self.env['pos.config']
        self.printer = self.Printer.create({'name': 'POS Printer'})

    def test_pos_config_has_printer_field(self):
        """pos.config has a receipt_printer_printer_id field."""
        pos_config = self.PosConfig.create({
            'name': 'Test POS',
        })
        self.assertFalse(pos_config.receipt_printer_printer_id)
        pos_config.write({'receipt_printer_printer_id': self.printer.id})
        self.assertEqual(pos_config.receipt_printer_printer_id, self.printer)

    def test_create_receipt_job_from_order(self):
        """POS config method creates a print job from a sample order."""
        pos_config = self.PosConfig.create({
            'name': 'Test POS',
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
