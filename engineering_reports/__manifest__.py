{
    'name': "Engineering Site Visit Reports",
    'summary': "Manages site visit reports and WhatsApp sharing for project tasks.",
    'author': "Engineering Office",
    'website': "https://www.yourcompany.com",
    'category': 'Services/Engineering',
    'version': '19.0.1.0.0',
    'depends': [
        'engineering_core',
        'project',
        'engineering_project',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/engineering_site_visit_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}
