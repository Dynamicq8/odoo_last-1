# -*- coding: utf-8 -*-
from odoo import models, fields

class EngineeringPledgeTemplate(models.Model):
    _name = 'engineering.pledge.template'
    _description = 'Municipality Pledge Template'
    _order = 'sequence, id'

    name = fields.Char(string='اسم التعهد (Pledge Name)', required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    building_type = fields.Selection([
        ('residential', 'سكن خاص'), ('investment', 'استثماري'), 
        ('commercial', 'تجاري'), ('industrial', 'صناعي'), 
        ('cooperative', 'جمعيات وتعاونيات'), ('mosque', 'مساجد'), 
        ('hangar', 'مخازن / شبرات'), ('farm', 'مزارع'), ('all', 'جميع الأنواع')
    ], string="نوع العقار المرتبط", required=True, default='all')

    body_html = fields.Html(string='نص التعهد (Pledge Body)', sanitize=False)
