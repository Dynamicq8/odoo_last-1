# -*- coding: utf-8 -*-
from odoo import models, fields, api

# 1. The Checklist Line Model
class EngineeringProjectPledge(models.Model):
    _name = 'engineering.project.pledge'
    _description = 'Project Municipality Pledge'

    project_id = fields.Many2one('project.project', string='Project', ondelete='cascade')
    template_id = fields.Many2one('engineering.pledge.template', string='نوع التعهد (Pledge Type)', required=True)
    
    # Checkbox for the secretary
    is_completed = fields.Boolean(string='متوفر / تم التوقيع (Completed)', default=False)
    
    # We will use this in Phase 3 for the PDF
    generated_html = fields.Html(string='Generated Content')


# 2. Add the Checklist to the Project Model
class ProjectProject(models.Model):
    _inherit = 'project.project'

    pledge_ids = fields.One2many('engineering.project.pledge', 'project_id', string='تعهدات البلدية (Pledges)')

    def action_load_required_pledges(self):
        """ Magic Button: Loads pledges based on the project's building type """
        for project in self:
            # Find templates that match the project's building type (or 'all')
            domain = [('active', '=', True)]
            if project.building_type:
                domain.append(('building_type', 'in', [project.building_type, 'all']))
            
            templates = self.env['engineering.pledge.template'].search(domain)
            
            # Find what is already in the list so we don't create duplicates
            existing_template_ids = project.pledge_ids.mapped('template_id.id')
            
            # Add missing templates to the checklist
            for template in templates:
                if template.id not in existing_template_ids:
                    self.env['engineering.project.pledge'].create({
                        'project_id': project.id,
                        'template_id': template.id,
                    })
