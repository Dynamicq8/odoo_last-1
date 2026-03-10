# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import urllib.parse

# ==============================================================================
#  HELPER FUNCTIONS FOR GOVERNORATE & REGION
# ==============================================================================
def _get_governorate_areas():
    return {
        'محافظة العاصمة': [
            ('جابر الاحمد', 'جابر الاحمد'), ('القبلة', 'القبلة'), ('الشرق', 'الشرق'),
            ('المرقاب', 'المرقاب'), ('الصالحية', 'الصالحية'), ('دسمان', 'دسمان'),
            ('الدعية', 'الدعية'), ('الدسمة', 'الدسمة'), ('كيفان', 'كيفان'),
            ('الخالدية', 'الخالدية'), ('الشامية', 'الشامية'), ('الروضة', 'الروضة'),
            ('العديلية', 'العديلية'), ('الفيحاء', 'الفيحاء'), ('القادسية', 'القادسية'),
            ('قرطبة', 'قرطبة'), ('السرة', 'السرة'), ('اليرموك', 'اليرموك'),
            ('النزهة', 'النزهة'), ('الشويخ الصناعية 1', 'الشويخ الصناعية 1'),
            ('الشويخ الصناعية 2', 'الشويخ الصناعية 2'), ('الشويخ الصناعية 3', 'الشويخ الصناعية 3'),
            ('الشويخ الادارية', 'الشويخ الادارية'), ('الشويخ السكنى', 'الشويخ السكنى'),
            ('الشويخ التعليمية', 'الشويخ التعليمية'), ('الشويخ الصحيه', 'الشويخ الصحيه'),
            ('الواجهه البحرية', 'الواجهه البحرية'), ('غرناطة', 'غرناطة'),
            ('الصليبيخات', 'الصليبيخات'), ('المنصورية', 'المنصورية'),
            ('الدوحة السكنيه', 'الدوحة السكنيه'), ('الرى', 'الرى'),
            ('ميناء الدوحة', 'ميناء الدوحة'), ('جزيره عوهه', 'جزيره عوهه'),
            ('جزيره فيلكه', 'جزيره فيلكه'), ('جزيره مسكان', 'جزيره مسكان'),
            ('حدائق السور – الحزام الاخضر', 'حدائق السور – الحزام الاخضر'),
            ('بنيد القار', 'بنيد القار'), ('ميناء الشويخ', 'ميناء الشويخ'),
            ('معسكرات المباركيه – جيوان', 'معسكرات المباركيه – جيوان'),
            ('شاليهات الدوحة', 'شاليهات الدوحة'), ('السره', 'السره'),
        ],
        'محافظة حولي': [
            ('حولي', 'حولي'), ('السالمية', 'السالمية'), ('الرميثية', 'الرميثية'),
            ('الجابرية', 'الجابرية'), ('بيان', 'بيان'), ('مشرف', 'مشرف'),
            ('سلوى', 'سلوى'), ('ميدان حولي', 'ميدان حولي'), ('الزهراء', 'الزهراء'),
            ('الصديق', 'الصديق'), ('حطين', 'حطين'), ('السلام', 'السلام'),
            ('الشهداء', 'الشهداء'), ('انجفة', 'انجفة'), ('الشعب', 'الشعب'),
            ('مبارك العبد الله', 'مبارك العبد الله'), ('الواجهه البحريه', 'الواجهه البحريه'),
            ('الضاحيه الدبلوماسيه', 'الضاحيه الدبلوماسيه'),
            ('المباركيه قطعة 15 بيان', 'المباركيه قطعة 15 بيان'), ('البدع', 'البدع'),
        ],
        'محافظة الفروانية': [
            ('الفروانية', 'الفروانية'), ('خيطان', 'خيطان'), ('العمرية', 'العمرية'),
            ('الرحاب', 'الرحاب'), ('الرقعى', 'الرقعى'), ('الشدادية', 'الشدادية'),
            ('الضجيج', 'الضجيج'), ('المطار', 'المطار'),
            ('غرب الجليب الشداديه', 'غرب الجليب الشداديه'),
            ('عبد الله المبارك', 'عبد الله المبارك'),
            ('مدينه صباح السالم الجامعية', 'مدينه صباح السالم الجامعية'),
            ('منطقة المعارض جنوب خيطان', 'منطقة المعارض جنوب خيطان'),
            ('الأندلس', 'الأندلس'), ('إشبيلية', 'إشبيلية'),
            ('جليب الشيوخ', 'جليب الشيوخ'), ('الفردوس', 'الفردوس'),
            ('صباح الناصر', 'صباح الناصر'), ('الرابية', 'الرابية'),
            ('العارضية', 'العارضية'),
            ('العارضية استعمالات حكومية', 'العارضية استعمالات حكومية'),
            ('العارضية مخازن', 'العارضية مخازن'), ('العارضية الحرفية', 'العارضية الحرفية'),
            ('غرب عبد المبارك السكنى', 'غرب عبد المبارك السكنى'),
            ('جنوب عبد الله المبارك السكنى', 'جنوب عبد الله المبارك السكنى'),
            ('العباسية', 'العباسية'),
        ],
        'محافظة الأحمدي': [
            ('الأحمدي', 'الأحمدي'), ('الفحيحيل', 'الفحيحيل'), ('المنقف', 'المنقف'),
            ('أبو حليفة', 'أبو حليفة'), ('الصباحية', 'الصباحية'), ('الرقة', 'الرقة'),
            ('هدية', 'هدية'), ('الفنطاس', 'الفنطاس'), ('المهبولة', 'المهبولة'),
            ('العقيلة', 'العقيلة'), ('الظهر', 'الظهر'), ('جابر العلي', 'جابر العلي'),
            ('صباح الأحمد السكنية', 'صباح الأحمد السكنية'), ('الوفرة', 'الوفرة'),
            ('الخيران', 'الخيران'), ('ميناء الزور', 'ميناء الزور'),
            ('ميناء عبد الله الصناعية', 'ميناء عبد الله الصناعية'),
            ('ميناء عبد الله', 'ميناء عبد الله'), ('مزارع الوفره', 'مزارع الوفره'),
            ('صباح الاحمد السكنيه', 'صباح الاحمد السكنيه'),
            ('صباح الاحمد البحريه', 'صباح الاحمد البحريه'),
            ('قردان والحفيرة والفوار', 'قردان والحفيرة والفوار'),
            ('فهد الاحمد', 'فهد الاحمد'),
            ('على صباح السالم – ام الهيمان', 'على صباح السالم – ام الهيمان'),
            ('عريفجان', 'عريفجان'), ('ضليع الزنيف', 'ضليع الزنيف'),
            ('شرق الاحمدى الخدميه والحرفية والتجاريه', 'شرق الاحمدى الخدميه والحرفية والتجاريه'),
            ('شرق الاحمدى', 'شرق الاحمدى'),
            ('شاليهات ميناء عبد الله', 'شاليهات ميناء عبد الله'),
            ('شاليهات بنيدر', 'شاليهات بنيدر'),
            ('شاليهات النويصيب', 'شاليهات النويصيب'),
            ('شاليهات الضاعيه', 'شاليهات الضاعيه'), ('شاليهات الزور', 'شاليهات الزور'),
            ('شاليهات الخيران', 'شاليهات الخيران'),
            ('شاليهات الجليعه', 'شاليهات الجليعه'),
            ('رجم خشمان ومصلان', 'رجم خشمان ومصلان'),
            ('جنوب الصباحية', 'جنوب الصباحية'), ('برقان', 'برقان'),
            ('الوفره السكنيه', 'الوفره السكنيه'),
            ('الهيئة العامة للزراعة والثورة السمكيه – مزارع', 'الهيئة العامة للزراعة والثورة السمكيه – مزارع'),
            ('النويصيب', 'النويصيب'), ('المقوع', 'المقوع'), ('الفحيحيل', 'الفحيحيل'),
            ('العبدليه', 'العبدليه'),
            ('الصناعية الصناعية الخلط الجاهز', 'الصناعية الصناعية الخلط الجاهز'),
            ('الشعيبة الصناعية الشرقيه', 'الشعيبة الصناعية الشرقيه'),
            ('الشعيبة الصناعية الغربيه', 'الشعيبة الصناعية الغربيه'),
            ('الشعيبة', 'الشعيبة'), ('الشدادية الصناعية', 'الشدادية الصناعية'),
            ('الزور وصوله', 'الزور وصوله'), ('ام حجول', 'ام حجول'),
            ('ام قدير', 'ام قدير'), ('ابو خرجين والصبيحية', 'ابو خرجين والصبيحية'),
        ],
        'محافظة الجهراء': [
            ('الجهراء', 'الجهراء'), ('القصر', 'القصر'), ('النسيم', 'النسيم'),
            ('الواحة', 'الواحة'), ('النعيم', 'النعيم'), ('تيماء', 'تيماء'),
            ('سعد العبدالله', 'سعد العبدالله'), ('الصليبية', 'الصليبية'),
            ('كبد', 'كبد'), ('المطلاع', 'المطلاع'), ('أمغرة', 'أمغرة'),
            ('البحيث', 'البحيث'), ('الجهراء الصناعية الثانية', 'الجهراء الصناعية الثانية'),
            ('الجهراء الصناعية الحرفيه الاولى', 'الجهراء الصناعية الحرفيه الاولى'),
            ('الرتقة والحريجه', 'الرتقة والحريجه'),
            ('الرحية وام توينج', 'الرحية وام توينج'), ('الروضتين', 'الروضتين'),
            ('السالمى', 'السالمى'), ('السكراب', 'السكراب'),
            ('الشقايا – الدبدبة – المتياهه', 'الشقايا – الدبدبة – المتياهه'),
            ('الصابرية – العرفجية', 'الصابرية – العرفجية'),
            ('الصبية', 'الصبية'), ('الصليبية الزراعية', 'الصليبية الزراعية'),
            ('الصليبيه السكنية', 'الصليبيه السكنية'),
            ('الصليبية الصناعية 2', 'الصليبية الصناعية 2'),
            ('الصليبيه الصناعية 1', 'الصليبيه الصناعية 1'),
            ('الصير وام المدفاع', 'الصير وام المدفاع'), ('العبدلى', 'العبدلى'),
            ('العبدلى وصخيبريات', 'العبدلى وصخيبريات'), ('العيون', 'العيون'),
            ('القيروان – جنوب الدوحة', 'القيروان – جنوب الدوحة'),
            ('المستثمر الاجنبى (منطقة العبدلى الاقتصادية )', 'المستثمر الاجنبى (منطقة العبدلى الاقتصادية )'),
            ('المطلاع وجال الاطراف', 'المطلاع وجال الاطراف'),
            ('النعايم الصناعية', 'النعايم الصناعية'),
            ('النهضة – شرق الصليبخات', 'النهضة – شرق الصليبخات'),
            ('امغره الصناعية', 'امغره الصناعية'), ('تيماء', 'تيماء'),
            ('جال الزور', 'جال الزور'), ('جزيرة ام المرادم', 'جزيرة ام المرادم'),
            ('جزيره ام النمل', 'جزيره ام النمل'), ('جزيرة بوبيان', 'جزيرة بوبيان'),
            ('جزيرة قارووه', 'جزيرة قارووه'), ('جزيرة كبر', 'جزيرة كبر'),
            ('جزيرة وربة', 'جزيرة وربة'), ('جنوب امغرة', 'جنوب امغرة'),
            ('شرق الجهراء', 'شرق الجهراء'), ('شرق تيماء', 'شرق تيماء'),
            ('شمال غرب الجهراء', 'شمال غرب الجهراء'),
            ('قلمة شايع والمناقيش', 'قلمة شايع والمناقيش'),
            ('كاظمة', 'كاظمة'), ('كبد والشق والضبعة', 'كبد والشق والضبعة'),
            ('معسكرات الجهراء', 'معسكرات الجهراء'), ('مقبرة', 'مقبرة'),
            ('مناطق نائية -الجهراء', 'مناطق نائية -الجهراء'),
        ],
        'محافظة مبارك الكبير': [
            ('مبارك الكبير', 'مبارك الكبير'), ('العدان', 'العدان'),
            ('القرين', 'القرين'), ('القصور', 'القصور'), ('المسيلة', 'المسيلة'),
            ('غرب أبو فطيرة', 'غرب أبو فطيرة'), ('الفنيطيس', 'الفنيطيس'),
            ('المسايل', 'المسايل'), ('الوسطى', 'الوسطى'),
            ('جنوب الوسطى', 'جنوب الوسطى'), ('صباح السالم', 'صباح السالم'),
            ('صبحان الصناعية', 'صبحان الصناعية'),
            ('ضاحية ابو فطيرة', 'ضاحية ابو فطيرة'), ('ابو الحصانية', 'ابو الحصانية'),
        ],
    }

