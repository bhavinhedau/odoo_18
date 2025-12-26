from odoo import models, fields, api

class SAPPayment(models.Model):
    _name = "sap.payment"
    _description = "SAP Incoming Payment"

    doc_entry = fields.Integer(string="DocEntry", required=True)
    doc_num = fields.Integer(string="DocNum")
    doc_type = fields.Char(string="DocType")
    doc_date = fields.Date(string="DocDate")
    card_code = fields.Char(string="CardCode")
    card_name = fields.Char(string="Card Name")
    doc_currency = fields.Char(string="DocCurrency")
    transfer_sum = fields.Float(string="Transfer Sum")
    doc_rate = fields.Float(string="DocRate")
    remarks = fields.Char(string="Remarks")
    journal_remarks = fields.Char(string="Journal Remarks")
    bpl_id = fields.Integer(string="BPLID")
    bpl_name = fields.Char(string="BPLName")

    invoice_line_ids = fields.One2many("sap.payment.invoice", "payment_id")
    cashflow_ids = fields.One2many("sap.payment.cashflow", "payment_id")

class SAPPaymentInvoice(models.Model):
    _name = "sap.payment.invoice"
    _description = "SAP Payment Invoice Lines"

    payment_id = fields.Many2one("sap.payment")
    line_num = fields.Integer(string="LineNum")
    doc_entry = fields.Integer(string="Doc Entry")
    sum_applied = fields.Float(string="Sum Applied")
    doc_line = fields.Integer(string="DocLine")
    invoice_type = fields.Char(string="InvoiceType")


class SAPPaymentCashFlow(models.Model):
    _name = "sap.payment.cashflow"
    _description = "SAP Cash Flow Assignment"

    payment_id = fields.Many2one("sap.payment")
    payment_means = fields.Char(string="PaymentMeans")
    check_number = fields.Char(string="Check Number")
    amount_lc = fields.Float(string="Amount Lc")
