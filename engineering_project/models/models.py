# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import urllib.parse

class ProjectProject(models.Model):
    _inherit = 'project.project'

    sale_order_id = fields.Many2one('sale.order', string='Source Quotation', readonly=True)
    
    building_type = fields.Selection([
        ('residential', 'سكن خاص'), ('investment', 'استثماري'), 
        ('commercial', 'تجاري'), ('industrial', 'صناعي'), 
        ('cooperative', 'جمعيات وتعاونيات'), ('mosque', 'مساجد'), 
        ('hangar', 'مخازن / شبرات'), ('farm', 'مزارع')
    ], string="نوع المبنى")

    service_type = fields.Selection([
        ('new_construction', 'بناء جديد'), ('demolition', 'هدم'), 
        ('modification', 'تعديل'), ('addition', 'اضافة'), 
        ('addition_modification', 'تعديل واضافة'), ('supervision_only', 'إشراف هندسي فقط'), 
        ('renovation', 'ترميم'), ('internal_partitions', 'قواطع داخلية'), 
        ('shades_garden', 'مظلات / حدائق')
    ], string="نوع الخدمة")
    
    region = fields.Char(string="المنطقة (Region)")
    plot_no = fields.Char(string="رقم القسيمة")
    block_no = fields.Char(string="القطعة")
    street_no = fields.Char(string="الشارع")
    area = fields.Char(string="المساحة (Area)")

    # --- WE KEEP THESE HERE SILENTLY SO ODOO DOES NOT CRASH ---
    floor_basement = fields.Text(string="أولاً السرداب")
    floor_ground = fields.Text(string="ثانياً الدور الأرضي")
    floor_first = fields.Text(string="الدور الأول")
    floor_second = fields.Text(string="الدور الثاني")
    floor_roof = fields.Text(string="الدور السطح")


class ProjectTask(models.Model):
    _inherit = 'project.task'

    # --- THESE ARE THE REAL FIELDS YOU WILL FILL OUT IN THE TASK ---
    floor_basement = fields.Text(string="أولاً السرداب")
    floor_ground = fields.Text(string="ثانياً الدور الأرضي")
    floor_first = fields.Text(string="الدور الأول")
    floor_second = fields.Text(string="الدور الثاني")
    floor_roof = fields.Text(string="الدور السطح")
    
    def action_view_parent_project(self):
        self.ensure_one()
        if not self.project_id:
            raise UserError(_("This task is not linked to any Project."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'res_id': self.project_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_send_task_form_whatsapp(self):
        self.ensure_one()
        # Get the customer's phone from the parent project
        phone = self.project_id.partner_id.mobile or self.project_id.partner_id.phone
        if not phone:
            raise UserError("رقم الهاتف مفقود للعميل في المشروع")
        
        cleaned_phone = ''.join(filter(str.isdigit, phone))
        
        # 1. Get the Base URL of your website
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        # 2. Build the Direct PDF Download Link
        # Format: /report/pdf/module_name.report_template_name/record_id
        report_name = 'engineering_project.report_initial_design_template'
        pdf_link = f"{base_url}/report/pdf/{report_name}/{self.id}"
        
        # 3. Create the new message
        message = _("مرحباً %s،\nنرفق لكم نموذج مكونات المشروع للمراجعة.\nيمكنكم عرض أو تحميل النموذج (PDF) عبر الرابط التالي:\n%s") % (self.project_id.partner_id.name, pdf_link)
        
        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://web.whatsapp.com/send?phone={cleaned_phone}&text={encoded_message}"
        
        return { 'type': 'ir.actions.act_url', 'url': whatsapp_url, 'target': 'new' }