def _get_all_regions(self):
    all_regions = []
    seen_regions = set()
    for areas in _get_governorate_areas().values():
        for area_val, area_label in areas:
            if area_val not in seen_regions:
                all_regions.append((area_val, area_label))
                seen_regions.add(area_val)
    return sorted(all_regions, key=lambda x: x[1])


# ==============================================================================
#  PROJECT MODEL
# ==============================================================================
class ProjectProject(models.Model):
    _inherit = 'project.project'

    sale_order_id = fields.Many2one('sale.order', string='Source Quotation', readonly=True)
    building_type = fields.Selection([('residential', 'سكن خاص'), ('investment', 'استثماري'), ('commercial', 'تجاري'), ('industrial', 'صناعي'), ('cooperative', 'جمعيات وتعاونيات'), ('mosque', 'مساجد'), ('hangar', 'مخازن / شبرات'), ('farm', 'مزارع')], string="نوع المبنى")
    service_type = fields.Selection([('new_construction', 'بناء جديد'), ('demolition', 'هدم'), ('modification', 'تعديل'), ('addition', 'اضافة'), ('addition_modification', 'تعديل واضافة'), ('supervision_only', 'إشراف هندسي فقط'), ('renovation', 'ترميم'), ('internal_partitions', 'قواطع داخلية'), ('shades_garden', 'مظلات / حدائق')], string="نوع الخدمة")
    
    # --- FIXED REGION & GOVERNORATE FIELDS ---
    governorate = fields.Selection(
        selection=[(gov, gov) for gov in _get_governorate_areas().keys()],
        string="المحافظة (Governorate)"
    )
    region = fields.Selection(_get_all_regions, string="المنطقة (Region)")
    
    @api.onchange('governorate')
    def _onchange_governorate(self):
        """Clears Region when Governorate changes"""
        self.region = False
        
    @api.constrains('governorate', 'region')
    def _check_valid_region(self):
        """Validates that the selected region belongs to the governorate"""
        for project in self:
            if project.governorate and project.region:
                valid_regions = [area[0] for area in _get_governorate_areas().get(project.governorate, [])]
                if project.region not in valid_regions:
                    raise ValidationError(_("المنطقة المختارة '%s' لا تتبع للمحافظة '%s'.") % (project.region, project.governorate))

    plot_no = fields.Char(string="رقم القسيمة")
    block_no = fields.Char(string="القطعة")
    street_no = fields.Char(string="الشارع")
    area = fields.Char(string="المساحة (Area)")

    # ==========================================
    # FULL TEAM ASSIGNMENT 
    # ==========================================
    architect_id = fields.Many2one('res.users', string="المهندس المعماري")
    accountant_id = fields.Many2one('res.users', string="المحاسبة")
    structural_id = fields.Many2one('res.users', string="المهندس الإنشائي")
    facade_draftsman_id = fields.Many2one('res.users', string="رسام الواجهات")
    secretary_id = fields.Many2one('res.users', string="السكرتارية")
    muni_draftsman_id = fields.Many2one('res.users', string="رسام البلدية")
    electrical_id = fields.Many2one('res.users', string="مهندس الكهرباء")
    draftsman_id = fields.Many2one('res.users', string="الرسام (صحي/مخططات)")

    workflow_started = fields.Boolean(default=False)
    step_2_triggered = fields.Boolean(default=False)
    step_3_triggered = fields.Boolean(default=False)
    step_4_triggered = fields.Boolean(default=False)
    step_5_triggered = fields.Boolean(default=False)
    step_6_triggered = fields.Boolean(default=False)
    step_8_triggered = fields.Boolean(default=False)
    step_9_triggered = fields.Boolean(default=False)
    step_10_triggered = fields.Boolean(default=False)

    def _get_project_stages(self):
        """ Helper to fetch all 7 columns safely """
        stages = self.env['project.task.type'].search([('project_ids', 'in', self.id)], order='sequence')
        s0 = stages[0].id if len(stages) > 0 else False # التصميم المبدئي
        s1 = stages[1].id if len(stages) > 1 else s0    # التعاقد والوثائق
        s2 = stages[2].id if len(stages) > 2 else s0    # المخطط الانشائي
        s3 = stages[3].id if len(stages) > 3 else s0    # الموافقات
        s4 = stages[4].id if len(stages) > 4 else s0    # التصميمات التفصيلية
        s5 = stages[5].id if len(stages) > 5 else s0    # الإشراف
        s6 = stages[6].id if len(stages) > 6 else s0    # إنهاء المشروع
        return s0, s1, s2, s3, s4, s5, s6

    def action_start_workflow(self):
        """ START PHASE 1 """
        self.ensure_one()
        if self.workflow_started:
            raise UserError(_("تم بدء سير العمل مسبقاً!"))
        
        s0, s1, s2, s3, s4, s5, s6 = self._get_project_stages()

        # Step 1 -> Column 1 (التصميم المبدئي)
        self._create_task('1. كروكي معماري', self.architect_id, s0, 'step_1')
        self.workflow_started = True

    def _trigger_next_workflow_step(self, completed_step):
        """ THE DOMINO EFFECT - Puts tasks in specific columns """
        s0, s1, s2, s3, s4, s5, s6 = self._get_project_stages()

        if completed_step == 'step_1' and not self.step_2_triggered:
            # Column 2 (التعاقد والوثائق)
            self._create_task('2. العقد وتحصيل الدفعة الاولي', self.accountant_id, s1)
            self._create_task('2. جمع الوثائق وتعبة النماذج', self.secretary_id, s1)
            # Column 3 (المخطط الانشائي)
            self._create_task('2. سيستم الاعمدة', self.structural_id, s2, 'step_2_cols')
            # Column 5 (التصميمات التفصيلية)
            self._create_task('2. الواجهات', self.facade_draftsman_id, s4)
            self.step_2_triggered = True

        elif completed_step == 'step_2_cols' and not self.step_3_triggered:
            # Column 4 (الموافقات)
            self._create_task('3. رسم المعماري للبلدية', self.muni_draftsman_id, s3, 'step_3')
            self.step_3_triggered = True

        elif completed_step == 'step_3' and not self.step_4_triggered:
            # Column 4 (الموافقات)
            self._create_task('4. ادخال المعاملة بلدية للاعتماد', self.secretary_id, s3, 'step_4')
            self.step_4_triggered = True

        elif completed_step == 'step_4' and not self.step_5_triggered:
            # Column 4 (الموافقات)
            self._create_task('5. اعتماد الرخصة من البلدية', self.secretary_id, s3, 'step_5')
            self.step_5_triggered = True

        elif completed_step == 'step_5' and not self.step_6_triggered:
            # Column 5 (التصميمات التفصيلية)
            self._create_task('6. تصميم الانشائي الكامل', self.structural_id, s4, 'step_6')
            self._create_task('7. تصميم مخطط الصحي', self.draftsman_id, s4)
            self._create_task('7. تصميم مخطط الكهرباء', self.electrical_id, s4)
            self.step_6_triggered = True

        elif completed_step == 'step_6' and not self.step_8_triggered:
            # Column 6 (الإشراف)
            self._create_task('8. تعهد الاشراف', self.secretary_id, s5, 'step_8')
            self.step_8_triggered = True

        elif completed_step == 'step_8' and not self.step_9_triggered:
            # Column 6 (الإشراف)
            self._create_task('9. الاشراف علي التنفيذ', self.structural_id, s5, 'step_9')
            self.step_9_triggered = True

        elif completed_step == 'step_9' and not self.step_10_triggered:
            # Column 7 (إنهاء المشروع)
            self._create_task('10. انهاء الاشراف', self.secretary_id, s6)
            self.step_10_triggered = True

    def _create_task(self, name, user, stage_id, workflow_step=False):
        """ Helper function to generate tasks cleanly """
        if not stage_id: return # Safegaurd
        val = {'name': name, 'project_id': self.id, 'stage_id': stage_id}
        if user: val['user_ids'] = [(4, user.id)]
        if workflow_step: val['workflow_step'] = workflow_step
        self.env['project.task'].create(val)


# ==============================================================================
#  PROJECT TASK MODEL
# ==============================================================================
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
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f"https://web.whatsapp.com/send?phone={cleaned_phone}&text={encoded_message}"
        return { 'type': 'ir.actions.act_url', 'url': whatsapp_url, 'target': 'new' }
