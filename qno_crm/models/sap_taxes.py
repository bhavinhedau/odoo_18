from odoo import models, fields, api


class SapTaxes(models.Model):
    _name='sap.taxes'
    _rec_name='name'
    _description = 'SAP Taxes'
    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    active = fields.Boolean(string="Active",default=True)
