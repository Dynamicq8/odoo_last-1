{
    'name': "Engineering Core",
    'summary': "Adds shared fields and core logic for engineering consultancy modules.",
    'description': """
        This module is the base for all other engineering modules. It adds the following fields:
        - Building Type / Service Type
        - Location details (Governorate / Region)
        - Project tracking fields
    """,
    'author': "Engineering Office",
    'website': "https://www.yourcompany.com",
    'category': 'Services/Engineering',
    'version': '17.0.1.0.0',
    'depends': ['base', 'crm', 'sale_management', 'project'],
    'data': [
        # 1. Security file must be loaded first
        'security/ir.model.access.csv',
        
        # 2. Data files (Governorates and Regions)
        'data/kuwait_data.xml',
        
        # 3. View files
        'views/res_partner_views.xml',
        'views/crm_lead_views.xml',
        'views/sale_order_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}
