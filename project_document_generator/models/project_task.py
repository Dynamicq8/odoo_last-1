# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime

_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    document_link_ids = fields.One2many(
        'project.document.pledge', 
        'task_id', 
        string='Project Documents',
        help="Links to various documents required for this project task."
    )

    def action_load_project_documents(self):
        """ Loads relevant Sign templates based on the project's building type """
        self.ensure_one()
        building_type = self.project_id.building_type if self.project_id else False

        if not building_type:
            raise UserError(_("Please set a 'Building Type' on the project first."))

        # Find Sign Templates that are marked as project documents and match the building type
        domain = [('is_project_document', '=', True), ('building_type', 'in', [building_type, 'all'])]
        templates = self.env['sign.template'].search(domain)
        
        existing_template_ids = self.document_link_ids.mapped('document_template_id').ids
        
        for template in templates:
            if template.id not in existing_template_ids:
                self.env['project.document.pledge'].create({
                    'task_id': self.id,
                    'document_template_id': template.id,
                })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _("Relevant documents loaded."),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_generate_project_documents(self):
        """ 
        Generates Sign Requests for all marked 'is_required' documents.
        """
        self.ensure_one()
        
        documents_to_generate = self.document_link_ids.filtered(lambda p: p.is_required)
        if not documents_to_generate:
            raise UserError(_("Please mark at least one document as 'Required/Ready' to generate."))

        project = self.project_id
        if not project:
            raise UserError(_("This task is not linked to a project."))
        
        if not project.partner_id:
            raise UserError(_("Cannot generate documents without a customer linked to the project. "
                              "Please assign a customer to the project first."))
        
        project_partner_id = project.partner_id.id

        # Define your replacements. Keys must match field names on the Sign Template.
        replacements = {
            'partner_name': project.partner_id.name or "",
            'date': datetime.date.today().strftime("%Y/%m/%d"), # YYYY/MM/DD
            'governorate': project.governorate_id.name if project.governorate_id else "",
            'region': project.region_id.name if project.region_id else "",
            'block_no': project.block_no or "",
            'plot_no': project.plot_no or "",
            'street_no': project.street_no or "",
            'project_name': project.name or "",
            'project_number': project.project_number or "", # Assuming you have this field on project
            # Add any other fields you want to auto-fill from your project model
        }

        # Get the default role for the signer (usually Customer/Partner)
        role_customer = self.env.ref('sign.sign_item_role_customer', raise_if_not_found=False)
        if not role_customer:
            _logger.error("Sign item role 'Customer' (sign.sign_item_role_customer) not found. "
                          "Ensure Odoo Sign module is correctly configured.")
            raise UserError(_("Error: 'Customer' role not found in Sign application. "
                              "Please check Sign app settings."))
        role_id = role_customer.id

        generated_requests = self.env['sign.request']

        for doc_link in documents_to_generate:
            # If a document is already generated for this line and not canceled, reuse it
            if doc_link.generated_sign_request_id and doc_link.generated_sign_request_id.state != 'canceled':
                generated_requests |= doc_link.generated_sign_request_id
                continue

            template = doc_link.document_template_id
            if not template:
                _logger.warning(f"Document link {doc_link.id} has no sign template assigned.")
                continue

            if not template.sign_item_ids:
                _logger.warning(f"Sign template '{template.name}' (ID: {template.id}) has no sign items defined. Skipping.")
                continue

            sign_request_items = []
            for item in template.sign_item_ids:
                if not item or not item.exists():
                    _logger.warning(f"Skipping invalid or missing sign item (ID: {item.id}) found in template '{template.name}'.")
                    continue

                item_vals = {
                    'role_id': role_id,
                    'sign_item_id': item.id,
                    'partner_id': project_partner_id, 
                }
                
                # Pre-fill if the item's name matches a key in replacements
                if item.name in replacements:
                    item_vals['value'] = str(replacements[item.name])
                
                sign_request_items.append((0, 0, item_vals))

            if not sign_request_items:
                _logger.warning(f"No valid sign request items could be prepared for template '{template.name}'. "
                                f"This might mean fields on the PDF are not correctly configured or named. Skipping.")
                continue

            try:
                sign_request = self.env['sign.request'].create({
                    'template_id': template.id,
                    'reference': f"{template.name} - {project.name}",
                    'request_item_ids': sign_request_items,
                    'state': 'sent', 
                })

                doc_link.generated_sign_request_id = sign_request.id
                generated_requests |= sign_request
            except Exception as e:
                _logger.error(f"Failed to create sign request for template '{template.name}' (ID: {template.id}). Error: {e}")
                raise UserError(_(f"Failed to create sign document for template '{template.name}'. "
                                  f"Please check the template settings and project details. Technical error: {e}"))

        if len(generated_requests) == 1:
            return generated_requests.go_to_document()
        elif len(generated_requests) > 1:
            return {
                'name': 'Generated Project Documents',
                'type': 'ir.actions.act_window',
                'res_model': 'sign.request',
                'view_mode': 'kanban,tree,form',
                'domain': [('id', 'in', generated_requests.ids)],
            }
        else:
            raise UserError(_("No sign documents were generated. Please ensure selected documents have valid templates and fields."))
