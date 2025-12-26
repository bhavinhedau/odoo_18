from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError

class ProjectMaster(models.Model):
    _name = "project.master"
    _description = "Project Master"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "code"
    _order = 'id desc'

    code = fields.Char(string="Code", required=True)
    name = fields.Char(string="Name", required=True)
    full_name = fields.Char(string="Full Name",required=True)
    start_date = fields.Date(string="Start Date",required=True)
    end_date = fields.Date(string="End Date",required=True)
    state_id = fields.Many2one("res.country.state", string="State",required=True)
    assign_user_ids = fields.One2many("project.assign.user", "project_id", string="Assigned Users", copy=True)
    equipment_ids = fields.One2many("project.assign.equipment", "project_id", string="Assigned Equipments", copy=True)
    plant_ids = fields.Many2many('plant.master', string='Assign Plants')
    division_ids = fields.Many2many('division.master', string='Division',required=True)
    closing_petrol = fields.Float(string='Opening Petrol',required=True)
    closing_diesel = fields.Float(string='Opening Diesel',required=True)
    sequence = fields.Char(string="Sequence", default='New')
    machinery_count = fields.Integer(
        compute='compute_machinery_count'
    )
    active = fields.Boolean(string='Active', default=True)


    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("sequence", "New") == "New":
                vals["sequence"] = seq.next_by_code("project.master") or "New"
        return super().create(vals_list)

    def compute_machinery_count(self):
        for record in self:
            record.machinery_count = self.env['machinery.progress'].search_count([
                ('project_id', '=', record.id)
            ])

    def action_view_machinery_list(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Machinery List",
            "res_model": "machinery.progress",
            "view_mode": "list",
            "domain": [("project_id", "=", self.id)],
            "context": {"default_project_id": self.id},
        }



class ProjectAssignEquipment(models.Model):
    _name = "project.assign.equipment"
    _description = "Project Assign Equipment"

    project_id = fields.Many2one("project.master", string="Project")
    equipment_ownership = fields.Selection([
        ('own', 'Own'),
        ('hired', 'Hired')
    ], string="Equipment Ownership", required=True)
    equipment_id = fields.Many2one("equipment.master", string="Code", required=True)
    registration_no = fields.Char(string="Registration No",related="equipment_id.registration_no")
    # equipment_name = fields.Char(string="Equipment Name",related="equipment_id.equipment_name" )
    equipment_maker = fields.Many2one('equipment.maker', string="Maker",related="equipment_id.equipment_maker")
    equipment_model = fields.Many2one('equipment.model', string="Model",related="equipment_id.equipment_model")
    equipment_capacity = fields.Many2one('equipment.capacity', string="Capacity",related="equipment_id.equipment_capacity")
    engine_no = fields.Char(string="Engine No",related="equipment_id.engine_no")
    chassis_no = fields.Char(string="Chassis No",related="equipment_id.chassis_no")
    project_start_date = fields.Date(string="Start Date Of Project", required=True)
    project_end_date = fields.Date(string="End Date Of Project", required=True)

    @api.constrains('equipment_id', 'project_id')
    def _check_duplicate_equipment_in_project(self):
        for rec in self:
            if rec.equipment_id and rec.project_id:
                domain = [
                    ('id', '!=', rec.id),
                    ('project_id', '=', rec.project_id.id),
                    ('equipment_id', '=', rec.equipment_id.id),
                ]
                if self.search(domain, limit=1):
                    raise ValidationError(
                        f"Equipment '{rec.equipment_id.display_name}' is already assigned to this project."
                    )

    @api.constrains('equipment_id', 'project_id', 'project_start_date', 'project_end_date')
    def _check_equipment_dates(self):
        for rec in self:
            if not (rec.equipment_id and rec.project_id and rec.project_start_date and rec.project_end_date):
                continue
            others = self.search([
                ('equipment_id', '=', rec.equipment_id.id),
                ('id', '!=', rec.id)
            ])
            for other in others:
                if not (other.project_start_date and other.project_end_date):
                    continue
                if rec.project_start_date <= other.project_end_date and rec.project_end_date >= other.project_start_date:
                    raise ValidationError(
                        f"Equipment {rec.equipment_id.display_name} is already assigned to project "
                        f"{other.project_id.code} - {other.project_id.name}."
                    )
class ProjectAssignUser(models.Model):
    _name = "project.assign.user"
    _description = "Project Assign User"

    project_id = fields.Many2one("project.master", string="Project")
    user_id = fields.Many2one('res.users', string='Email', required=True)
    name = fields.Char(string="Name", related='user_id.name')
    designation = fields.Char(string="Designation", related='user_id.designation')
    phone = fields.Char(string="Phone", related='user_id.phone')
    # form_id = fields.Many2one('ir.ui.view')
    # model_id = fields.Many2one('ir.model',string='Form Name',required=True)
    # rights = fields.Selection([
    #     ('1', 'DATA ENTRY'),
    #     ('2', 'DATA APPROVAL'),
    #     ('3', 'DATA ENTRY/APPROVAL'),
    # ], string="Rights")
    froms = fields.Selection([
        ('1', 'Machinery Progress'),
    ], string="Form Name",default='1' , required=True)
    can_edit = fields.Boolean(string="Data Entry")
    can_approve = fields.Boolean(string="Data Approval")

    @api.constrains('user_id', 'project_id')
    def _check_duplicate_user(self):
        for rec in self:
            if rec.user_id and rec.project_id:
                domain = [
                    ('id', '!=', rec.id),
                    ('project_id', '=', rec.project_id.id),
                    ('user_id', '=', rec.user_id.id),
                ]
                if self.search(domain, limit=1):
                    raise ValidationError(
                        f"User '{rec.user_id.name}' is already assigned to this project."
                    )

class DivisionMaster(models.Model):
    _name = 'division.master'
    _description = 'Division Master'

    name = fields.Char(string='Division Name', required=True)

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            exists = self.search([('name', '=', record.name), ('id', '!=', record.id)], limit=1)
            if exists:
                raise ValidationError(_('The name "%s" already exists!') % record.name)
