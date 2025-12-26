from odoo import models, fields, api

class AccountTax(models.Model):
    _inherit="account.tax"

    sap_tax_id = fields.Many2one('sap.taxes',string="Sap Tax Id",domain=[('active', '=', True)])