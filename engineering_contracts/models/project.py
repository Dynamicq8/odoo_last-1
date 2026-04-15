# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProjectProject(models.Model):
    _inherit = 'project.project'

    contract_ids = fields.One2many('engineering.contract', 'project_id', string='العقود (Contracts)')
    contract_count = fields.Integer(compute='_compute_contract_count', string='عدد العقود')

    @api.depends('contract_ids')
    def _compute_contract_count(self):
        for project in self:
            project.contract_count = len(project.contract_ids)

    def action_view_contracts(self):
        """View contracts related to this project"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Project Contracts'),
            'res_model': 'engineering.contract',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_building_type': self.building_type,
                'default_service_type': self.service_type,
            },
        }

    def action_create_contract(self):
        """Create a new contract for this project"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Contract'),
            'res_model': 'engineering.contract',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_project_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_building_type': self.building_type,
                'default_service_type': self.service_type,
                'default_plot_no': self.plot_no,
                'default_block_no': self.block_no,
                'default_area': self.area,
            },
        }
