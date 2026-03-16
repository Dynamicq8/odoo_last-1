# -*- coding: utf-8 -*-
from odoo import models, fields

class SignTemplate(models.Model):
    _inherit = 'sign.template'

    building_type = fields.Selection([
        ('residential', 'سكن خاص'), ('investment', 'استثماري'), 
        ('commercial', 'تجاري'), ('industrial', 'صناعي'), 
        ('cooperative', 'جمعيات وتعاونيات'), ('mosque', 'مساجد'), 
        ('hangar', 'مخازن / شبرات'), ('farm', 'مزارع'), ('all', 'جميع الأنواع')
    ], string="Building Type (نوع العقار)", default='all')
    
    is_commitment = fields.Boolean(string="Is Engineering Commitment? (تعهد هندسي؟)", default=False)
