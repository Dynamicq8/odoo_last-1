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
        """ Loads Sign templates based on the project's building type """
        for task in self:
            # Assuming your project has a building_type field. If not, this acts as a safeguard.
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
        # Important: Reload the view to show the newly loaded commitments
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Commitments Loaded!"),
                'message': _("Templates have been successfully loaded."),
                'type': 'success',
                'sticky': False,
            }
        }


    def action_generate_commitments_pdf(self):
        """ Creates a Sign Request and Auto-fills the variables """
        self.ensure_one()

        required_commitments = self.commitment_ids.filtered(lambda p: p.is_required)
        if not required_commitments:
            raise UserError(_("Please mark at least one commitment as 'Required' first. (يرجى تحديد تعهد واحد على الأقل كمطلوب)"))

        project = self.project_id
        if not project.partner_id:
            raise UserError(_("The project must have a Customer to generate documents. (يجب تحديد عميل للمشروع)"))

        # --- AUTOFILL DICTIONARY ---
        # The KEYS here (left side) MUST match the "Name" you give the fields inside the Odoo Sign App!
        replacements = {
            'Name': project.partner_id.name or "",
            'Date': datetime.date.today().strftime("%Y/%m/%d"),
            'Governorate': project.governorate_id.name if hasattr(project, 'governorate_id') and project.governorate_id else "",
            'Region': project.region_id.name if hasattr(project, 'region_id') and project.region_id else "",
            'Block': project.block_no if hasattr(project, 'block_no') else "",
            'Plot': project.plot_no if hasattr(project, 'plot_no') else "",
            'Street': project.street_no if hasattr(project, 'street_no') else "",
        }

        # Find the default 'Customer' role for signing
        role_customer = self.env.ref('sign.sign_item_role_customer', raise_if_not_found=False)
        if not role_customer:
            raise UserError(_("Error: 'Customer' role not found in Sign application."))

        generated_requests = self.env['sign.request']

        for commitment in required_commitments:
            # Skip if already generated and not canceled
            if commitment.sign_request_id and commitment.sign_request_id.state != 'canceled':
                generated_requests |= commitment.sign_request_id
                continue

            template = commitment.sign_template_id
            if not template.sign_item_ids:
                _logger.warning(f"Template '{template.name}' has no sign items defined.")
                continue

            sign_request_items_vals = []
            for sign_item_template in template.sign_item_ids: # 'sign_item_template' is a sign.item record
                item_vals = {
                    'partner_id': project.partner_id.id,
                    'role_id': role_customer.id,
                    'type_id': sign_item_template.type_id.id, # Link to the sign.item.type (e.g., Signature, Text)
                    'name': sign_item_template.name,         # Crucial for matching auto-fill fields (e.g., "Name", "Date")
                    'x': sign_item_template.x,               # Copy position from template
                    'y': sign_item_template.y,               # Copy position from template
                    'width': sign_item_template.width,       # Copy size from template
                    'height': sign_item_template.height,     # Copy size from template
                    'page': sign_item_template.page,         # Copy page number
                }

                # If the field Name in the Sign App matches our dictionary, inject the data!
                if sign_item_template.name in replacements:
                    item_vals['value'] = str(replacements[sign_item_template.name])

                sign_request_items_vals.append((0, 0, item_vals))

            # Create the document
            sign_request = self.env['sign.request'].create({
                'template_id': template.id,
                'reference': f"{template.name} - {project.name}",
                'request_item_ids': sign_request_items_vals,
                'state': 'sent', # Mark as ready to be signed/viewed
            })

            # Link document to the task line
            commitment.sign_request_id = sign_request.id
            generated_requests |= sign_request

        # Return an action to open the generated Sign Requests
        if generated_requests:
            return {
                'name': _("Generated Commitments"),
                'type': 'ir.actions.act_window',
                'res_model': 'sign.request',
                'views': [[False, 'tree'], [False, 'form']],
                'domain': [('id', 'in', generated_requests.ids)],
                'context': {'active_id': self.id, 'active_model': self._name}, # Optional: pass context
                'target': 'current', # Opens in the current window (replaces task form)
            }
        # If no requests were generated (e.g., no required commitments), just close
        return {'type': 'ir.actions.act_window_close'}
