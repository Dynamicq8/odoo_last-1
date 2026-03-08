# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import urllib.parse

class ProjectProject(models.Model):
    _inherit = 'project.project'

    sale_order_id = fields.Many2one('sale.order', string='Source Quotation', readonly=True)
    building_type = fields.Selection([('residential', 'سكن خاص'), ('investment', 'استثماري'), ('commercial', 'تجاري'), ('industrial', 'صناعي'), ('cooperative', 'جمعيات وتعاونيات'), ('mosque', 'مساجد'), ('hangar', 'مخازن / شبرات'), ('farm', 'مزارع')], string="نوع المبنى")
    service_type = fields.Selection([('new_construction', 'بناء جديد'), ('demolition', 'هدم'), ('modification', 'تعديل'), ('addition', 'اضافة'), ('addition_modification', 'تعديل واضافة'), ('supervision_only', 'إشراف هندسي فقط'), ('renovation', 'ترميم'), ('internal_partitions', 'قواطع داخلية'), ('shades_garden', 'مظلات / حدائق')], string="نوع الخدمة")
    region = fields.Char(string="المنطقة (Region)")
    plot_no = fields.Char(string="رقم القسيمة")
    block_no = fields.Char(string="القطعة")
    street_no = fields.Char(string="الشارع")
    area = fields.Char(string="المساحة (Area)")

    # (Kept silently to prevent database crashes)
    floor_basement = fields.Text(string="أولاً السرداب")
    floor_ground = fields.Text(string="ثانياً الدور الأرضي")
    floor_first = fields.Text(string="الدور الأول")
    floor_second = fields.Text(string="الدور الثاني")
    floor_roof = fields.Text(string="الدور السطح")

    # ==========================================
    # AUTOMATION WORKFLOW: TEAM ASSIGNMENT
    # ==========================================
    architect_id = fields.Many2one('res.users', string="المهندس المعماري (Architect)")
    secretary_id = fields.Many2one('res.users', string="السكرتارية (Secretary)")
    structural_id = fields.Many2one('res.users', string="المهندس الإنشائي (Structural)")
    draftsman_id = fields.Many2one('res.users', string="الرسام (Draftsman)")

    workflow_started = fields.Boolean(default=False, string="بدأ سير العمل")

    def action_start_workflow(self):
        """ This is the big button you click to start Phase 1 """
        self.ensure_one()
        if self.workflow_started:
            raise UserError(_("تم بدء سير العمل مسبقاً! (Workflow already started)"))
        
        if not self.architect_id or not self.secretary_id:
            raise UserError(_("يرجى تعيين المهندس المعماري والسكرتارية أولاً! (Assign Architect and Secretary first)"))

        # Get stages
        stages = self.env['project.task.type'].search([('project_ids', 'in', self.id)], order='sequence')
        if not stages:
            raise UserError(_("لا توجد مراحل في هذا المشروع! (No stages found)"))
            
        stage_1 = stages[0] # التصميم المبدئي
        stage_2 = stages[1] if len(stages) > 1 else stage_1 # التعاقد والوثائق

        # 1. Create Architect Task (Phase 1)
        self.env['project.task'].create({
            'name': 'كروكي معماري (Architectural Sketch)',
            'project_id': self.id,
            'user_ids': [(4, self.architect_id.id)],
            'stage_id': stage_1.id,
            'workflow_step': 'phase1_architect', # This tells Odoo to listen to this task
        })

        # 2. Create Secretary Tasks
        sec_tasks = ['جمع وثائق المشروع', 'طلب فحص تربة', 'ورقة كهرباء']
        for task_name in sec_tasks:
            self.env['project.task'].create({
                'name': task_name,
                'project_id': self.id,
                'user_ids': [(4, self.secretary_id.id)],
                'stage_id': stage_2.id,
            })
        
        self.workflow_started = True

    def _trigger_phase_2(self):
        """ Automatically creates Phase 2 when Phase 1 is approved """
        # We need a stage for this. Let's put it in the 3rd stage (الموافقات/التنسيق)
        stages = self.env['project.task.type'].search([('project_ids', 'in', self.id)], order='sequence')
        target_stage = stages[2] if len(stages) > 2 else stages[0]

        # Task: Structural
        if self.structural_id:
            self.env['project.task'].create({
                'name': 'وضع الأعمدة المناسبة (Structural Columns)',
                'project_id': self.id,
                'user_ids': [(4, self.structural_id.id)],
                'stage_id': target_stage.id,
                'workflow_step': 'phase2_structural',
            })
        
        # Task: Facade
        if self.architect_id:
            self.env['project.task'].create({
                'name': 'تصميم الواجهات (Facade Design)',
                'project_id': self.id,
                'user_ids': [(4, self.architect_id.id)],
                'stage_id': target_stage.id,
                'workflow_step': 'phase2_facade',
            })


class ProjectTask(models.Model):
    _inherit = 'project.task'

    # Hidden field to track the domino effect
    workflow_step = fields.Selection([
        ('phase1_architect', 'Phase 1: Architect'),
        ('phase2_structural', 'Phase 2: Structural'),
        ('phase2_facade', 'Phase 2: Facade'),
        ('phase3_drafting', 'Phase 3: Drafting'),
        ('phase4_licensing', 'Phase 4: Licensing'),
    ], string="خطوة سير العمل", readonly=True)

    floor_basement = fields.Text(string="أولاً السرداب")
    floor_ground = fields.Text(string="ثانياً الدور الأرضي")
    floor_first = fields.Text(string="الدور الأول")
    floor_second = fields.Text(string="الدور الثاني")
    floor_roof = fields.Text(string="الدور السطح")
    
    def action_view_parent_project(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'project.project',
            'res_id': self.project_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_send_task_form_whatsapp(self):
        self.ensure_one()
        phone = self.project_id.partner_id.mobile or self.project_id.partner_id.phone
        if not phone: raise UserError("رقم الهاتف مفقود للعميل في المشروع")
        cleaned_phone = ''.join(filter(str.isdigit, phone))
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        self._portal_ensure_token()
        project_url = f"{base_url}/report/pdf/engineering_project.report_initial_design_template/{self.id}"
        message = _("مرحباً %s،\nنرفق لكم نموذج مكونات المشروع للمراجعة.\nالرابط:\n%s") % (self.project_id.partner_id.name, project_url)
        import urllib.parse
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://web.whatsapp.com/send?phone={cleaned_phone}&text={encoded_message}"
        return { 'type': 'ir.actions.act_url', 'url': whatsapp_url, 'target': 'new' }

    def action_move_to_next_stage(self):
        self.ensure_one()
        if not self.project_id:
            raise UserError(_("المهمة غير مرتبطة بمشروع!"))

        project_stages = self.env['project.task.type'].search([('project_ids', 'in', self.project_id.id)], order='sequence, id')
        stages_list = list(project_stages)
        
        if self.stage_id in stages_list:
            current_index = stages_list.index(self.stage_id)
            if current_index + 1 < len(stages_list):
                next_stage = stages_list[current_index + 1]
                self.write({'stage_id': next_stage.id})
                
                # ==========================================
                # AUTOMATION LISTENER: Check if we need to trigger next phase
                # ==========================================
                if self.workflow_step == 'phase1_architect':
                    self.project_id._trigger_phase_2()

                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': _('تم نقل المهمة للمرحلة التالية!'),
                        'type': 'rainbow_man',
                    }
                }
            else:
                raise UserError(_("هذه هي المرحلة الأخيرة، لا توجد مرحلة تالية."))
        elif stages_list:
            self.write({'stage_id': stages_list[0].id})
        return True
