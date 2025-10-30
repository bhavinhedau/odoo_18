from odoo import models, fields, api
from odoo.tools import formatLang


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    price_unit = fields.Float(string="Unit Price")

    amount_untaxed = fields.Monetary(string="Untaxed Amount", compute="_compute_amounts", store=True,currency_field="currency_id")

    amount_sgst = fields.Monetary(string="SGST", compute="_compute_amounts", store=True, currency_field="currency_id")

    amount_cgst = fields.Monetary(string="CGST", compute="_compute_amounts", store=True, currency_field="currency_id")

    amount_cess = fields.Monetary(string="CESS", compute="_compute_amounts", store=True, currency_field="currency_id")

    amount_igst = fields.Monetary(string="IGST", compute="_compute_amounts", store=True, currency_field="currency_id")

    amount_total = fields.Monetary(string="Total", compute="_compute_amounts", store=True, currency_field="currency_id")

    currency_id = fields.Many2one("res.currency", string="Currency", default=lambda self: self.env.company.currency_id,readonly=True)


    @api.depends("move_ids_without_package.price_unit","move_ids_without_package.quantity","move_ids_without_package.taxes_id")
    def _compute_amounts(self):
        for picking in self:
            untaxed = sgst = cgst = cess = igst = 0.0

            for move in picking.move_ids_without_package:
                qty = move.quantity
                subtotal = qty * move.price_unit
                untaxed += subtotal

                for tax in move.taxes_id:
                    tax_name = tax.name.lower()
                    tax_rate = tax.amount  / 100.0

                    # ✅ Handle based on tax name
                    if "sgst" in tax_name:
                        sgst += subtotal * tax_rate
                    elif "cgst" in tax_name:
                        cgst += subtotal * tax_rate
                    elif "igst" in tax_name:
                        igst += subtotal * tax_rate
                    elif "cess" in tax_name:
                        cess += subtotal * tax_rate
                    # If only "gst" is mentioned (no prefix), split equally
                    elif "gst" in tax_name:
                        sgst += subtotal * (tax_rate / 2)
                        cgst += subtotal * (tax_rate / 2)

                # ✅ Assign computed values
                picking.amount_untaxed = untaxed
                picking.amount_sgst = sgst
                picking.amount_cgst = cgst
                picking.amount_cess = cess
                picking.amount_igst = igst
                picking.amount_total = untaxed + sgst + cgst + cess + igst


class StockMove(models.Model):
    _inherit = 'stock.move'

    taxes_id = fields.Many2many('account.tax', string="Taxes")

    price_subtotal = fields.Monetary(string="Subtotal", currency_field="currency_id", compute="_compute_price_subtotal",
                                     store=True, readonly=True)

    currency_id = fields.Many2one("res.currency", store=True, default=lambda self: self.env.company.currency_id,
                                  readonly=True)

    @api.depends("price_unit", "quantity")
    def _compute_price_subtotal(self):
        for move in self:
            qty = move.quantity
            move.price_subtotal = qty * move.price_unit



    @api.model_create_multi
    def create(self, vals_list):
        """Auto-copy taxes and price info from purchase or sale line."""
        moves = super().create(vals_list)
        for move in moves:
            # ✅ Purchase Orders → Receipts (WH/IN)
            if move.purchase_line_id:
                purchase_line = move.purchase_line_id
                move.taxes_id = purchase_line.taxes_id
                move.price_unit = purchase_line.price_unit


            # ✅ Sales Orders → Deliveries (WH/OUT)
            elif move.sale_line_id:
                sale_line = move.sale_line_id
                move.taxes_id = sale_line.tax_id
                move.price_unit = sale_line.price_unit


            # ✅ Manual Receipts
            else:
                if not move.price_unit:
                    move.price_unit = move.product_id.standard_price

        return moves
