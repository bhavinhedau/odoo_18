from odoo import models, fields


class ResUsersInherit(models.Model):
    _inherit = 'res.users'
    _rec_name = 'email'

    designation = fields.Char(string="Designation")