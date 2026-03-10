# -*- coding: utf-8 -*-
from odoo import models, fields, api

# ==========================================================
#  1. THE CHECKLIST LINE MODEL (Now links to a Task)
# ==========================================================
class EngineeringTaskPledge(models.Model):
    _name = 'engineering.task.pledge' # Renamed for clarity
    _description = 'Task Municipality Pledge'

    # The link is now to a Task, not a Project
    task_id = fields.Many2one('project.task', string='Task', ondelete='cascade')
    
    template_id = fields.Many2one('engineering.pledge.template', string='نوع التعهد (Pledge Type)', required=True)
    is_completed = fields.Boolean(string='متوفر / تم التوقيع (Completed)', default=False)
    generated_html = fields.Html(string='Generated Content')

# ==========================================================
#  2. ADD THE CHECKLIST TO THE **TASK** MODEL
# ==========================================================
class ProjectTask(models.Model):
    _inherit = 'project.task'
    stage_sequence = fields.Integer(related='stage_id.sequence', readonly=True)

    # The One2many field is now on the Task
    pledge_ids = fields.One2many('engineering.task.pledge', 'task_id', string='تعهدات البلدية (Pledges)')

    def action_load_required_pledges(self):
        """ Magic Button: Loads pledges based on the parent project's building type """
        for task in self:
            # Get the building type from the parent project
            building_type = task.project_id.building_type
            if not building_type:
                continue

            # Find templates that match the project's building type (or 'all')
            domain = [('active', '=', True), ('building_type', 'in', [building_type, 'all'])]
            templates = self.env['engineering.pledge.template'].search(domain)
            
            # Find what is already in the list so we don't create duplicates
            existing_template_ids = task.pledge_ids.mapped('template_id.id')
            
            # Add missing templates to the checklist
            for template in templates:
                if template.id not in existing_template_ids:
                    self.env['engineering.task.pledge'].create({
                        'task_id': task.id,
                        'template_id': template.id,
                    })
