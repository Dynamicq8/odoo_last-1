# -*- coding: utf-8 -*-
{
    'name': "Engineering Commitments",
    'summary': "Manage Municipality Commitments & Autofill PDFs via Sign App",
    'version': '1.0',
    'category': 'Services/Project',
    'depends': [
        'base',
        'sign',
        'project',
        'engineering_project', # Assuming your custom project fields are here
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/sign_template_views.xml',
        'views/project_task_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
