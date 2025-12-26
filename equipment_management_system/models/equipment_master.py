from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from pkg_resources import require


class EquipmentMaster(models.Model):
    _name = 'equipment.master'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Equipment Master"
    _rec_name = 'equipment_code'
    _order = 'id desc'

    equipment_ownership = fields.Selection([
        ('own', 'Own'),
        ('hired', 'Hired')
    ], string="Equipment Ownership", default='own',required=True)

    # own and hired common
    cost_center_name = fields.Char(string="Cost Center Name")
    cost_center_code = fields.Char(string="Cost Center Code")
    manufacturing_date = fields.Date(string="Manufacturing Date",required=True)
    equipment_code = fields.Char(string="Equipment code", default='New')
    sequence = fields.Char(string="Sequence", default='New')
    # equipment_name = fields.Char(string="Equipment Name N",compute="_compute_name_from_type")
    equipment_capacity = fields.Many2one('equipment.capacity', string="Equipment Capacity",
                                         related="equipment_model.equipment_capacity", readonly=False,required=True)
    equipment_maker = fields.Many2one('equipment.maker', string="Equipment Maker")
    equipment_model = fields.Many2one('equipment.model', string="Equipment Model",
                                      domain="[('equipment_maker', '=', equipment_maker)]",required=True)
    registration_no = fields.Char(string="Registration No",required=True)
    equipment_purpose_ids = fields.Many2many('equipment.purpose', string="Equipment Purpose",
                                             related="equipment_model.equipment_purpose_ids", readonly=False,required=True)
    unit_of_utilization = fields.Many2many('unit.utilization', string="Applicable Unit of Utilization", required=True)
    standard_fuel_average = fields.Float(string="Standard Fuel Average",required=True)
    starting_meter_reading = fields.Float(string="Starting Meter Reading",required=True)
    active = fields.Boolean(string='Active', default=True)
    equipment_category = fields.Selection([
        ('key', 'Key Equipment'),
        ('secondary', 'Secondary Equipment')
    ], string="Equipment Category", default='key',required=True)

    # own
    engine_no = fields.Char(string="Engine No",required=True)
    purchase_cost = fields.Float(string="Purchase Cost",required=True)
    equipment_file_no = fields.Char(string="Equipment Document File No",required=True)
    chassis_no = fields.Char(string="Chassis No",required=True)
    date_of_purchase = fields.Date(string="Date of Purchase",required=True)
    odometer = fields.Float(string="Starting KMR", tracking=True,required=True)
    hourmeter = fields.Float(string="Starting HRS", tracking=True,required=True)
    service_reminder_kmr = fields.Float(string="Service Reminder In KMR",required=True)
    service_reminder_hmr = fields.Float(string="Service Reminder In HMR",required=True)
    last_service_kmr = fields.Float(string="Last Service KMR",required=True)
    last_service_hmr = fields.Float(string="Last Service HMR",required=True)
    # location_code = fields.Char(string="Location Code")
    equipment_type = fields.Many2one('equipment.type', string="Equipment Type",required=True)
    delivery_project = fields.Many2one('project.master', string="Equipment Delivery Project",required=True)
    fuel_type = fields.Selection([
        ('diesel', 'Diesel'),
        ('petrol', 'Petrol'),
    ],
        string="Fuel Type",
        default='diesel',
        required=True, )

    # hired
    vendor_name = fields.Char(string="Vendor Name",required=True)
    hired_date = fields.Date(string="Hired Date",required=True)
    hired_cost = fields.Float(string="Hired Cost",required=True)
    # hired_equipment_type = fields.Many2one('hired.equipment.type', string="Hired Equipment Name")

    show_hrs_fields = fields.Boolean(compute="_compute_utilization_visibility")
    show_kms_fields = fields.Boolean(compute="_compute_utilization_visibility")

    @api.depends('unit_of_utilization')
    def _compute_utilization_visibility(self):
        for record in self:
            selected_names = record.unit_of_utilization.mapped('name')
            record.show_hrs_fields = 'HRs' in selected_names
            record.show_kms_fields = 'KMs' in selected_names

    def create(self, vals_list):
        records = super().create(vals_list)

        for rec in records:
            # ---------------- OWN EQUIPMENT ----------------
            if rec.equipment_ownership == 'own' and rec.equipment_type:
                type_rec = rec.equipment_type

                new_num = type_rec.sequence or 1
                rec.equipment_code = f"{type_rec.prefix}{str(new_num).zfill(3)}"

                type_rec.sequence = new_num + 1

            # ---------------- HIRED EQUIPMENT ----------------
            if rec.equipment_ownership == 'hired' and rec.equipment_type:
                type_rec = rec.equipment_type

                new_num = type_rec.h_sequence or 1
                rec.equipment_code = f"{type_rec.h_prefix}{str(new_num).zfill(3)}"

                type_rec.h_sequence = new_num + 1

            # ---------------- SEQUENCE FIELD ----------------
            if rec.sequence == 'New':
                rec.sequence = self.env["ir.sequence"].next_by_code("equipment.master") or "New"

        return records

    # @api.model_create_multi
    # def create(self, vals_list):
    #     seq = self.env["ir.sequence"]
    #     for vals in vals_list:
    #         if vals.get("sequence", "New") == "New":
    #             vals["sequence"] = seq.next_by_code("equipment.master") or "New"
    #
    #     for vals in vals_list:
    #
    #         # ---------------- OWN EQUIPMENT ----------------
    #         if vals.get('equipment_ownership') == 'own' and vals.get('equipment_type'):
    #             type_id = vals['equipment_type']
    #             type_rec = self.env['equipment.type'].browse(type_id)
    #
    #             # Retrieve last number
    #             last = self.search([('equipment_type', '=', type_id)],
    #                                order="equipment_code desc", limit=1)
    #
    #             if last and last.equipment_code:
    #                 last_num = int(last.equipment_code[-3:])
    #             else:
    #                 last_num = 0
    #
    #             new_num = last_num + 1
    #
    #             # Assign final code
    #             vals['equipment_code'] = f"{type_rec.prefix}{str(new_num).zfill(3)}"
    #
    #             # Increase sequence in equipment.type
    #             type_rec.sequence = new_num
    #
    #         # ---------------- HIRED EQUIPMENT ----------------
    #         if vals.get('equipment_ownership') == 'hired' and vals.get('hired_equipment_type'):
    #             type_id = vals['hired_equipment_type']
    #             type_rec = self.env['equipment.type'].browse(type_id)
    #
    #             # Retrieve last number
    #             last = self.search([('hired_equipment_type', '=', type_id)],
    #                                order="equipment_code desc", limit=1)
    #
    #             if last and last.equipment_code:
    #                 last_num = int(last.equipment_code[-3:])
    #             else:
    #                 last_num = 0
    #
    #             new_num = last_num + 1
    #
    #             # Assign final code
    #             vals['equipment_code'] = f"{type_rec.prefix}{str(new_num).zfill(3)}"
    #
    #             # Increase sequence in hired.equipment.type
    #             type_rec.sequence = new_num
    #
    #     return super().create(vals_list)

    # def _compute_name_from_type(self):
    #     for rec in self:
    # if rec.equipment_ownership == 'hired' and rec.hired_equipment_type:
    #     rec.equipment_name = rec.hired_equipment_type.name
    # if rec.equipment_type:
    #     rec.equipment_name = rec.equipment_type.name
    # else:
    #     rec.equipment_name = None


