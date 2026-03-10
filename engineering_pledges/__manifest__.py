{
    'name': "Engineering Pledges",
    'summary': "Manage Municipality Pledges (تعهدات البلدية)",
    'version': '1.0',
    'category': 'Services/Project',
    'depends': ['base', 'project'],
    'data': [
        'security/ir.model.access.csv',
        'views/pledge_template_views.xml',
    ],
    'installable': True,
    'application': False,
}
