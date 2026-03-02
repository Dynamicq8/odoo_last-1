# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EngineeringQuotationStage(models.Model):
    _name = 'engineering.quotation.stage'
    _description = 'Engineering Quotation Stage'
    _order = 'sequence, id'

    name = fields.Char(string='اسم المرحلة (Stage Name)', required=True, translate=True)
    sequence = fields.Integer(default=10)
    next_stage_id = fields.Many2one('engineering.quotation.stage', string="المرحلة التالية (Next Stage)")
    button_name = fields.Char(string="نص الزر (Button Label)", help="Text for the button to move to Next Stage.")
    
    is_approved_stage = fields.Boolean(string="مرحلة الموافقة؟ (Is Approved Stage?)", 
                                        help="Moving to this stage triggers Project Creation")
    is_rejected_stage = fields.Boolean(string="مرحلة الرفض؟ (Is Rejected Stage?)")
    fold = fields.Boolean(string='Folded in Kanban', default=False)

# --- TASK 2.2 – Stage History Tracking ---
class EngineeringQuotationStageHistory(models.Model):
    _name = 'engineering.quotation.stage.history'
    _description = 'Quotation Stage History'
    _order = 'change_date desc'

    quotation_id = fields.Many2one('sale.order', string='Quotation', ondelete='cascade')
    from_stage_id = fields.Many2one('engineering.quotation.stage', string='From Stage')
    to_stage_id = fields.Many2one('engineering.quotation.stage', string='To Stage')
    changed_by_id = fields.Many2one('res.users', string='Changed By', default=lambda self: self.env.user)
    change_date = fields.Datetime(string='Change Date', default=fields.Datetime.now)