# class EquipmentName(models.Model):
#     _name = 'equipment.name'
#     _description = "Equipment Name"
#
#     name = fields.Char(string="Name", required=True)

class EquipmentType(models.Model):
    _name = 'equipment.type'
    _description = "Equipment Type"
    _order_by = 'id'

    name = fields.Char(string="Name", required=True)
    description = fields.Char(string="Description")
    prefix = fields.Char(string="Own Equipment Prefix", required=True)
    sequence = fields.Integer(string="Own Equipment Sequence", default=1)
    h_prefix = fields.Char(string="Hired Prefix", required=True)
    h_sequence = fields.Integer(string="Hired Equipment Sequence", default=1)

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            exists = self.search([('name', '=', record.name), ('id', '!=', record.id)], limit=1)
            if exists:
                raise ValidationError(_('The name "%s" already exists!') % record.name)


# class HiredEquipmentType(models.Model):
#     _name = 'hired.equipment.type'
#     _description = "Hired Equipment Name"
#
#     name = fields.Char(string="Name", required=True)
#     description = fields.Char(string="Description")
#     prefix = fields.Char(string="Prefix")
#     sequence = fields.Integer(string="Sequence",default=1)

class EquipmentMaker(models.Model):
    _name = 'equipment.maker'
    _description = "Equipment Maker"

    name = fields.Char(string="Name", required=True)
    description = fields.Char(string="Description")

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            exists = self.search([('name', '=', record.name), ('id', '!=', record.id)], limit=1)
            if exists:
                raise ValidationError(_('The name "%s" already exists!') % record.name)


class EquipmentModel(models.Model):
    _name = 'equipment.model'
    _description = "Equipment Model"

    name = fields.Char(string="Name", required=True)
    description = fields.Char(string="Description")
    equipment_maker = fields.Many2one('equipment.maker', string="Equipment Maker",required=True)
    equipment_capacity = fields.Many2one('equipment.capacity', string="Equipment Capacity",required=True)
    equipment_purpose_ids = fields.Many2many('equipment.purpose', string="Equipment Purpose",required=True)

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            exists = self.search([('name', '=', record.name), ('id', '!=', record.id)], limit=1)
            if exists:
                raise ValidationError(_('The name "%s" already exists!') % record.name)


class EquipmentCapacity(models.Model):
    _name = 'equipment.capacity'
    _description = "Equipment Capacity"

    name = fields.Char(string="Name", required=True)
    description = fields.Char(string="Description")

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            exists = self.search([('name', '=', record.name), ('id', '!=', record.id)], limit=1)
            if exists:
                raise ValidationError(_('The name "%s" already exists!') % record.name)


class EquipmentPurpose(models.Model):
    _name = 'equipment.purpose'
    _description = "Equipment Purpose"

    name = fields.Char(string="Name", required=True)
    description = fields.Char(string="Description")

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            exists = self.search([('name', '=', record.name), ('id', '!=', record.id)], limit=1)
            if exists:
                raise ValidationError(_('The name "%s" already exists!') % record.name)


class UnitOfUtilization(models.Model):
    _name = 'unit.utilization'
    _description = "APPLICABLE UNIT OF UTILIZATION"

    name = fields.Char(string="Name", required=True)
    description = fields.Char(string="Description")

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            exists = self.search([('name', '=', record.name), ('id', '!=', record.id)], limit=1)
            if exists:
                raise ValidationError(_('The name "%s" already exists!') % record.name)
