{
    'name': "Engineering Project Documents & WhatsApp Sender",
    'summary': "Manages document uploads and implements the WhatsApp redirect send feature.",
    'author': "Engineering Office",
    'category': 'Services/Engineering',
    'version': '19.0.1.0.0',
    'depends': [
        'engineering_core',
        'sale_management',
        'project',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/engineering_document_views.xml',
        'reports/engineering_reports.xml',
        'reports/engineering_report_templates.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}
