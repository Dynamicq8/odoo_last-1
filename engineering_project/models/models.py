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

    # ==========================================
    # FULL TEAM ASSIGNMENT (10 Steps Workflow)
    # ==========================================
    architect_id = fields.Many2one('res.users', string="المهندس المعماري")
    accountant_id = fields.Many2one('res.users', string="المحاسبة")
    structural_id = fields.Many2one('res.users', string="المهندس الإنشائي")
    facade_draftsman_id = fields.Many2one('res.users', string="رسام الواجهات")
    secretary_id = fields.Many2one('res.users', string="السكرتارية")
    muni_draftsman_id = fields.Many2one('res.users', string="رسام البلدية")
    electrical_id = fields.Many2one('res.users', string="مهندس الكهرباء")
    draftsman_id = fields.Many2one('res.users', string="الرسام (صحي/مخططات)")

    # Prevention flags (Stops duplicate tasks if clicked twice)
    workflow_started = fields.Boolean(default=False)
    step_2_triggered = fields.Boolean(default=False)
    step_3_triggered = fields.Boolean(default=False)
    step_4_triggered = fields.Boolean(default=False)
    step_5_triggered = fields.Boolean(default=False)
    step_6_triggered = fields.Boolean(default=False)
    step_8_triggered = fields.Boolean(default=False)
    step_9_triggered = fields.Boolean(default=False)
    step_10_triggered = fields.Boolean(default=False)

    def action_start_workflow(self):
        """ START PHASE 1 """
        self.ensure_one()
        if self.workflow_started:
            raise UserError(_("تم بدء سير العمل مسبقاً!"))
        
        stages = self.env['project.task.type'].search([('project_ids', 'in', self.id)], order='sequence')
        first_stage = stages[0].id if stages else False

        # Step 1: Architect Sketch
        self._create_task('1. كروكي معماري', self.architect_id, first_stage, 'step_1')
        self.workflow_started = True

    def _trigger_next_workflow_step(self, completed_step):
        """ THE DOMINO EFFECT - Automatically runs when a task is Approved """
        stages = self.env['project.task.type'].search([('project_ids', 'in', self.id)], order='sequence')
        default_stage = stages[0].id if stages else False # Tasks spawn in the first column so you see them

        if completed_step == 'step_1' and not self.step_2_triggered:
            self._create_task('2. العقد وتحصيل الدفعة الاولي', self.accountant_id, default_stage)
            self._create_task('2. سيستم الاعمدة', self.structural_id, default_stage, 'step_2_cols')
            self._create_task('2. الواجهات', self.facade_draftsman_id, default_stage)
            self._create_task('2. جمع الوثائق وتعبة النماذج', self.secretary_id, default_stage)
            self.step_2_triggered = True

        elif completed_step == 'step_2_cols' and not self.step_3_triggered:
            self._create_task('3. رسم المعماري للبلدية', self.muni_draftsman_id, default_stage, 'step_3')
            self.step_3_triggered = True

        elif completed_step == 'step_3' and not self.step_4_triggered:
            self._create_task('4. ادخال المعاملة بلدية للاعتماد', self.secretary_id, default_stage, 'step_4')
            self.step_4_triggered = True

        elif completed_step == 'step_4' and not self.step_5_triggered:
            self._create_task('5. اعتماد الرخصة من البلدية', self.secretary_id, default_stage, 'step_5')
            self.step_5_triggered = True

        elif completed_step == 'step_5' and not self.step_6_triggered:
            self._create_task('6. تصميم الانشائي الكامل', self.structural_id, default_stage, 'step_6')
            self._create_task('7. تصميم مخطط الصحي', self.draftsman_id, default_stage)
            self._create_task('7. تصميم مخطط الكهرباء', self.electrical_id, default_stage)
            self.step_6_triggered = True

        elif completed_step == 'step_6' and not self.step_8_triggered:
            self._create_task('8. تعهد الاشراف', self.secretary_id, default_stage, 'step_8')
            self.step_8_triggered = True

        elif completed_step == 'step_8' and not self.step_9_triggered:
            self._create_task('9. الاشراف علي التنفيذ', self.structural_id, default_stage, 'step_9')
            self.step_9_triggered = True

        elif completed_step == 'step_9' and not self.step_10_triggered:
            self._create_task('10. انهاء الاشراف', self.secretary_id, default_stage)
            self.step_10_triggered = True

    def _create_task(self, name, user, stage_id, workflow_step=False):
        """ Helper function to generate tasks cleanly """
        val = {
            'name': name,
            'project_id': self.id,
            'stage_id': stage_id,
        }
        if user:
            val['user_ids'] = [(4, user.id)]
        if workflow_step:
            val['workflow_step'] = workflow_step
        self.env['project.task'].create(val)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    # --- THE FIX IS HERE: Brought back Selection to stop Odoo crashing ---
    workflow_step = fields.Selection([
        ('step_1', 'Step 1'),
        ('step_2_cols', 'Step 2 Cols'),
        ('step_3', 'Step 3'),
        ('step_4', 'Step 4'),
        ('step_5', 'Step 5'),
        ('step_6', 'Step 6'),
        ('step_8', 'Step 8'),
        ('step_9', 'Step 9'),
        ('step_10', 'Step 10'),
    ], string="Workflow Trigger", readonly=True)

    floor_basement = fields.Text(string="أولاً السرداب")
    floor_ground = fields.Text(string="ثانياً الدور الأرضي")
    floor_first = fields.Text(string="الدور الأول")
    floor_second = fields.Text(string="الدور الثاني")
    floor_roof = fields.Text(string="الدور السطح")
    
    # -----------------------------------------------------
    # THE MAGIC: Listen for 'Approved' state to trigger tasks
    # -----------------------------------------------------
    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        # Check if the state changed to 'Approved' (03_approved) or 'Done' (1_done)
        if 'state' in vals and vals['state'] in ['03_approved', '1_done']:
            for task in self:
                if task.workflow_step and task.project_id:
                    # Fire the trigger!
                    task.project_id._trigger_next_workflow_step(task.workflow_step)
        return res

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
