from odoo import models, fields, api


class SapWarehouse(models.Model):
    _name='sap.warehouse'
    _rec_name='name'
    _description = 'SAP Warehouse'

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    active = fields.Boolean(string="Active",default=True)

