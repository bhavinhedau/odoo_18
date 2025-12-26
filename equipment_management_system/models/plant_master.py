from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PlantMaker(models.Model):
    _name = 'plant.maker'
    _description = 'Plant Maker'

    name = fields.Char(string='Plant Name', required=True)

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            exists = self.search([('name', '=', record.name), ('id', '!=', record.id)], limit=1)
            if exists:
                raise ValidationError(_('The name "%s" already exists!') % record.name)

class MakerMasterName(models.Model):
    _name = 'maker.master.name'
    _description = 'Maker Master Name'

    name = fields.Char(string='Name', required=True)
    short_name = fields.Char(string='Short Name', required=True)

    # _name_unique = models.Constraint(
    #     'unique(name)',
    #     'This name already exists! Please choose a different one.'
    # )
    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            exists = self.search([('name', '=', record.name), ('id', '!=', record.id)], limit=1)
            if exists:
                raise ValidationError(_('The name "%s" already exists!') % record.name)

class PlantModel(models.Model):
    _name = 'plant.model'
    _description = 'Plant Model'

    name = fields.Char(string='Plant Model Name', required=True)

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            exists = self.search([('name', '=', record.name), ('id', '!=', record.id)], limit=1)
            if exists:
                raise ValidationError(_('The name "%s" already exists!') % record.name)

class PlantCapacity(models.Model):
    _name = 'plant.capacity'
    _description = 'Plant Capacity'

    name = fields.Char(string='Plant Model Capacity', required=True)

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            exists = self.search([('name', '=', record.name), ('id', '!=', record.id)], limit=1)
            if exists:
                raise ValidationError(_('The name "%s" already exists!') % record.name)

class PlantCategory(models.Model):
    _name = 'plant.category'
    _description = 'Plant Category'

    name = fields.Char(string='Plant Category Name', required=True)
    short_name = fields.Char(string='Short Name', required=True)

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            exists = self.search([('short_name', '=', record.short_name), ('id', '!=', record.id)], limit=1)
            if exists:
                raise ValidationError(_('The short name "%s" already exists!') % record.short_name)

class PlantMaster(models.Model):
    _name = 'plant.master'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Plant Management'
    _rec_name = 'plant_code'
    _order = 'id desc'


    plant_code = fields.Char(string='Plant Code', default='New')
    plant_name = fields.Char(string='Plant Name', required=True)
    serial_no = fields.Char(string='Serial No',required=True)
    plant_category_id = fields.Many2one('plant.category',string='Plant Categories',required=True)
    maker_id = fields.Many2one('maker.master.name',string='Make',required=True)
    plant_model_id = fields.Many2one('plant.model',string='Model',required=True)
    capacity = fields.Many2one('plant.capacity',string='Capacity',required=True)
    manufacturing_date = fields.Date(string='Manufacturing Date',required=True)
    date_of_purchase = fields.Date(string='Date of Purchase',required=True)
    purchase_cost = fields.Float(string='Purchase Cost',required=True)
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Char(string="Sequence", default='New')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.sequence == "New":
                rec.sequence = self.env["ir.sequence"].next_by_code("plant.master") or "New"
            if rec.serial_no:
                rec.serial_no = rec.serial_no.upper()
            if not rec.plant_code or rec.plant_code == "New":
                maker_code = (rec.maker_id.short_name or "").upper()
                capacity_code = (rec.capacity.name or "").upper()
                serial = rec.serial_no or ""
                prefix = "P"

                final_code = f"{prefix}{maker_code}{capacity_code}{serial}"
                rec.plant_code = final_code

        return records