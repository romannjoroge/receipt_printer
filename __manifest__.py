{
    'name': 'Receipt Printer',
    'version': '19.0.1.0.0',
    'summary': 'Send receipts directly to a USB thermal printer via a local agent',
    'description': """
        Send receipts directly to a USB thermal printer via a local print agent,
        bypassing the browser print dialog.
    """,
    'author': 'Jani',
    'category': 'Tools',
    'license': 'LGPL-3',
    'depends': ['base', 'point_of_sale'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/receipt_printer_printer_views.xml',
        'views/receipt_printer_job_views.xml',
        'views/pos_config_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
