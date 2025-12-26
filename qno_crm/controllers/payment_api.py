from odoo import http
from odoo.http import request
import json

VALID_API_KEY = ""

class SAPPaymentAPI(http.Controller):

    def _get_valid_api_key(self):
        return request.env['ir.config_parameter'].sudo().get_param('sap.odoo.api.key')

    @http.route('/api/payment', type='json', auth='public', methods=['POST', 'PUT'], csrf=False)
    def sync_payment(self, **kwargs):
        current_payment = None
        current_invoice_line = None
        current_cashflow_line = None

        try:
            VALID_API_KEY = self._get_valid_api_key()
            api_key = request.httprequest.headers.get('x-api-key')

            if api_key != VALID_API_KEY:
                return {
                    "Result": 0,
                    "Message": "Unauthorized: Invalid API Key",
                    "doc_entry": 0,
                    "error": "Invalid API Key"
                }, 401

            data = json.loads(request.httprequest.get_data())
            api_log = request.env['api.log'].sudo().create({
                'name': '/api/sap/payment',
                'request_data': json.dumps(data)
            })

            if not data:
                if api_log:
                    api_log.sudo().write({
                        'response_data': json.dumps({
                            "Result": 0,
                            "Message": "Invalid JSON",
                            "doc_entry": 0,
                            "error": "Missing or malformed JSON",
                        })
                    })

                return {
                    "Result": 0,
                    "Message": "Invalid JSON",
                    "doc_entry": 0,
                    "error": "Missing or malformed JSON",
                }

            payload = data
            doc_entry = payload.get("DocEntry")
            if not doc_entry:
                return {"success": False, "message": "DocEntry missing"}

            Payment = request.env['sap.payment'].sudo()
            PaymentInvoice = request.env['sap.payment.invoice'].sudo()
            PaymentCashflow = request.env['sap.payment.cashflow'].sudo()

            # Search existing header
            existing = Payment.search([('doc_entry', '=', doc_entry)], limit=1)
            current_payment = doc_entry

            # Header values
            payment_vals = {
                "doc_entry": payload.get("DocEntry"),
                "doc_num": payload.get("DocNum"),
                "doc_type": payload.get("DocType"),
                "doc_date": payload.get("DocDate"),
                "card_code": payload.get("CardCode"),
                "card_name": payload.get("CardName"),
                "doc_currency": payload.get("DocCurrency"),
                "transfer_sum": payload.get("TransferSum"),
                "doc_rate": payload.get("DocRate"),
                "remarks": payload.get("Remarks"),
                "journal_remarks": payload.get("JournalRemarks"),
                "bpl_id": payload.get("BPLID"),
                "bpl_name": payload.get("BPLName"),
            }

            # Create or Update payment
            if existing:
                payment = existing
                payment.write(payment_vals)
                message = "Updated successfully"
            else:
                payment = Payment.create(payment_vals)
                message = "Created successfully"

            incoming_invoice_lines = {
                l.get("LineNum") for l in (payload.get("PaymentInvoices") or [])
            }

            # Remove deleted lines
            for old_line in payment.invoice_line_ids:
                if old_line.line_num not in incoming_invoice_lines:
                    old_line.unlink()

            # Map existing invoice lines
            existing_invoice_map = {
                line.line_num: line for line in payment.invoice_line_ids
            }

            # Create/Update lines safely
            for line in (payload.get("PaymentInvoices") or []):
                current_invoice_line = line.get("LineNum")

                if current_invoice_line in existing_invoice_map:
                    rec = existing_invoice_map[current_invoice_line]
                    rec.write({
                        "doc_entry": line.get("DocEntry"),
                        "sum_applied": line.get("SumApplied"),
                        "doc_line": line.get("DocLine"),
                        "invoice_type": line.get("InvoiceType"),
                    })
                else:
                    PaymentInvoice.create({
                        "payment_id": payment.id,
                        "line_num": line.get("LineNum"),
                        "doc_entry": line.get("DocEntry"),
                        "sum_applied": line.get("SumApplied"),
                        "doc_line": line.get("DocLine"),
                        "invoice_type": line.get("InvoiceType"),
                    })

            incoming_cashflows = {
                f.get("PaymentMeans") for f in (payload.get("CashFlowAssignments") or [])
            }

            # Remove missing cashflows
            for old_cf in payment.cashflow_ids:
                if old_cf.payment_means not in incoming_cashflows:
                    old_cf.unlink()

            # Map existing
            existing_cf_map = {
                cf.payment_means: cf for cf in payment.cashflow_ids
            }

            # Create/update cashflows
            for cf in (payload.get("CashFlowAssignments") or []):
                current_cashflow_line = cf.get("PaymentMeans")

                if current_cashflow_line in existing_cf_map:
                    rec = existing_cf_map[current_cashflow_line]
                    rec.write({
                        "check_number": cf.get("CheckNumber"),
                        "amount_lc": cf.get("AmountLC"),
                    })
                else:
                    PaymentCashflow.create({
                        "payment_id": payment.id,
                        "payment_means": cf.get("PaymentMeans"),
                        "check_number": cf.get("CheckNumber"),
                        "amount_lc": cf.get("AmountLC"),
                    })

            return {
                "success": True,
                "message": message,
                "doc_entry": payment.doc_entry,
            }

        except Exception as e:
            return {
                "success": False,
                "message": "Error during payment processing",
                "doc_entry": current_payment,
                "invoice_line": current_invoice_line,
                "cashflow_line": current_cashflow_line,
                "error": str(e),
            }
