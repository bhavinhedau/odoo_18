from odoo import models, fields, api


class SAPCredit(models.Model):
    _name = "sap.credit"
    _description = "SAP Credit Note"

    doc_entry = fields.Integer(string="DocEntry")
    doc_number = fields.Integer(string="DocNumber")
    num_at_card = fields.Char(string="Num At Card")
    card_code = fields.Char(string="Card Code")
    card_name = fields.Char(string="Customer Name")
    date = fields.Date(string="Date")
    remarks = fields.Text(string="Remarks")
    total_before_tax = fields.Float(string="Total Before Tax")
    total_tax = fields.Float(string="Total Tax")
    doc_total = fields.Float(string="Document Total")
    ship_to_code = fields.Char(string="ShipToCode")

    line_ids = fields.One2many(
        'sap.credit.line',
        'credit_id',
        string='Document Lines'
    )

    batch_all_ids = fields.One2many(
        'sap.credit.batch.line',
        'credit_id',
        string="All Batches",
        compute="_compute_batch_all",
        store=False
    )

    @api.depends('line_ids.batch_line_ids')
    def _compute_batch_all(self):
        for record in self:
            record.batch_all_ids = record.line_ids.mapped('batch_line_ids')


class SAPCreditLine(models.Model):
    _name = 'sap.credit.line'
    _description = 'SAP Credit Note Line'

    credit_id = fields.Many2one(
        'sap.credit',
        string='Credit Note',
        required=True,
        ondelete='cascade'
    )
    line_num = fields.Integer(string="Line Number")
    base_entry = fields.Integer(string="Base Entry")
    base_line = fields.Integer(string="Base Line")
    item_code = fields.Char(string="Item Code")
    item_description = fields.Char(string="Item Description")
    quantity = fields.Float(string="Quantity")
    uom = fields.Char(string="UoM")
    price = fields.Float(string="Price")
    tax_code = fields.Char(string="Tax Code")
    tax_amount = fields.Float(string="Tax Amount")
    line_total = fields.Float(string="Line Total")
    line_total_with_tax = fields.Float(string="Line Total w/ Tax")

    batch_line_ids = fields.One2many(
        'sap.credit.batch.line',
        'line_id',
        string='Batch Lines'
    )


class SAPCreditBatchLine(models.Model):
    _name = 'sap.credit.batch.line'
    _description = 'SAP Credit Note Batch Line'

    line_id = fields.Many2one(
        'sap.credit.line',
        string='Credit Line',
        ondelete='cascade'
    )

    credit_id = fields.Many2one(
        'sap.credit',
        string="Credit Note",
        related="line_id.credit_id",
        store=False
    )

    batch_number = fields.Char(string='Batch Number')
    quantity_number = fields.Float(string='Quantity')
