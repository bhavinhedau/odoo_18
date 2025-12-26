from odoo import models, fields

class CustomerSeries(models.Model):
    _name = 'customer.series'
    _description = 'Customer Series'

    name = fields.Char(string='Series Name', required=True)
    code = fields.Integer(string='Series Code', required=True)
