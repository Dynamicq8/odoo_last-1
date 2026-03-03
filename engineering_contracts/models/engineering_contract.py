# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import urllib.parse

class EngineeringContract(models.Model):
    _name = 'engineering.contract'
    _description = 'Engineering Contract'
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

    def _compute_access_url(self):
        super(EngineeringContract, self)._compute_access_url()
        for contract in self:
            contract.access_url = f'/my/contract/{contract.id}'

    # ---> THE FIX IS HERE: DYNAMIC TEXT REPLACEMENT <---
    @api.onchange('building_type', 'service_type', 'package_type', 'template_id', 'partner_id', 'contract_date', 'civil_number', 'plot_no', 'block_no', 'street_no', 'area')
    def _onchange_template(self):
        """Auto-select template and fill content dynamically."""
        if self.building_type and self.service_type and not self.template_id:
            template = self.env['engineering.contract.template'].get_template_for_contract(
                self.building_type, self.service_type, self.package_type
            )
            if template:
                self.template_id = template

        if self.template_id:
            # 1. Get the raw HTML from the template
            body = self.template_id.contract_body or ""
            terms = self.template_id.terms_conditions or ""

            # 2. Get the actual values (or leave a blank line if missing)
            customer_name = self.partner_id.name if self.partner_id else "__________________"
            c_date = self.contract_date.strftime('%Y/%m/%d') if self.contract_date else "____/____/____"
            civil = self.civil_number if self.civil_number else "__________________"
            plot = self.plot_no if self.plot_no else "____"
            block = self.block_no if self.block_no else "____"
            street = self.street_no if self.street_no else "____"
            c_area = self.area if self.area else "________________"
            amount = str(self.contract_amount) if self.contract_amount else "____"

            # 3. Replace the Placeholders in the HTML
            body = body.replace('{{customer_name}}', customer_name)
            body = body.replace('{{contract_date}}', c_date)
            body = body.replace('{{civil_number}}', civil)
            body = body.replace('{{plot_no}}', plot)
            body = body.replace('{{block_no}}', block)
            body = body.replace('{{street_no}}', street)
            body = body.replace('{{area}}', c_area)
            body = body.replace('{{amount}}', amount)

            terms = terms.replace('{{customer_name}}', customer_name)
            terms = terms.replace('{{contract_date}}', c_date)

            # 4. Set the final generated HTML into the fields
            self.contract_body = body
            self.terms_conditions = terms
            
    @api.onchange('project_id')
    def _onchange_project_id(self):
        """Auto-fill from project AND THEN load the template."""
        for rec in self:
            if rec.project_id and rec.project_id.sale_order_id:
                order = rec.project_id.sale_order_id
                rec.partner_id = order.partner_id
                rec.building_type = order.building_type
                rec.service_type = order.service_type
                rec.plot_no = order.plot_no
                rec.block_no = order.block_no
                rec.street_no = order.street_no
                rec.area = order.area
                rec.contract_amount = order.amount_total
                if order.partner_id:
                    rec.civil_number = order.partner_id.civil_number
                
                # Triggers the replacement function
                rec._onchange_template()

    # --- BUTTON ACTIONS ---

    def action_send_for_signature(self):
        self.ensure_one()
        if not self.contract_body:
            raise UserError(_("The contract body is empty! Please select a template or fill the content first."))
        self.state = 'sent'
        return self.action_send_whatsapp()

    def action_send_whatsapp(self):
        self.ensure_one()
        if not self.partner_id.phone and not self.partner_id.mobile:
            raise UserError(_("Customer phone number is missing."))
        
        self._portal_ensure_token() 
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        full_link = f"{base_url}{self.get_portal_url()}"
        
        phone = self.partner_id.mobile or self.partner_id.phone
        cleaned_phone = ''.join(filter(str.isdigit, phone))
        
        service_name = dict(self._fields['service_type'].selection).get(self.service_type, '')
        message = _("السلام عليكم %s،\nنرفق لكم عقد %s رقم %s للمراجعة والتوقيع.\nيرجى فتح الرابط التالي:\n%s") % (self.partner_id.name, service_name, self.name, full_link)
        
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://web.whatsapp.com/send?phone={cleaned_phone}&text={encoded_message}"
        
        return {'type': 'ir.actions.act_url', 'url': whatsapp_url, 'target': 'new'}

    def action_print_contract(self):
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
