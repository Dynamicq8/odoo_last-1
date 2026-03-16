# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProjectDocumentPledge(models.Model):
    _name = 'project.document.pledge' 
    _description = 'Project Document Link'

    task_id = fields.Many2one('project.task', string='Task', ondelete='cascade', required=True)
    document_template_id = fields.Many2one(
        'sign.template', 
        string='Document Template', 
        required=True, 
        domain=[('is_project_document', '=', True)],
        help="Select the Sign Template for this document."
    )
    is_required = fields.Boolean(string='Required/Ready', default=False, 
                                 help="Mark if this document is required or ready for generation.")
    
    generated_sign_request_id = fields.Many2one(
        'sign.request', 
        string='Generated Document', 
        readonly=True,
        help="The actual Sign Request document generated from this line."
    )

    @api.depends('document_template_id.name')
    def _compute_name(self):
        for record in self:
            record.name = record.document_template_id.name if record.document_template_id else "New Document Link"

    name = fields.Char(string="Document Name", compute=_compute_name, store=True)

    _sql_constraints = [
        ('unique_template_per_task', 'unique(task_id, document_template_id)', 'A specific document template can only be linked once per task.')
    ]
