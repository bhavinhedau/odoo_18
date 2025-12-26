from odoo import models, fields

class CustomerGroup(models.Model):
    _name = 'customer.group'
    _description = 'Customer Group'
    _rec_name='group_name'

    code = fields.Integer(string='Code', required=True)
    group_name = fields.Char(string='Group Name', required=True)
    grouptype = fields.Selection([
        ('c', 'Customer'),
        ('s', 'Supplier')
    ], string='Group Type', required=True)
    locked = fields.Selection([
        ('Y', 'Y'),
        ('N', 'N')
    ], string='Locked', default='N', required=True)

