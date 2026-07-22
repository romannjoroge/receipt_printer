from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestReceiptPrinterSecurity(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Printer = self.env['receipt_printer.print.printer']
        self.Job = self.env['receipt_printer.print.job']

        # Create a user with no printer access
        self.user_no_access = self.env['res.users'].create({
            'name': 'No Access User',
            'login': 'no_access_printer',
            'password': 'test',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })

    def test_user_without_access_cannot_read_printers(self):
        """A user without printer group cannot read printers."""
        printer = self.Printer.create({'name': 'Test'})
        user_env = self.env['receipt_printer.print.printer'].with_user(
            self.user_no_access
        )
        # Should raise access error when trying to search/read
        with self.assertRaises(Exception):
            user_env.search([])

    def test_user_without_access_cannot_create_printer(self):
        """A user without printer group cannot create a printer."""
        user_env = self.env['receipt_printer.print.printer'].with_user(
            self.user_no_access
        )
        with self.assertRaises(Exception):
            user_env.create({'name': 'Hacker Printer'})

    def test_user_without_access_cannot_read_jobs(self):
        """A user without printer group cannot read jobs."""
        user_env = self.env['receipt_printer.print.job'].with_user(
            self.user_no_access
        )
        with self.assertRaises(Exception):
            user_env.search([])
