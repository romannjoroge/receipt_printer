from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestReceiptPrinterSecurity(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Printer = self.env['receipt_printer.print.printer']
        self.Job = self.env['receipt_printer.print.job']

    def test_security_groups_exist(self):
        """Required security groups are defined."""
        user_group = self.env.ref('receipt_printer.group_printer_user')
        manager_group = self.env.ref('receipt_printer.group_printer_manager')
        self.assertTrue(user_group)
        self.assertTrue(manager_group)
        # Manager implies user
        self.assertIn(user_group, manager_group.implied_ids)

    def test_printer_access_rules_exist(self):
        """Access rules for printer model are defined."""
        rules = self.env['ir.rule'].search([
            ('model_id.model', '=', 'receipt_printer.print.printer'),
        ])
        # At minimum the model should be in ir.model.access
        access = self.env['ir.model.access'].search([
            ('model_id.model', '=', 'receipt_printer.print.printer'),
        ])
        self.assertTrue(access, "No access rules for printer model")

    def test_job_access_rules_exist(self):
        """Access rules for job model are defined."""
        access = self.env['ir.model.access'].search([
            ('model_id.model', '=', 'receipt_printer.print.job'),
        ])
        self.assertTrue(access, "No access rules for job model")

    def test_printer_user_has_read_write(self):
        """group_printer_user has read/write/create on printers."""
        access = self.env['ir.model.access'].search([
            ('model_id.model', '=', 'receipt_printer.print.printer'),
            ('group_id', '=', self.env.ref('receipt_printer.group_printer_user').id),
        ])
        self.assertTrue(access)
        self.assertTrue(access.perm_read)
        self.assertTrue(access.perm_write)
        self.assertTrue(access.perm_create)

    def test_job_user_has_read_write(self):
        """group_printer_user has read/write/create on jobs."""
        access = self.env['ir.model.access'].search([
            ('model_id.model', '=', 'receipt_printer.print.job'),
            ('group_id', '=', self.env.ref('receipt_printer.group_printer_user').id),
        ])
        self.assertTrue(access)
        self.assertTrue(access.perm_read)
        self.assertTrue(access.perm_write)
        self.assertTrue(access.perm_create)