# --- TASK 2.3 – Extend Sale Order ---
class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # --- Project Link (replaces sale_project dependency) ---
    project_id = fields.Many2one('project.project', string='Project', copy=False)
    
    # --- Stages & History Fields ---
    quotation_stage_id = fields.Many2one(
        'engineering.quotation.stage',
        string='Quotation Stage',
        tracking=True,
        default=lambda self: self.env['engineering.quotation.stage'].search([], order='sequence', limit=1)
    )
    stage_history_ids = fields.One2many(
        'engineering.quotation.stage.history',
        'quotation_id',
        string='Stage History'
    )
    
    next_stage_button_name = fields.Char(compute='_compute_next_stage_button_name')
    show_next_stage_button = fields.Boolean(compute='_compute_next_stage_button_name')

    # --- Required Documents Logic ---
    required_documents = fields.Html(
        string="المستندات المطلوبة (Required Documents)",
        compute='_compute_required_documents',
        store=True
    )

    @api.depends('service_type', 'building_type')
    def _compute_required_documents(self):
        for order in self:
            docs = "<ul>"
            docs += "<li>البطاقة المدنية للمالك (Civil ID Copy)</li>"
            
            if order.service_type == 'new_construction':
                docs += "<li>وثيقة الملكية (Title Deed)</li><li>كتاب التخصيص (Allocation Letter)</li><li>مخطط المساحة (Survey Plan)</li>"
            elif order.service_type in ['modification', 'extension', 'extension_modification']:
                docs += "<li>رخصة البناء الأصلية (Original Building Permit)</li><li>المخططات المعمارية والإنشائية المرخصة (Original Plans)</li><li>وثيقة البيت (House Document)</li>"
            elif order.service_type == 'demolition':
                docs += "<li>كتاب براءة ذمة من الكهرباء والماء (Clearance Certificate)</li><li>رخصة البناء القديمة (Old Permit)</li>"
            
            docs += "</ul>"
            order.required_documents = docs

    # --- 50 KD Opening Fee Logic ---
    def action_create_opening_fee_invoice(self):
        self.ensure_one()
        product_fee = self.env['product.product'].search([('name', '=', 'رسوم فتح ملف')], limit=1)
        if not product_fee:
            product_fee = self.env['product.product'].create({'name': 'رسوم فتح ملف', 'type': 'service', 'list_price': 50.0})

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {'product_id': product_fee.id, 'quantity': 1, 'price_unit': 50.0, 'name': 'رسوم فتح ملف وتصميم مبدئي'})],
        }
        invoice = self.env['account.move'].create(invoice_vals)
        return {'name': _('Open Invoice'), 'view_mode': 'form', 'res_model': 'account.move', 'res_id': invoice.id, 'type': 'ir.actions.act_window'}

    def action_apply_opening_deduction(self):
        self.ensure_one()
        product_fee = self.env['product.product'].search([('name', '=', 'رسوم فتح ملف')], limit=1)
        if not product_fee: raise UserError(_("Product 'رسوم فتح ملف' not found."))
        
        self.env['sale.order.line'].create({
            'order_id': self.id,
            'product_id': product_fee.id,
            'name': 'خصم رسوم فتح ملف (Deduction of File Opening Fees)',
            'product_uom_qty': 1,
            'price_unit': -50.0,
            'tax_id': False,
        })
        return True

    # ---------------------------------------------------------
    # CORE LOGIC: Approval & Project Creation
    # ---------------------------------------------------------

    def action_confirm(self):
        """
        Override standard confirm:
        - If customer signs via portal, auto-move to 'Approved' stage and confirm.
        - If salesman clicks confirm manually, block it unless it's in the 'Approved' stage.
        """
        for order in self:
            # Skip this check entirely for standard Odoo orders
            if not order.building_type:
                continue

            # Find the 'Approved' stage in the database
            approved_stage = self.env['engineering.quotation.stage'].search([('is_approved_stage', '=', True)], limit=1)

            # SCENARIO 1: The customer just signed via the Portal
            # Odoo saves the signature just before calling this function
            if order.signature:
                if approved_stage and order.quotation_stage_id != approved_stage:
                    # Log the stage change in history
                    self.env['engineering.quotation.stage.history'].create({
                        'quotation_id': order.id,
                        'from_stage_id': order.quotation_stage_id.id if order.quotation_stage_id else False,
                        'to_stage_id': approved_stage.id,
                    })
                    # Auto-change the stage to Approved
                    order.quotation_stage_id = approved_stage.id

            # SCENARIO 2: A user is clicking "Confirm" manually in the backend
            elif order.quotation_stage_id and not order.quotation_stage_id.is_approved_stage:
                raise UserError(_("لا يمكن تأكيد عرض السعر يدوياً حتى يتم الموافقة عليه (Approved) أو توقيعه من قبل العميل.\nYou cannot confirm the quotation until it is in an 'Approved' stage or signed by the customer."))
        
        return super(SaleOrder, self).action_confirm()

    def action_move_to_next_stage(self):
        """
        Moves to next stage. Project is NOT created automatically here.
        Project creation happens via separate action after approval.
        """
        self.ensure_one()
        current_stage = self.quotation_stage_id
        next_stage = current_stage.next_stage_id if current_stage else False
        
        if next_stage:
            # Track History
            self.env['engineering.quotation.stage.history'].create({
                'quotation_id': self.id,
                'from_stage_id': current_stage.id if current_stage else False,
                'to_stage_id': next_stage.id,
            })
            
            # Update Stage
            self.write({'quotation_stage_id': next_stage.id})

            # If approved stage, show success message but DON'T auto-create project
            if next_stage.is_approved_stage:
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': _('تمت الموافقة على عرض السعر! يمكنك الآن إنشاء المشروع والعقد.\nQuotation Approved! You can now create the project and contract.'),
                        'type': 'rainbow_man',
                    }
                }

            return {'type': 'ir.actions.client', 'tag': 'reload'}
        else:
            raise UserError(_("لا توجد مرحلة تالية محددة.\nNo next stage defined."))

    def action_create_project_from_quotation(self):
        """
        Manually create project from approved quotation.
        This is called via button, NOT automatically.
        """
        self.ensure_one()
        
        if not self.quotation_stage_id or not self.quotation_stage_id.is_approved_stage:
            raise UserError(_("يجب الموافقة على عرض السعر أولاً قبل إنشاء المشروع.\nQuotation must be approved before creating a project."))
        
        if self.project_id:
            raise UserError(_("يوجد مشروع مرتبط بهذا العرض بالفعل.\nA project already exists for this quotation."))
        
        # Confirm the order first if not confirmed
        if self.state in ['draft', 'sent']:
            self.action_confirm()
        
        # Create the project
        project = self._create_engineering_project()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('المشروع (Project)'),
            'res_model': 'project.project',
            'res_id': project.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _create_engineering_project(self):
        self.ensure_one()
        if self.project_id:
            return self.project_id

        # Create Project
        project = self.env['project.project'].create({
            'name': f"{self.name} - {self.partner_id.name}",
            'partner_id': self.partner_id.id,
            'sale_order_id': self.id,
        })
        
        # Define Project Stages (Tasks Columns)
        stages = ['التصميم المبدئي (الكروكي)', 'التعاقد وجمع الوثائق', 'الموافقات الخارجية', 'التصميمات التفصيلية', 'الإشراف الهندسي', 'إنهاء المشروع']
        project_stage_model = self.env['project.task.type']
        for index, stage_name in enumerate(stages):
            project_stage_model.create({
                'name': stage_name, 
                'project_ids': [(4, project.id)], 
                'sequence': index + 1
            })
            
        self.write({'project_id': project.id})
        return project

    # --- Button Visibility Helper ---
    @api.depends('quotation_stage_id')
    def _compute_next_stage_button_name(self):
        for order in self:
            # Show button if there is a next stage AND order is not cancelled
            if order.quotation_stage_id and order.quotation_stage_id.next_stage_id and order.state != 'cancel':
                order.next_stage_button_name = order.quotation_stage_id.button_name
                order.show_next_stage_button = True
            else:
                order.next_stage_button_name = False
                order.show_next_stage_button = False

    # --- WhatsApp ---
    def action_send_quotation_whatsapp(self):
        self.ensure_one()
        customer_phone = self.partner_id.mobile or self.partner_id.phone
        if not customer_phone:
            raise UserError(_("Please add a mobile number for the customer."))

        # 1. Clean phone number
        cleaned_phone = ''.join(filter(str.isdigit, customer_phone))

        # 2. GENERATE THE CORRECT LINK
        # A. Ensure the record has an access token (critical for the link to work without login)
        if not self.access_token:
            self._portal_ensure_token()

        # B. Get the Base URL (e.g. https://mazen41...)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        # C. Get the Portal Path (e.g. /my/orders/8?access_token=...)
        portal_path = self.get_portal_url()

        # D. Combine them
        full_link = base_url.rstrip('/') + portal_path

        # 3. Create Message
        msg_text = _("مرحباً %s،\nيرجى مراجعة عرض السعر %s عبر الرابط التالي:\n%s") % (self.partner_id.name, self.name, full_link)
        
        # 4. Encode for URL
        import urllib.parse
        encoded_msg = urllib.parse.quote(msg_text)
        
        whatsapp_url = f"https://web.whatsapp.com/send?phone={cleaned_phone}&text={encoded_msg}"
        
        return {'type': 'ir.actions.act_url', 'url': whatsapp_url, 'target': 'new'}
