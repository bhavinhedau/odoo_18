from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class MachineryProgress(models.Model):
    _name = "machinery.progress"
    _description = "Machinery Progress"
    _rec_name = "name"
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Sequence', default='New', copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_approval', 'In Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', tracking=True, string='Status')
    progress_line_ids = fields.One2many("machinery.progress.line", "progress_id", string="Progress Lines")
    project_id = fields.Many2one("project.master", string="Project Code", required=True)
    project_name = fields.Char(string="Project Name", related='project_id.name')
    report_send_by = fields.Many2one('res.users', string='Report Send By', default=lambda self: self.env.user)
    report_date = fields.Date(string="Report Date", default=fields.Date.context_today,required=True)
    opening_petrol = fields.Float(string='Opening Petrol', compute="_compute_opening_fuel", store=True,required=True)
    opening_diesel = fields.Float(string='Opening Diesel', compute="_compute_opening_fuel", store=True)
    closing_petrol = fields.Float(string='Closing Petrol', compute="_compute_closing_fuel",required=True)
    closing_diesel = fields.Float(string='Closing Diesel', compute="_compute_closing_fuel")
    petrol_received = fields.Float(string='Petrol Received', digits=(16, 2),required=True)
    diesel_received = fields.Float(string='Diesel Received', digits=(16, 2),required=True)
    working_hrs = fields.Float(string='Working Hours', compute="_compute_totals", store=True)
    idle_hrs = fields.Float(string='Idle Hours')
    breakdown_hrs = fields.Float(string='Break Down Hours')
    remarks = fields.Text(string='Remarks', tracking=True)
    can_edit = fields.Boolean(string="Can Edit", compute="_compute_no_edit_approve")
    can_approve = fields.Boolean(string="Can Approve", compute="_compute_no_edit_approve")

    t_utilization_km = fields.Float(string="Total Utilization Km",
                                    compute='_compute_utilization_km_hr', readonly=True
                                    )
    t_utilization_hr = fields.Float(string="Total Utilization Hr",
                                    compute='_compute_utilization_km_hr', readonly=True
                                    )

    @api.depends('progress_line_ids.utilization_km', 'progress_line_ids.utilization_hr')
    def _compute_utilization_km_hr(self):
        for rec in self:
            rec.t_utilization_km = sum(rec.progress_line_ids.mapped('utilization_km'))
            rec.t_utilization_hr = sum(rec.progress_line_ids.mapped('utilization_hr'))

    def _compute_no_edit_approve(self):
        for rec in self:
            user = self.env.user
            if user and rec.project_id:
                assign = self.env['project.assign.user'].search([
                    ('project_id', '=', rec.project_id.id),
                    ('user_id', '=', user.id),
                    ('froms', '=', '1'),
                ], limit=1)
                if assign:
                    rec.can_edit = assign.can_edit
                    rec.can_approve = assign.can_approve
                else:
                    rec.can_edit = False
                    rec.can_approve = False
            else:
                rec.can_edit = True
                rec.can_approve = False

    def _check_create_access(self, vals):
        user = self.env.user
        project_id = vals.get("project_id")
        if not project_id:
            return
        assign = self.env['project.assign.user'].search([
            ('project_id', '=', project_id),
            ('user_id', '=', user.id),
            ('froms', '=', '1'),
        ], limit=1)
        if not assign or not assign.can_edit:
            raise UserError("You are not allowed to create machinery progress for this project.")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        seq = self.env["ir.sequence"]
        seq_code = "machinery.progress"
        for rec in records:
            if rec.name == 'New':
                rec.name = seq.next_by_code(seq_code) or "New"
        if records:
            records._post_machine_form_notification()
        return records

    def action_send_for_approval(self):
        self.write({'state': 'in_approval'})

    def action_draft(self):
        return {
            'name': 'Write Send Back Remarks',
            'type': 'ir.actions.act_window',
            'res_model': 'machinery.draft.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id}
        }

    def action_approve(self):
        for rec in self:
            rec.write({'state': 'approved'})
            if rec.project_id:
                project = rec.project_id
                project.sudo().write({
                    'closing_petrol': rec.closing_petrol,
                    'closing_diesel': rec.closing_diesel,
                })
            for line in rec.progress_line_ids:
                equipment = line.equipment_id
                if line.unit_of_utilization.name == 'KMs' and line.closing_reading_km:
                    equipment.sudo().write({
                        'odometer': line.closing_reading_km
                    })
                if line.unit_of_utilization.name == 'HRs' and line.closing_reading_hr:
                    equipment.sudo().write({
                        'hourmeter': line.closing_reading_hr
                    })

    def action_reject(self):
        self.write({'state': 'rejected'})

    @api.onchange('project_id')
    def create_lines(self):
        for rec in self:
            rec.progress_line_ids = [(5, 0, 0)]
            if not rec.project_id:
                rec.progress_line_ids = [(5, 0, 0)]
                continue

            assigned_equipment = self.env['project.assign.equipment'].search([
                ('project_id', '=', rec.project_id.id)
            ])
            lines = []

            if not assigned_equipment:
                rec.progress_line_ids = lines

            for item in assigned_equipment:
                equipment = item.equipment_id

                for unit in equipment.unit_of_utilization:
                    # Decide opening reading
                    # opening = 0.0
                    # if unit.name == "HRs":
                    #     opening = equipment.hourmeter
                    # elif unit.name == "KMs":
                    #     opening = equipment.odometer

                    lines.append((0, 0, {
                        'equipment_id': equipment.id,
                        'unit_of_utilization': unit.id,
                        # 'opening_reading': opening,
                    }))

            rec.progress_line_ids = lines

    @api.onchange('project_id')
    def _compute_opening_fuel(self):
        for rec in self:
            rec.opening_petrol = rec.project_id.closing_petrol
            rec.opening_diesel = rec.project_id.closing_diesel

    @api.depends(
        'opening_petrol', 'opening_diesel',
        'petrol_received', 'diesel_received',
        'progress_line_ids.fuel_issue',
        'progress_line_ids.fuel_type'
    )
    def _compute_closing_fuel(self):
        for rec in self:
            petrol_issue = sum(rec.progress_line_ids.filtered(lambda l: l.fuel_type == 'petrol').mapped('fuel_issue'))
            diesel_issue = sum(rec.progress_line_ids.filtered(lambda l: l.fuel_type == 'diesel').mapped('fuel_issue'))

            rec.closing_petrol = (rec.opening_petrol + rec.petrol_received) - petrol_issue
            rec.closing_diesel = (rec.opening_diesel + rec.diesel_received) - diesel_issue

    @api.depends(
        "progress_line_ids.working_hours",
        "progress_line_ids.idle_hours",
        "progress_line_ids.breakdown_hours",
    )
    def _compute_totals(self):
        for rec in self:
            rec.working_hrs = sum(rec.progress_line_ids.mapped("working_hours"))
            rec.idle_hrs = sum(rec.progress_line_ids.mapped("idle_hours"))
            rec.breakdown_hrs = sum(rec.progress_line_ids.mapped("breakdown_hours"))

    @api.constrains('report_date')
    def _check_report_date(self):
        for rec in self:
            if rec.report_date and rec.report_date > fields.Date.today():
                raise ValidationError("Report Date must be less than or equal to today's date.")

    def action_view_progress_lines(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Progress Lines",
            "res_model": "machinery.progress.line",
            "view_mode": "list",
            "domain": [("progress_id", "=", self.id)],
            "context": {"default_progress_id": self.id},
        }

    @api.constrains('progress_line_ids')
    def _check_total_hours(self):
        for rec in self:
            for line in rec.progress_line_ids:
                if line.closing_reading_km < line.opening_reading_km:
                    raise ValidationError(
                        f"Equipment {line.equipment_id.display_name}: "
                        f"Closing Reading ({line.closing_reading_km:,.2f}) cannot be less than "
                        f"Opening Reading ({line.opening_reading_km:,.2f})."
                    )

                if line.closing_reading_hr < line.opening_reading_hr:
                    raise ValidationError(
                        f"Equipment {line.equipment_id.display_name}: "
                        f"Closing Reading cannot be less than Opening Reading."
                    )

    def _post_machine_form_notification(self):
        MailMessage = self.env['mail.message']
        odoo_bot_partner_id = self.env.ref('base.user_root').partner_id.id
        subtype_xml_id = self.env.ref('mail.mt_comment').id
        action = self.env.ref("equipment_management_system.action_machinery_progress")

        for rec in self:
            partner_ids = []

            if rec.project_id:
                project = rec.project_id
                user_lines = project.assign_user_ids

                for line in user_lines:
                    if line.user_id.partner_id:
                        partner_ids.append(line.user_id.partner_id.id)

                link = (
                    f"/web#action={action.id}"
                    f"&model={self._name}"
                    f"&id={rec.id}"
                    f"&view_type=form"
                )

                final_message_body = (
                    f'New machinery progress form <b>{rec.name}</b> has been created. '
                    f'Click here to view: <a href="{link}" target="_blank">Open Record</a>.'
                )

                message = MailMessage.create({
                    'model': self._name,
                    'res_id': rec.id,
                    'body': final_message_body,
                    'author_id': odoo_bot_partner_id,
                    'message_type': 'comment',
                    'subtype_id': subtype_xml_id,
                })

                notifications = []
                for pid in partner_ids:
                    notifications.append((0, 0, {
                        'res_partner_id': pid,
                        'notification_type': 'inbox',
                        'mail_message_id': message.id,
                        'is_read': False,
                    }))

                if notifications:
                    message.write({'notification_ids': notifications})


