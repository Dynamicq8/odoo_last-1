# -*- coding: utf-8 -*-
from odoo import models, fields, api

# ==============================================================================
#  NEW MODELS FOR HIERARCHY
# ==============================================================================

class KuwaitGovernorate(models.Model):
    _name = 'kuwait.governorate'
    _description = 'Governorate'
    name = fields.Char(string="المحافظة", required=True)

class KuwaitRegion(models.Model):
    _name = 'kuwait.region'
    _description = 'Region'
    name = fields.Char(string="المنطقة", required=True)
    governorate_id = fields.Many2one('kuwait.governorate', string="المحافظة", ondelete='cascade')

# ==============================================================================
#  NEW MODEL FOR ENGINEERING PACKAGE
# ==============================================================================
class EngineeringPackage(models.Model):
    _name = 'engineering.package'
    _description = 'Engineering Package'

    name = fields.Char(string="اسم الباقة الهندسية", required=True)
    code = fields.Char(string="كود الباقة", copy=False, default='جديد') # Example: Add a code
    # You can add other fields relevant to an engineering package here, e.g.:
    # description = fields.Text(string="وصف الباقة")
    # price = fields.Float(string="السعر")
    # active = fields.Boolean(string="نشط", default=True)


# ==============================================================================
#  RES PARTNER (Customer Profile)
# ==============================================================================
class ResPartner(models.Model):
    _inherit = 'res.partner'

    building_type = fields.Selection([('residential', 'سكن خاص'), ('investment', 'استثماري'), ('commercial', 'تجاري'), ('industrial', 'صناعي'), ('cooperative', 'جمعيات وتعاونيات'), ('mosque', 'مساجد'), ('hangar', 'مخازن / شبرات'), ('farm', 'مزارع')], string="نوع العقار", tracking=True)
    service_type = fields.Selection([('new_construction', 'بناء جديد'), ('demolition', 'هدم'), ('modification', 'تعديل'), ('addition', 'اضافة'), ('addition_modification', 'تعديل واضافة'), ('supervision_only', 'إشراف هندسي فقط'), ('renovation', 'ترميم'), ('internal_partitions', 'قواطع داخلية'), ('shades_garden', 'مظلات / حدائق')], string="نوع الخدمة", tracking=True)
    civil_number = fields.Char(string="الرقم المدني (Civil ID)")
    plot_no = fields.Char(string="رقم القسيمة (Plot)")
    block_no = fields.Char(string="القطعة (Block)")
    street_no = fields.Char(string="الضاحيه")
    area = fields.Char(string="مساحة الارض (Area)")
    
    governorate_id = fields.Many2one('kuwait.governorate', string="المحافظة")
    region_id = fields.Many2one('kuwait.region', string="المنطقة (Region)")


# ==============================================================================
#  CRM LEAD
# ==============================================================================
# All custom fields and data-passing functions have been removed. 
# Odoo will just use the standard Name, Email, Phone, etc.


# ==============================================================================
#  SALE ORDER
# ==============================================================================
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    building_type = fields.Selection([('residential', 'سكن خاص'), ('investment', 'استثماري'), ('commercial', 'تجاري'), ('industrial', 'صناعي'), ('cooperative', 'جمعيات وتعاونيات'), ('mosque', 'مساجد'), ('hangar', 'مخازن / شبرات'), ('farm', 'مزارع')], string="نوع العقار", store=True)
    service_type = fields.Selection([('new_construction', 'بناء جديد'), ('demolition', 'هدم'), ('modification', 'تعديل'), ('addition', 'اضافة'), ('addition_modification', 'تعديل واضافة'), ('supervision_only', 'إشراف هندسي فقط'), ('renovation', 'ترميم'), ('internal_partitions', 'قواطع داخلية'), ('shades_garden', 'مظلات / حدائق')], string="نوع الخدمة", store=True)

    plot_no = fields.Char(string="رقم القسيمة", store=True)
    block_no = fields.Char(string="القطعة", store=True)
    street_no = fields.Char(string="الضاحيه", store=True)
    area = fields.Char(string="مساحة الارض", store=True)
    
    governorate_id = fields.Many2one('kuwait.governorate', string="المحافظة", store=True)
    region_id = fields.Many2one('kuwait.region', string="المنطقة (Region)", store=True)

    # ADD THIS FIELD:
    engineering_package_id = fields.Many2one(
        'engineering.package',  # This links to the new model defined above
        string="Engineering Package",
        help="Select the engineering package for this sale order",
        index=True,
        ondelete='restrict', # Consider 'set null' if a package can be deleted without breaking sales
        store=True,
    )

    # Automatically pull these details from the Customer when creating a Quotation
    @api.onchange('partner_id')
    def _onchange_partner_id_engineering_fields(self):
        if self.partner_id:
            self.building_type = self.partner_id.building_type
            self.service_type = self.partner_id.service_type
            self.plot_no = self.partner_id.plot_no
            self.block_no = self.partner_id.block_no
            self.street_no = self.partner_id.street_no
            self.area = self.partner_id.area
            self.governorate_id = self.partner_id.governorate_id
            self.region_id = self.partner_id.region_id
            # You might also want to set a default engineering_package_id here
            # if there's a logic for that, but it's optional.
