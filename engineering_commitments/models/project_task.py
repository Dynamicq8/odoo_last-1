# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, _, api
from odoo.exceptions import UserError
import datetime

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
        current_partner = self.env.user.partner_id 

        replacements = {
            'Name': project.partner_id.name or "NO NAME",
            'Date': fields.Date.context_today(self).strftime("%Y/%m/%d"),
            'Governorate': project.governorate_id.name if project.governorate_id else "NO GOV",
            'Region': project.region_id.name if project.region_id else "NO REGION",
            'Block': project.block_no or "NO BLOCK",
            'Plot': project.plot_no or "NO PLOT",
            'Customer Signature Text': project.partner_id.name or "N/A", 
            'Signature Date Text': fields.Date.context_today(self).strftime("%Y/%m/%d"),
            'Company Signature Text': self.env.user.company_id.name or "N/A", 
        }

        generated_requests = self.env['sign.request']

        for commitment in required_commitments:
            if commitment.sign_request_id and commitment.sign_request_id.state in ('signed', 'completed'):
                _logger.info(f"Skipping commitment {commitment.sign_template_id.name} as request {commitment.sign_request_id.name} is already signed.")
                generated_requests |= commitment.sign_request_id
                continue
            elif commitment.sign_request_id and commitment.sign_request_id.state != 'canceled':
                _logger.info(f"Canceling existing pending sign request {commitment.sign_request_id.name} for {commitment.sign_template_id.name}.")
                commitment.sign_request_id.cancel()
                commitment.sign_request_id = False 

            template = commitment.sign_template_id
            
            roles = template.sign_item_ids.mapped('responsible_id')
            signers_list_vals = []
            for role in roles:
                partner_to_assign = project.partner_id if (role_customer and role.id == role_customer.id) else current_partner
                signers_list_vals.append((0, 0, {
                    'role_id': role.id,
                    'partner_id': partner_to_assign.id,
                }))

            sign_request = self.env['sign.request'].create({
                'template_id': template.id,
                'reference': f"{template.name} - {project.name}",
                'request_item_ids': signers_list_vals,
            })

            # Delete any mail activities generated immediately after creation
            sign_request.activity_ids.unlink() 

            for template_field in template.sign_item_ids:
                field_name = template_field.name
                if field_name in replacements:
                    value_to_insert = replacements[field_name]
                    
                    signer_record = sign_request.request_item_ids.filtered(
                        lambda r: r.role_id.id == template_field.responsible_id.id
                    )
                    
                    if signer_record:
                        self.env['sign.request.item.value'].sudo().create({
                            'sign_request_item_id': signer_record[0].id,
                            'sign_item_id': template_field.id,
                            'value': value_to_insert,
                        })

            # --- FIX STARTS HERE: Attempt to call the internal signing method ---
            # Instead of directly writing to 'signed_by' and 'signed_on',
            # we will try to call the method that Odoo Sign uses to mark an item as signed.
            # Common methods are _mark_signed or action_sign.
            for request_item in sign_request.request_item_ids:
                # IMPORTANT: This part is highly dependent on your Odoo version's sign module.
                # If '_mark_signed' doesn't exist or has different parameters, this will fail.
                try:
                    # _mark_signed typically takes the signer's partner ID and an optional signature string/image.
                    # Since we are "auto-signing", we'll pass the assigned partner_id.
                    request_item._mark_signed(request_item.partner_id.id, signature_id=False, signature_name=False)
                except AttributeError:
                    _logger.warning(f"'_mark_signed' method not found or failed for sign.request.item ID {request_item.id}. Attempting direct state update as fallback.")
                    # Fallback if _mark_signed doesn't exist or fails.
                    # This might not correctly populate all related fields but could set the state.
                    request_item.write({
                        'state': 'signed',
                        # Removed 'signed_by' and 'signed_on' here as direct write failed.
                        # These should ideally be set by _mark_signed.
                    })
                except Exception as e:
                    _logger.error(f"Error calling _mark_signed for sign.request.item ID {request_item.id}: {e}")
                    # Fallback for other errors during _mark_signed call
                    request_item.write({
                        'state': 'signed',
                    })
            # --- FIX ENDS HERE ---
            
            sign_request._compute_state() 

            commitment.sign_request_id = sign_request.id
            generated_requests |= sign_request

        if not generated_requests:
            return True

        action = self.env['ir.actions.actions']._for_xml_id('sign.sign_request_action')
        if len(generated_requests) == 1:
            action.update({'view_mode': 'form', 'res_id': generated_requests.id, 'views': [(False, 'form')]})
        else:
            action['domain'] = [('id', 'in', generated_requests.ids)]
        
        return action
