from odoo import models, fields

class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    sap_ref = fields.Many2one('sap.payment.term', string='SAP Ref')
