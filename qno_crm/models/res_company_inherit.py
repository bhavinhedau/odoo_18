from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit="res.company"

    sap_default_warehouse_id = fields.Many2one('sap.warehouse',string="Sap Default Warehouse",domain=[('active', '=', True)])
    sap_branch_id = fields.Integer()