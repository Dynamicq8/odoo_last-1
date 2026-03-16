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
        """ Loads Sign templates based on the project's building type """
        for task in self:
            building_type = task.project_id.building_type if hasattr(task.project_id, 'building_type') else False
            
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
        """ Creates Sign Requests and auto-fills variables for required commitments. """
        self.ensure_one()

        required_commitments = self.commitment_ids.filtered(lambda p: p.is_required)
        if not required_commitments:
            raise UserError(_("Please mark at least one commitment as 'Required' first. (يرجى تحديد تعهد واحد على الأقل كمطلوب)"))

        project = self.project_id
        if not project.partner_id:
            raise UserError(_("The project must have a Customer to generate documents. (يجب تحديد عميل للمشروع)"))

        role_customer = self.env.ref('sign.sign_item_role_customer', raise_if_not_found=False)
        if not role_customer:
            raise UserError(_("Error: The 'Customer' role could not be found in the Sign application. Please check its configuration."))

        replacements = {
            'Name': project.partner_id.name or "",
            'Date': fields.Date.context_today(self).strftime("%Y/%m/%d"),
            'Governorate': project.governorate_id.name if hasattr(project, 'governorate_id') and project.governorate_id else "",
            'Region': project.region_id.name if hasattr(project, 'region_id') and project.region_id else "",
            'Block': project.block_no or "" if hasattr(project, 'block_no') else "",
            'Plot': project.plot_no or "" if hasattr(project, 'plot_no') else "",
            'Street': project.street_no or "" if hasattr(project, 'street_no') else "",
        }

        generated_requests = self.env['sign.request']

        for commitment in required_commitments:
            if commitment.sign_request_id and commitment.sign_request_id.state != 'canceled':
                generated_requests |= commitment.sign_request_id
                continue

            template = commitment.sign_template_id
            
            _logger.info(f"Processing commitment for template: {template.name} (ID: {template.id})")
            _logger.info(f"Number of sign items on template before creating request: {len(template.sign_item_ids)}")

            if not template.sign_item_ids:
                _logger.warning(f"Template '{template.name}' has no sign items defined. This commitment will be skipped.")
                continue

            # 1. Create the Sign Request from the template.
            sign_request = self.env['sign.request'].create({
                'template_id': template.id,
                'reference': f"{template.name} - {project.name}",
            })
            
            _logger.info(f"Created sign request {sign_request.id} from template {template.name}.")
            _logger.info(f"Number of request items on the NEWLY CREATED sign request: {len(sign_request.request_item_ids)}")

            # --- CRITICAL CHECK FOR THIS ERROR ---
            if not sign_request.request_item_ids:
                _logger.error(
                    f"Validation Error: Sign request {sign_request.id} (from template '{template.name}') "
                    f"has NO items after creation. This will cause the 'A valid sign request needs at least one sign request item' error. "
                    f"Please double-check the template's PDF attachment and fields in the Sign app. "
                    f"Deleting the empty sign request and skipping this commitment."
                )
                sign_request.unlink() # Clean up the empty request
                continue # Skip to the next commitment

            # 2. Assign the partner to the items with the 'Customer' role.
            customer_items = sign_request.request_item_ids.filtered(
                lambda item: item.role_id.id == role_customer.id
            )
            if customer_items:
                customer_items.write({'partner_id': project.partner_id.id})
            else:
                _logger.warning(f"No customer-assigned items found for sign request {sign_request.id}.")

            # 3. Loop through items to fill values.
            for item in sign_request.request_item_ids:
                if item.name and item.name in replacements:
                    item.write({'value': replacements[item.name]})

            # 4. Send the request.
            sign_request.action_sent()

            commitment.sign_request_id = sign_request.id
            generated_requests |= sign_request

        if not generated_requests:
            _logger.info("No sign requests were generated.")
            return True

        action = self.env['ir.actions.actions']._for_xml_id('sign.sign_request_action')
        
        if len(generated_requests) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': generated_requests.id,
                'views': [(False, 'form')],
            })
        else:
            action['domain'] = [('id', 'in', generated_requests.ids)]
        
        _logger.info(f"Returning action for generated requests: {generated_requests.ids}")
        return action
