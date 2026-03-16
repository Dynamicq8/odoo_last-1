# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError # Import ValidationError too

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
        """ Creates Sign Requests by directly injecting items during creation (Odoo 17 fix) """
        self.ensure_one()
        _logger.info("Starting action_generate_commitments_pdf...")

        required_commitments = self.commitment_ids.filtered(lambda p: p.is_required)
        if not required_commitments:
            raise UserError(_("Please mark at least one commitment as 'Required' first. (يرجى تحديد تعهد واحد على الأقل كمطلوب)"))

        project = self.project_id
        if not project.partner_id:
            raise UserError(_("The project must have a Customer to generate documents. (يجب تحديد عميل للمشروع)"))

        role_customer = self.env.ref('sign.sign_item_role_customer', raise_if_not_found=False)
        if not role_customer:
            raise UserError(_("Error: The 'Customer' role could not be found in the Sign application. Please check its configuration."))
        _logger.info(f"Customer role ID: {role_customer.id if role_customer else 'Not found'}")


        # --- AUTOFILL DICTIONARY ---
        replacements = {
            'Name': project.partner_id.name or "",
            'Date': fields.Date.context_today(self).strftime("%Y/%m/%d"),
            'Governorate': project.governorate_id.name if hasattr(project, 'governorate_id') and project.governorate_id else "",
            'Region': project.region_id.name if hasattr(project, 'region_id') and project.region_id else "",
            'Block': project.block_no or "" if hasattr(project, 'block_no') else "",
            'Plot': project.plot_no or "" if hasattr(project, 'plot_no') else "",
            'Street': project.street_no or "" if hasattr(project, 'street_no') else "",
        }
        _logger.info(f"Autofill replacements prepared: {replacements}")

        generated_requests = self.env['sign.request']

        for commitment in required_commitments:
            _logger.info(f"Processing commitment for template: {commitment.sign_template_id.name} (ID: {commitment.sign_template_id.id})")
            
            # Skip if already generated and not canceled
            if commitment.sign_request_id and commitment.sign_request_id.state != 'canceled':
                generated_requests |= commitment.sign_request_id
                _logger.info(f"Skipping, request already exists: {commitment.sign_request_id.id}")
                continue

            template = commitment.sign_template_id
            if not template.sign_item_ids:
                raise UserError(_(f"Template '{template.name}' has no fields/signature configured. Please add them in the Sign app."))
            
            _logger.info(f"Template '{template.name}' has {len(template.sign_item_ids)} sign items.")

            # ==========================================
            # Build items BEFORE creating the sign.request
            # ==========================================
            request_item_vals_list = []
            
            for template_item in template.sign_item_ids:
                _logger.info(f"  - Processing template item: {template_item.name} (ID: {template_item.id})")
                
                # 1. Check if this specific item is assigned to the Customer role
                item_responsible_id = template_item.responsible_id.id if template_item.responsible_id else False
                partner_id = project.partner_id.id if item_responsible_id == role_customer.id else False
                
                # 2. Check if we have an auto-fill value for this field name
                value = replacements.get(template_item.name, "") if template_item.name else ""

                item_create_vals = {
                    'sign_item_type_id': template_item.type_id.id, # <--- Using 'sign_item_type_id' again for Odoo 17
                    'name': template_item.name,
                    'required': template_item.required,
                    'responsible_id': item_responsible_id, # Ensure responsible_id is always present if it exists
                    'partner_id': partner_id,
                    'page': template_item.page,
                    'posX': template_item.posX,
                    'posY': template_item.posY,
                    'width': template_item.width,
                    'height': template_item.height,
                    'value': str(value),
                    # IMPORTANT: For Odoo 17.0, do NOT include 'template_item_id' directly here unless
                    # you are absolutely certain your custom 'sign.request.item' model accepts it.
                    # It's usually inferred from template_id on the parent request, or through sign_item_type_id.
                }
                _logger.info(f"    - Prepared item create values: {item_create_vals}")
                request_item_vals_list.append((0, 0, item_create_vals))

            if not request_item_vals_list:
                raise UserError(_(f"After processing template items, no valid request items were prepared for '{template.name}'. This indicates a template configuration issue or an error in processing its items."))

            # ==========================================
            # Create the request WITH the items included
            # ==========================================
            sign_request_create_vals = {
                'template_id': template.id,
                'reference': f"{template.name} - {project.name}",
                'request_item_ids': request_item_vals_list, # Injecting items here is the goal
            }
            _logger.info(f"Attempting to create sign.request with values: {sign_request_create_vals}")
            
            try:
                sign_request = self.env['sign.request'].create(sign_request_create_vals)
                _logger.info(f"Successfully created sign request: {sign_request.id}")
            except ValidationError as e:
                _logger.error(f"Validation Error during sign request creation: {e}")
                raise UserError(_(f"Failed to create sign request due to validation error: {e.args[0]}"))
            except Exception as e:
                _logger.error(f"Unexpected Error during sign request creation: {e}", exc_info=True)
                raise UserError(_(f"An unexpected error occurred while creating the sign request. Please check server logs for details. Error: {e}"))

            # Send the request
            sign_request.action_sent()
            _logger.info(f"Sign request {sign_request.id} sent.")

            # Link document to the task line
            commitment.sign_request_id = sign_request.id
            generated_requests |= sign_request
            _logger.info(f"Commitment {commitment.id} linked to sign request {sign_request.id}")

        if not generated_requests:
            _logger.warning("No sign requests were generated.")
            return True

        _logger.info(f"Total generated requests: {generated_requests.ids}")
        # Open the generated documents for the user to see
        action = self.env['ir.actions.actions']._for_xml_id('sign.sign_request_action')
        if len(generated_requests) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': generated_requests.id,
                'views': [(False, 'form')],
            })
        else:
            action['domain'] = [('id', 'in', generated_requests.ids)]
        
        return action
