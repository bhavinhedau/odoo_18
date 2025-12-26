# models/sap_payment_term.py
from odoo import models, fields

class SapPaymentTerm(models.Model):
    _name = 'sap.payment.term'
    _description = 'SAP Payment Term'
    _rec_name = 'pymntgroup'

    groupnum = fields.Integer(string="Group Number", required=True)
    pymntgroup = fields.Char(string="Payment Group", required=True)
    extradays = fields.Integer(string="Extra Days")