class MachineryProgressLine(models.Model):
    _name = "machinery.progress.line"
    _description = "Machinery Progress Line"
    _order = 'id desc'

    progress_id = fields.Many2one("machinery.progress", string="Progress", ondelete="cascade")
    # date = fields.Date(string="Date", default=fields.Date.context_today)
    project_id = fields.Many2one("project.master", string="Project Code", related='progress_id.project_id',required=True)
    state = fields.Selection(
        related='progress_id.state',
        string='Status',
        store=True,
        readonly=True,
    )
    project_name = fields.Char(string="Project Name", related='project_id.name')
    available_equipment_ids = fields.Many2many("equipment.master", compute="_compute_available_equipment_ids",
                                               string="Available Equipments")
    equipment_id = fields.Many2one('equipment.master', string="Equipment Code")
    registration_no = fields.Char(string="Registration No", related="equipment_id.registration_no")
    # equipment_name = fields.Char(string="Name", related="equipment_id.equipment_name")
    fuel_type = fields.Selection([
        ('diesel', 'Diesel'),
        ('petrol', 'Petrol'),
    ],
        string="Fuel Type",
        related='equipment_id.fuel_type', store=True)
    equipment_condition = fields.Selection([('breakdown', 'BREAKDOWN'), ('idle', 'IDLE'), ('working', 'WORKING')],
                                           string='EQUIPMENT CONDITION', default='working')
    purpose = fields.Many2one('equipment.purpose', string="Equipment Purpose",
                              domain="[('id', 'in', available_purpose_ids)]",required=True)
    available_purpose_ids = fields.Many2many(
        'equipment.purpose',
        compute='_compute_available_purpose_ids'
    )
    opening_reading_km = fields.Float(string='KM Opening Reading', compute='_compute_opening_reading', default=0,
                                      store=True)
    opening_reading_hr = fields.Float(string='HR Opening Reading', compute='_compute_opening_reading', default=0,
                                      store=True)
    closing_reading_km = fields.Float(string='KM Closing Reading',required=True)
    closing_reading_hr = fields.Float(string='HR Closing Reading',required=True)
    utilization_km = fields.Float(string='KM Utilization', compute='_compute_utilization')
    utilization_hr = fields.Float(string='HR Utilization', compute='_compute_utilization')
    unit_of_utilization = fields.Many2one('unit.utilization', string="Unit of Utilization")
    unit_of_utilization_name = fields.Char(string="Unit of Utilization Name", related='unit_of_utilization.name')
    fuel_issue = fields.Float(string="Fuel Issue")
    working_hours = fields.Float(string='Working Hours', default=0)
    breakdown_hours = fields.Float(string='Break Down Hours', default=0)
    idle_hours = fields.Float(string='Idle Hours', compute='_compute_idle_hours', default=24)
    remarks = fields.Text(string='Remarks')
    report_send_by = fields.Many2one('res.users', string='Report Send By', related='progress_id.report_send_by')
    report_date = fields.Date(string="Report Date", related='progress_id.report_date')
    report_create_date = fields.Datetime(string="Report Create Date", related='progress_id.create_date')


    @api.constrains('working_hours', 'breakdown_hours')
    def _check_total_hours(self):
        # print("_check_total_hours")
        for rec in self:
            # print((abs(rec.working_hours)), (abs(rec.breakdown_hours)), (abs(rec.idle_hours)))
            if rec.progress_id.state in ('draft'):
                if rec.equipment_condition in ('breakdown','idle'):
                    if rec.working_hours > 0:
                        # print(rec.working_hours)
                        raise ValidationError(
                            "[%s | Reg No: %s] Working hours cannot be greater than 0 when equipment is in %s condition."
                            % (rec.equipment_id.display_name or 'Unknown Equipment',
                               rec.registration_no or 'N/A',
                               rec.equipment_condition)
                        )
                    if rec.closing_reading_hr != rec.opening_reading_hr:
                        raise ValidationError(
                            "[%s | Reg No: %s] Closing hours cannot be greater than Opening hours when equipment is in %s condition."
                            % (rec.equipment_id.display_name or 'Unknown Equipment',
                               rec.registration_no or 'N/A',
                               rec.equipment_condition)
                        )


                if (abs(rec.working_hours)) + (abs(rec.breakdown_hours)) + (abs(rec.idle_hours)) > 24:
                    raise ValidationError(
                        "[%s | Reg No: %s] Total hours (working + breakdown + idle) cannot exceed 24 hours."
                        % (rec.equipment_id.display_name or 'Unknown Equipment',
                           rec.registration_no or 'N/A')
                    )


    @api.depends('working_hours', 'breakdown_hours', 'closing_reading_hr')
    def _compute_idle_hours(self):
        # print("_compute_idle_hours")
        for record in self:
            hours = 24.0 - record.working_hours - record.breakdown_hours
            if hours > 0:
                record.idle_hours = hours
            else:
                record.idle_hours = 0

    @api.depends('project_id')
    def _compute_available_equipment_ids(self):
        # print("_compute_available_equipment_ids")
        for record in self:
            if record.project_id:
                assigned_equipments = self.env['project.assign.equipment'].search([
                    ('project_id', '=', record.project_id.id)
                ]).mapped('equipment_id')
                record.available_equipment_ids = assigned_equipments
            else:
                record.available_equipment_ids = False

    @api.depends('equipment_id')
    def _compute_available_purpose_ids(self):
        # print("_compute_available_purpose_ids")
        for record in self:
            if record.equipment_id:
                record.available_purpose_ids = record.equipment_id.equipment_purpose_ids
            else:
                record.available_purpose_ids = False

    @api.depends('equipment_id')
    def _compute_opening_reading(self):
        # print("_compute_opening_reading")
        for rec in self:
            rec.opening_reading_hr = 0.0
            rec.opening_reading_km = 0.0

            if not rec.equipment_id or not rec.unit_of_utilization:
                continue

            if rec.unit_of_utilization.name == "HRs":
                rec.opening_reading_hr = rec.equipment_id.hourmeter or 0.0

            elif rec.unit_of_utilization.name == "KMs":
                rec.opening_reading_km = rec.equipment_id.odometer or 0.0


    @api.depends(
        'opening_reading_km',
        'closing_reading_km',
        'opening_reading_hr',
        'closing_reading_hr'
    )
    def _compute_utilization(self):
        # print("_compute_utilization")
        for rec in self:

            if rec.closing_reading_km and rec.opening_reading_km:
                rec.utilization_km = rec.closing_reading_km - rec.opening_reading_km
            else:
                rec.utilization_km = 0.0

            if rec.closing_reading_hr and rec.opening_reading_hr and rec.unit_of_utilization.name == 'HRs':
                rec.utilization_hr = rec.closing_reading_hr - rec.opening_reading_hr
                # rec.working_hours = rec.closing_reading_hr - rec.opening_reading_hr
            else:
                rec.utilization_hr = 0.0
                # rec.working_hours = 0.0

    @api.onchange('closing_reading_hr')
    def _compute_working_hours(self):
        # print("_compute_working_hours")
        for rec in self:
            if rec.closing_reading_hr > 0 :
                rec.working_hours = rec.closing_reading_hr - rec.opening_reading_hr
            else:
                rec.working_hours = 0.0


    # # @api.onchange('equipment_condition', 'utilization_hr')
    # # def _onchange_condition_hours(self):
    # #     for rec in self:
    # #         rec.working_hours = 0.0
    # #
    # #         if rec.equipment_condition == 'working':
    # #             rec.working_hours = rec.utilization_hr

    @api.onchange('equipment_condition')
    def _unit_of_utilizationand_condition(self):
        # print("_unit_of_utilizationand_condition")
        for rec in self:
            if rec.unit_of_utilization and rec.equipment_condition:
                if rec.equipment_condition in ('breakdown','idle') and rec.unit_of_utilization.name == 'HRs':
                    rec.closing_reading_hr = rec.opening_reading_hr

                if rec.equipment_condition in ('breakdown','idle') and rec.unit_of_utilization.name == 'KMs':
                    rec.closing_reading_km = rec.opening_reading_km
                if rec.equipment_condition == 'breakdown':
                    rec.working_hours = 0.0
                    rec.idle_hours = 0.0
                    rec.breakdown_hours = 24
                    rec.purpose = self.env.ref('equipment_management_system.equipment_purpose_no_work').id


    #             # rec.write({
    #             #     'working_hours': 0.0,
    #             #     'idle_hours': 0.0,
    #             #     'breakdown_hours': 24,
    #             # })
    #
    # # on change input values distro
    # @api.onchange('equipment_id', 'equipment_condition', 'unit_of_utilization')
    # def _onchange_equipment_config(self):
    #     print("_onchange_equipment_config")
    #     for rec in self:
    #         rec.closing_reading_km = 0.0
    #         rec.closing_reading_hr = 0.0
    #         rec.fuel_issue = 0.0
    #         rec.working_hours = 0.0
    #         rec.breakdown_hours = 0.0
    #         # rec.unit_of_utilization = ''
    #
    #
    #
    #
