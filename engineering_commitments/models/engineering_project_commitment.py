# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import urllib.parse
import re

# =========================================================
# HELPER FUNCTION FOR WHATSAPP
# =========================================================
def _action_send_whatsapp_direct(self):
    self.ensure_one()
    if not self.sign_request_id:
        raise UserError(_("لا يوجد مستند محدد بعد. يرجى توليد PDF أولاً.\n(No document generated yet. Please generate the PDF first.)"))

    request = self.sign_request_id
    partner = None

    if hasattr(self, 'project_id') and self.project_id:
        partner = self.project_id.partner_id
    elif hasattr(self, 'task_id') and self.task_id:
        partner = self.task_id.project_id.partner_id

    if not partner:
        partner = self.env.user.partner_id

    phone = (partner.mobile or partner.phone or '').strip()

    if not phone:
        phone = (self.env.user.partner_id.mobile or self.env.user.partner_id.phone or '').strip()

    if not phone:
        raise UserError(_("لا يوجد رقم هاتف مسجل للعميل.\nPlease set a mobile/phone number on the customer record."))

    phone_clean = re.sub(r'[\s\-\(\)]+', '', phone)
    if phone_clean.startswith('00'):
        phone_clean = '+' + phone_clean[2:]
    elif phone_clean.startswith('0'):
        phone_clean = '965' + phone_clean[1:]
    phone_clean = phone_clean.lstrip('+')

    request_item = request.request_item_ids.filtered(lambda r: r.partner_id.id == partner.id)
    if not request_item:
        request_item = request.request_item_ids[:1]

    if not request_item:
        raise UserError(_("No signer found on this sign request."))

    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '').rstrip('/')
    sign_url = f"{base_url}/sign/document/{request.id}/{request_item[0].access_token}"

    doc_name = request.reference or self.sign_template_id.name or _("المستند")
    message = (
        f"مرحباً {partner.name}،\n\n"
        f"يرجى مراجعة وتوقيع المستند التالي:\n"
        f"📄 {doc_name}\n\n"
        f"🔗 رابط التوقيع:\n{sign_url}\n\n"
        f"شكراً لتعاملكم معنا."
    )

    whatsapp_url = f"https://wa.me/{phone_clean}?text={urllib.parse.quote(message)}"

    return {
        'type': 'ir.actions.act_url',
        'url': whatsapp_url,
        'target': 'new',
    }


# =========================================================
# COMMITMENT MODEL FOR PROJECTS
# =========================================================
class EngineeringProjectCommitment(models.Model):
    _name = 'engineering.project.commitment'
    _description = 'Project Commitment'

    project_id = fields.Many2one('project.project', ondelete='cascade')
    sign_template_id = fields.Many2one('sign.template', required=True)
    sign_request_id = fields.Many2one('sign.request')
    is_required = fields.Boolean("Required")

    def action_send_whatsapp(self):
        return _action_send_whatsapp_direct(self)

    def action_sign_now(self):
        self.ensure_one()
        if not self.sign_request_id:
            raise UserError(_("No generated document yet."))
            
        request = self.sign_request_id
        user = self.env.user
        
        is_admin = user.has_group('base.group_system')
        is_secretary = bool(getattr(user, 'secretary_id', False))
        
        if is_admin or is_secretary:
            request_item = request.request_item_ids[:1]
        else:
            request_item = request.request_item_ids.filtered(
                lambda r: r.partner_id.id == user.partner_id.id
            )
            
        if not request_item:
            raise UserError(_("You are not assigned to sign this document."))
            
        return {
            'type': 'ir.actions.act_url',
            'url': f'/sign/document/{request.id}/{request_item[0].access_token}',
            'target': 'new',
        }

# =========================================================
# COMPANY CONTRACT MODEL FOR PROJECTS
# =========================================================
class EngineeringProjectCompanyContract(models.Model):
    _name = 'engineering.project.company.contract' 
    _description = 'Engineering Project Company Contract Line'

    project_id = fields.Many2one('project.project', string='Project', ondelete='cascade')
    sign_template_id = fields.Many2one('sign.template', string='Template', required=True)
    is_required = fields.Boolean(string='Required', default=False)
    sign_request_id = fields.Many2one('sign.request', string='Sign Request')

    def action_send_whatsapp(self):
        return _action_send_whatsapp_direct(self)

    def action_sign_now(self):
        self.ensure_one()
        if not self.sign_request_id:
            raise UserError(_("No generated document yet."))
            
        request = self.sign_request_id
        user = self.env.user
        
        is_admin = user.has_group('base.group_system')
        is_secretary = bool(getattr(user, 'secretary_id', False))
        
        if is_admin or is_secretary:
            request_item = request.request_item_ids[:1]
        else:
            request_item = request.request_item_ids.filtered(
                lambda r: r.partner_id.id == user.partner_id.id
            )
            
        if not request_item:
            raise UserError(_("You are not assigned to sign this document."))
            
        return {
            'type': 'ir.actions.act_url',
            'url': f'/sign/document/{request.id}/{request_item[0].access_token}',
            'target': 'new',
        }

# =========================================================
# PHASES APPROVAL MODEL FOR PROJECTS
# =========================================================
class EngineeringProjectPhaseApproval(models.Model):
    _name = 'engineering.project.phase.approval'
    _description = 'Engineering Project Phase Approval Line'

    project_id = fields.Many2one('project.project', string='Project', ondelete='cascade')
    sign_template_id = fields.Many2one('sign.template', string='Template', required=True)
    is_required = fields.Boolean(string='Required', default=False)
    sign_request_id = fields.Many2one('sign.request', string='Sign Request')

    def action_sign_now(self):
        self.ensure_one()
        if not self.sign_request_id:
            raise UserError(_("No generated document yet."))
            
        request = self.sign_request_id
        user = self.env.user
        
        is_admin = user.has_group('base.group_system')
        is_secretary = bool(getattr(user, 'secretary_id', False))
        
        if is_admin or is_secretary:
            request_item = request.request_item_ids[:1]
        else:
            request_item = request.request_item_ids.filtered(
                lambda r: r.partner_id.id == user.partner_id.id
            )
            
        if not request_item:
            raise UserError(_("You are not assigned to sign this document."))
            
        return {
            'type': 'ir.actions.act_url',
            'url': f'/sign/document/{request.id}/{request_item[0].access_token}',
            'target': 'new',
        }