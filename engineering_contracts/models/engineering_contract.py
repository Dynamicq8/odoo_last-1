# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import urllib.parse

class EngineeringContract(models.Model):
    _name = 'engineering.contract'
    _description = 'Engineering Contract'
    # ADDED 'portal.mixin' here so we can generate web links
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='رقم العقد (Contract Number)', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    
    project_id = fields.Many2one('project.project', string='المشروع (Project)', ondelete='cascade', tracking=True)
    sale_order_id = fields.Many2one('sale.order', string='عرض السعر (Quotation)', related='project_id.sale_order_id', store=True)
    partner_id = fields.Many2one('res.partner', string='العميل (Customer)', required=True, tracking=True)
    
    building_type = fields.Selection([('residential', 'سكن خاص'), ('investment', 'استثماري'), ('commercial', 'تجاري'), ('industrial', 'صناعي'), ('cooperative', 'جمعيات وتعاونيات'), ('mosque', 'مساجد'), ('hangar', 'مخازن / شبرات'), ('farm', 'مزارع'), ('garden', 'حدائق'), ('shades', 'مظلات')], string="نوع المبنى", required=True, tracking=True)
    service_type = fields.Selection([('new_construction', 'بناء جديد'), ('demolition', 'هدم'), ('modification', 'تعديل'), ('extension', 'توسعة'), ('extension_modification', 'تعديل وتوسعة'), ('supervision_only', 'إشراف هندسي فقط'), ('renovation', 'ترميم'), ('internal_partitions', 'قواطع داخلية'), ('shades_garden', 'مظلات / حدائق')], string="نوع الخدمة", required=True, tracking=True)
    package_type = fields.Selection([('basic', 'الباقة الأساسية'), ('premium', 'الباقة المميزة'), ('gold', 'الباقة الذهبية'), ('supervision', 'باقة الإشراف')], string="نوع الباقة", tracking=True)

    plot_no = fields.Char(string="رقم القسيمة (Plot)")
    block_no = fields.Char(string="القطعة (Block)")
    street_no = fields.Char(string="الشارع (Street)")
    area = fields.Char(string="المنطقة (Area)")
    civil_number = fields.Char(string="الرقم المدني (Civil ID)")

    template_id = fields.Many2one('engineering.contract.template', string='قالب العقد (Contract Template)')
    contract_body = fields.Html(string='محتوى العقد (Contract Body)', sanitize=False)
    terms_conditions = fields.Html(string='الشروط والأحكام (Terms & Conditions)')
    
    contract_amount = fields.Monetary(string='قيمة العقد (Contract Amount)', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    
    contract_date = fields.Date(string='تاريخ العقد (Contract Date)', default=fields.Date.today)
    start_date = fields.Date(string='تاريخ البدء (Start Date)')
    end_date = fields.Date(string='تاريخ الانتهاء (End Date)')
    
    state = fields.Selection([('draft', 'مسودة'), ('sent', 'مرسل للتوقيع'), ('signed', 'موقع'), ('active', 'نشط'), ('completed', 'مكتمل'), ('cancelled', 'ملغي')], string='الحالة', default='draft', tracking=True)

    signed_document = fields.Binary(string='العقد الموقع (Signed Contract)', attachment=True)
    signed_document_name = fields.Char(string='اسم الملف (Filename)')
    signature_date = fields.Datetime(string='تاريخ التوقيع (Signature Date)')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('engineering.contract') or _('New')
        return super().create(vals_list)

    # PORTAL ROUTE LINK GENERATOR
    def _compute_access_url(self):
        super(EngineeringContract, self)._compute_access_url()
        for contract in self:
            contract.access_url = f'/my/contract/{contract.id}'

    @api.onchange('project_id')
    def _onchange_project_id(self):
        """ FIXED AUTO-FILL: Pulls data accurately when a Project is chosen """
        for rec in self:
            if rec.project_id:
                rec.partner_id = rec.project_id.partner_id
                
                # Try getting data from Quotation first
                if rec.project_id.sale_order_id:
                    order = rec.project_id.sale_order_id
                    rec.building_type = order.building_type
                    rec.service_type = order.service_type
                    rec.plot_no = order.plot_no
                    rec.block_no = order.block_no
                    rec.street_no = order.street_no
                    rec.area = order.area
                    rec.contract_amount = order.amount_total
                    if order.partner_id:
                        rec.civil_number = order.partner_id.civil_number
                else:
                    # Fallback: if project was created manually without a quotation
                    if hasattr(rec.project_id, 'building_type'): rec.building_type = rec.project_id.building_type
                    if hasattr(rec.project_id, 'service_type'): rec.service_type = rec.project_id.service_type

    def action_send_for_signature(self):
        """ Changes state to sent and opens WhatsApp with Portal Link """
        self.state = 'sent'
        return self.action_send_whatsapp()

    def action_send_whatsapp(self):
        """ Generates the Portal Link and opens WhatsApp Web """
        self.ensure_one()
        if not self.partner_id.phone and not self.partner_id.mobile:
            raise UserError(_("Customer phone number is missing (رقم هاتف العميل غير موجود)."))
        
        # 1. Ensure the contract has a secure web token for the portal link
        self._portal_ensure_token() 
        
        # 2. Get the Base URL (e.g. https://mazen41-odoo-last.odoo.com)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        full_link = f"{base_url}{self.get_portal_url()}"
        
        # 3. Clean the phone number
        phone = self.partner_id.mobile or self.partner_id.phone
        cleaned_phone = ''.join(filter(str.isdigit, phone))
        
        # 4. Get Arabic Service Type Name safely
        service_dict = dict(self._fields['service_type'].selection)
        service_name = service_dict.get(self.service_type, '')
        
        # 5. Create message with Portal Link
        message = _("السلام عليكم %s،\nنرفق لكم عقد %s رقم %s للمراجعة والتوقيع.\nيرجى فتح الرابط التالي:\n%s") % (
            self.partner_id.name, service_name, self.name, full_link
        )
        
        # 6. Encode and send
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://web.whatsapp.com/send?phone={cleaned_phone}&text={encoded_message}"
        
        return {'type': 'ir.actions.act_url', 'url': whatsapp_url, 'target': 'new'}

    def action_print_contract(self):
        """ Print contract PDF """
        return self.env.ref('engineering_contracts.action_report_engineering_contract').report_action(self)

    def action_mark_signed(self):
        self.write({'state': 'signed', 'signature_date': fields.Datetime.now()})
        return True

    def action_activate(self):
        self.state = 'active'
        return True

    def action_complete(self):
        self.state = 'completed'
        return True

    def action_cancel(self):
        self.state = 'cancelled'
        return True

    def action_reset_to_draft(self):
        self.state = 'draft'
        return True
