# -*- coding: utf-8 -*-
from odoo import models, fields

# =========================================================
# 1. SIGN TEMPLATE EXTENSION (Added Document Type & Package)
# =========================================================
class SignTemplate(models.Model):
    _inherit = 'sign.template'

    document_type = fields.Selection([
        ('commitment', 'تعهد هندسي (Engineering Commitment)'),
        ('company_contract', 'عقد شركة (Company Contract)'),
        ('none', 'غير محدد (None)')
    ], string="Document Type (نوع المستند)", default='none', 
       help="Choose whether this is an Engineering Commitment or a Company Contract.")

    package_id = fields.Many2one('engineering.package', string="الباقة (Package)",
        help="If selected, this contract will only load for projects using this package.")

    building_type = fields.Selection([
        ('residential', 'سكن خاص'), 
        ('investment', 'استثماري'), 
        ('commercial', 'تجاري'), 
        ('industrial', 'صناعي'), 
        ('cooperative', 'جمعيات وتعاونيات'), 
        ('mosque', 'مساجد'), 
        ('hangar', 'مخازن / شبرات'), 
        ('farm', 'مزارع'), 
        ('all', 'جميع الأنواع')
    ], string="Building Type (نوع العقار)", default='all')
    
    service_type = fields.Selection([
        ('new_construction', 'بناء جديد'), 
        ('demolition', 'هدم'), 
        ('modification', 'تعديل'), 
        ('addition', 'اضافة'), 
        ('addition_modification', 'تعديل واضافة'), 
        ('supervision_only', 'إشراف هندسي فقط'), 
        ('renovation', 'ترميم'), 
        ('internal_partitions', 'قواطع داخلية'), 
        ('shades_garden', 'مظلات / حدائق'),
        ('all', 'جميع الأنواع') 
    ], string="Service Type (نوع الخدمة)", default='all')
