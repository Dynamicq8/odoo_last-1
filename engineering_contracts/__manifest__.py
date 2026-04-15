{
    'name': "Engineering Contracts Management",
    'summary': "Complete contract management system for engineering office with building type templates.",
    'description': """
        نظام إدارة العقود الهندسية
        ===========================
        - إنشاء عقود مرتبطة بالمشروع والعميل ونوع المبنى والباقة
        - تصنيف العقود حسب نوع المبنى (سكن خاص، تجاري، استثماري، صناعي...)
        - قوالب عقود جاهزة لكل نوع مبنى وخدمة
        - إرسال العقود للتوقيع إلكترونياً
        - حفظ نسخة العقد بعد التوقيع داخل المشروع
        - إرسال رابط التوقيع عبر WhatsApp
    """,
    'author': "Engineering Office",
    'website': "https://www.yourcompany.com",
    'category': 'Services/Engineering',
    'version': '19.0.1.0.0',
    'depends': [
        'engineering_core',
        'engineering_quotation',
        'project',
        'sale_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/contract_template_data.xml',
        'views/engineering_contract_views.xml',
        'views/engineering_contract_template_views.xml',
        'views/project_views.xml',
        'views/menu_views.xml',
        'report/contract_report.xml',
        'report/contract_templates.xml',
            'views/portal_contract_templates.xml', # <--- ADD THIS

    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}
