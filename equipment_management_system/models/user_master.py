from odoo import models, fields

class UserMaster(models.Model):
    _name = "user.master"
    _description = "User Master"
    _rec_name = "email"

    name = fields.Char(string="Name", required=True)
    email = fields.Char(string="Email", required=True)
    designation = fields.Char(string="Designation")
    mobile = fields.Char(string="Mobile", required=True)
