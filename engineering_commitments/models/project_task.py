# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, _, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    commitment_ids = fields.One2many(
        'engineering.task.commitment', 
        'task_id', 
        string='Engineering Commitments (التعهدات)'
    )

    def action_load_commitments(self):
        for task in self:
            building_type = getattr(task.project_id, 'building_type', False)
            if not building_type:
                domain = [('is_commitment', '=', True), ('building_type', '=', 'all')]
            else:
                domain = [('is_commitment', '=', True), ('building_type', 'in', [building_type, 'all'])]
            
            templates = self.env['sign.template'].search(domain)
            existing_template_ids = task.commitment_ids.mapped('sign_template_id.id')
            
            for template in templates:
                if template.id not in existing_template_ids:
                    self.env['engineering.task.commitment'].create({
                        'task_id': task.id,
                        'sign_template_id': template.id,
                    })

    def action_generate_commitments_pdf(self):
        self.ensure_one()

        required_commitments = self.commitment_ids.filtered(lambda p: p.is_required)
        if not required_commitments:
            raise UserError(_("Please mark at least one commitment as 'Required' first."))

        project = self.project_id
        if not project.partner_id:
            raise UserError(_("The project must have a Customer to generate documents."))

        role_customer = self.env.ref('sign.sign_item_role_customer', raise_if_not_found=False)

        # 1. GET VALUES FROM PROJECT
        replacements = {
            'Name': project.partner_id.name or "NO NAME",
            'Date': fields.Date.context_today(self).strftime("%Y/%m/%d"),
            'Governorate': project.governorate_id.name if project.governorate_id else "NO GOV",
            'Region': project.region_id.name if project.region_id else "NO REGION",
            'Block': project.block_no or "NO BLOCK",
            'Plot': project.plot_no or "NO PLOT",
        }

        generated_requests = self.env['sign.request']

        for commitment in required_commitments:
            if commitment.sign_request_id and commitment.sign_request_id.state != 'canceled':
                generated_requests |= commitment.sign_request_id
                continue

            template = commitment.sign_template_id
            
            # ==========================================
            # 2. BUILD THE ENTIRE DOCUMENT IN ONE SHOT
            # This is the most basic and compatible method.
            # ==========================================
            
            # Group fields by who is responsible for them (by role)
            fields_by_role = {}
            for field in template.sign_item_ids:
                role_id = field.responsible_id.id
                if role_id not in fields_by_role:
                    fields_by_role[role_id] = []
                fields_by_role[role_id].append(field)

            # Prepare the list of signers and their pre-filled values
            request_item_ids_vals = []
            for role_id, fields_in_role in fields_by_role.items():
                partner_id = project.partner_id.id if (role_customer and role_id == role_customer.id) else self.env.user.partner_id.id
                
                # For each signer, define which values to fill
                value_ids_vals = []
                for field in fields_in_role:
                    if field.name in replacements:
                        value_ids_vals.append((0, 0, {
                            'sign_item_id': field.id,
                            'value': replacements[field.name],
                        }))

                request_item_ids_vals.append((0, 0, {
                    'role_id': role_id,
                    'partner_id': partner_id,
                    'request_item_value_ids': value_ids_vals, # Nest the values inside the signer
                }))

            # 3. Create the sign request with all data pre-loaded
            sign_request = self.env['sign.request'].create({
                'template_id': template.id,
                'reference': f"{template.name} - {project.name}",
                'request_item_ids': request_item_ids_vals,
            })

            commitment.sign_request_id = sign_request.id
            generated_requests |= sign_request

        if not generated_requests:
            return True

        # 4. Open the document(s)
        action = self.env['ir.actions.actions']._for_xml_id('sign.sign_request_action')
        if len(generated_requests) == 1:
            action.update({'view_mode': 'form', 'res_id': generated_requests.id, 'views': [(False, 'form')]})
        else:
            action['domain'] = [('id', 'in', generated_requests.ids)]
        
        return action
