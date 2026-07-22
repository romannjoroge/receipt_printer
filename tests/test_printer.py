from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestReceiptPrinterPrinter(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Printer = self.env['receipt_printer.print.printer']

    def test_create_printer(self):
        """A printer can be created with required fields."""
        printer = self.Printer.create({
            'name': 'Kitchen Printer',
            'connection_type': 'usb',
            'identifier': '0x0456:0x0808',
        })
        self.assertEqual(printer.name, 'Kitchen Printer')
        self.assertEqual(printer.connection_type, 'usb')
        self.assertEqual(printer.identifier, '0x0456:0x0808')
        self.assertTrue(printer.active)

    def test_connection_type_default_usb(self):
        """Default connection_type is usb."""
        printer = self.Printer.create({'name': 'Test'})
        self.assertEqual(printer.connection_type, 'usb')

    def test_state_offline_when_no_last_seen(self):
        """State is offline when last_seen is not set."""
        printer = self.Printer.create({'name': 'Test'})
        self.assertEqual(printer.state, 'offline')

    def test_state_online_when_recently_seen(self):
        """State is online when last_seen is within 60 seconds."""
        printer = self.Printer.create({'name': 'Test'})
        printer.write({'last_seen': fields.Datetime.now()})
        printer.invalidate_recordset(['state'])
        self.assertEqual(printer.state, 'online')

    def test_state_offline_when_not_recently_seen(self):
        """State is offline when last_seen is older than 60 seconds."""
        printer = self.Printer.create({'name': 'Test'})
        old_time = fields.Datetime.now() - timedelta(seconds=120)
        printer.write({'last_seen': old_time})
        printer.invalidate_recordset(['state'])
        self.assertEqual(printer.state, 'offline')

    def test_api_key_generated(self):
        """A printer gets a unique api_key on creation."""
        p1 = self.Printer.create({'name': 'P1'})
        p2 = self.Printer.create({'name': 'P2'})
        self.assertTrue(p1.api_key)
        self.assertTrue(p2.api_key)
        self.assertNotEqual(p1.api_key, p2.api_key)
