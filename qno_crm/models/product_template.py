from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    sap_default_warehouse = fields.Char(string='SAP Default Warehouse Code')
    measurementname = fields.Char(string='measurementName')