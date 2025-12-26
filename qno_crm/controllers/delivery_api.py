from odoo import http
from odoo.http import request
import json

VALID_API_KEY = ""

class SAPDeliveryAPIController(http.Controller):

    def _get_valid_api_key(self):
        return request.env['ir.config_parameter'].sudo().get_param('sap.odoo.api.key')

    @http.route('/api/delivery', type='json', auth='public', methods=['POST'], csrf=False)
    def sync_delivery(self, **kwargs):
        current_delivery = None
        current_line = None
        current_batch = None

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

            # -------------------------------
            # Parse incoming JSON
            # -------------------------------
            data = json.loads(request.httprequest.get_data())
            api_log = request.env['api.log'].sudo().create({
                'name': '/api/delivery',
                'request_data': json.dumps(data)
            })

            if not data:
                if api_log:
                    api_log.sudo().write({
                        'response_data': json.dumps({
                            "Result": 0,
                            "Message": "Invalid JSON",
                            "doc_entry": 0,
                            "error": "Missing or malformed JSON"
                        })
                    })
                return {
                    "Result": 0,
                    "Message": "Invalid JSON",
                    "doc_entry": 0,
                    "error": "Missing or malformed JSON"
                }

            payload = data
            doc_entry = payload.get("DocEntry")
            if not doc_entry:
                return {"success": False, "message": "DocEntry missing"}

            Delivery = request.env['sap.delivery'].sudo()
            Line = request.env['sap.delivery.line'].sudo()
            Batch = request.env['sap.delivery.batch.line'].sudo()

            existing = Delivery.search([('doc_entry', '=', doc_entry)], limit=1)
            current_delivery = doc_entry

            delivery_vals = {
                'num_at_card': payload.get("NumAtCard"),
                'card_code': payload.get("CardCode"),
                'card_name': payload.get("CardName"),
                'doc_entry': payload.get("DocEntry"),
                'doc_number': payload.get("DocNum"),
                'date': payload.get("DocDate"),
                'remarks': payload.get("Remarks"),
                'total_before_tax': payload.get("TotalBeforeTax"),
                'total_tax': payload.get("TotalTax"),
                'doc_total': payload.get("DocTotal"),
                'ship_to_code': payload.get("ShipToCode")
            }

            if existing:
                delivery = existing
                delivery.write(delivery_vals)
                message = "Updated successfully"
            else:
                delivery = Delivery.create(delivery_vals)
                message = "Created successfully"

            # -------------------------------
            # Update / Create Lines
            # -------------------------------
            incoming_line_nums = {l.get("LineNum") for l in payload.get("Lines", [])}
            for old_line in delivery.line_ids:
                if old_line.line_num not in incoming_line_nums:
                    old_line.unlink()

            existing_lines = {line.line_num: line for line in delivery.line_ids}

            for line_data in payload.get("Lines", []):
                current_line = line_data.get("LineNum")
                if current_line in existing_lines:
                    line_rec = existing_lines[current_line]
                    line_rec.write({
                        'base_entry': line_data.get("BaseEntry"),
                        'base_line': line_data.get("BaseLine"),
                        'item_code': line_data.get("ItemCode"),
                        'item_description': line_data.get("ItemDescription"),
                        'quantity': line_data.get("Quantity"),
                        'uom': line_data.get("UoM"),
                        'price': line_data.get("Price"),
                        'tax_code': line_data.get("TaxCode"),
                        'tax_amount': line_data.get("TaxAmount"),
                        'line_total': line_data.get("LineTotal"),
                        'line_total_with_tax': line_data.get("LineTotalWithTax"),
                    })
                else:
                    line_rec = Line.create({
                        'delivery_id': delivery.id,
                        'line_num': current_line,
                        'base_entry': line_data.get("BaseEntry"),
                        'base_line': line_data.get("BaseLine"),
                        'item_code': line_data.get("ItemCode"),
                        'item_description': line_data.get("ItemDescription"),
                        'quantity': line_data.get("Quantity"),
                        'uom': line_data.get("UoM"),
                        'price': line_data.get("Price"),
                        'tax_code': line_data.get("TaxCode"),
                        'tax_amount': line_data.get("TaxAmount"),
                        'line_total': line_data.get("LineTotal"),
                        'line_total_with_tax': line_data.get("LineTotalWithTax"),
                    })

                # -------------------------------
                # Update / Create Batches
                # -------------------------------
                incoming_batch_nums = {b.get("BatchNumber") for b in line_data.get("BatchNumbers", [])}
                for old_batch in line_rec.batch_line_ids:
                    if old_batch.batch_number not in incoming_batch_nums:
                        old_batch.unlink()

                existing_batches = {b.batch_number: b for b in line_rec.batch_line_ids}
                for batch in line_data.get("BatchNumbers", []):
                    current_batch = batch.get("BatchNumber")
                    if current_batch in existing_batches:
                        existing_batches[current_batch].write({
                            'quantity_number': batch.get("Quantity")
                        })
                    else:
                        Batch.create({
                            'line_id': line_rec.id,
                            'batch_number': current_batch,
                            'quantity_number': batch.get("Quantity")
                        })

            return {
                "success": True,
                "message": "Delivery Sync Successfully",
                "doc_entry": delivery.doc_entry
            }

        except Exception as e:
            return {
                "success": False,
                "message": "Error during delivery processing",
                "doc_entry": current_delivery,
                "line_num": current_line,
                "batch_number": current_batch,
                "error": str(e)
            }
