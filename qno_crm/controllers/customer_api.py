from odoo import http
from odoo.http import request
import json
from datetime import datetime

VALID_API_KEY = ""


class CustomerAPIController(http.Controller):
    def _get_valid_api_key(self):
        return request.env['ir.config_parameter'].sudo().get_param('sap.odoo.api.key')

    @http.route('/api/customer', type='json', auth='public', methods=['POST'], csrf=False)
    def create_customer(self, **post):
        try:
            VALID_API_KEY = self._get_valid_api_key()
            api_key = request.httprequest.headers.get('x-api-key')
            if api_key != VALID_API_KEY:
                return {'Result': 0, 'status': 'error', 'message': 'Unauthorized: Invalid API Key'}, 401

            data = json.loads(request.httprequest.get_data())
            if not data:
                return {'Result': 0, 'status': 'error', 'message': 'Invalid or empty JSON'}

            name = data.get('name')
            if not name:
                return {'Result': 0, 'status': 'error', 'message': 'Customer name is required'}

            partner = request.env['res.partner'].sudo().search([('cardcode', '=', data.get('CardCode'))], limit=1)
            customer_series = request.env['customer.series'].sudo().search([('code', '=', data.get('Series'))], limit=1)
            customer_group = request.env['customer.group'].sudo().search([('code', '=', data.get('customer_group'))],limit=1)
            payment_terms_id = request.env['sap.payment.term'].sudo().search([('groupnum', '=', data.get('PayTermsGrpCode'))], limit=1)
            odoo_payment_terms_id = request.env['account.payment.term'].sudo().search([('sap_ref', '=', payment_terms_id.id)], limit=1)
            # branch = None
            # channel_bp = data.get('ChannlBP')
            # if channel_bp:
            #     branch = request.env['res.company'].sudo().search([('cardcode', '=', channel_bp)], limit=1)
            bp_addresses = data.get('BPAddresses', [])
            bp_bank_accounts = data.get('BPBankAccounts', [])
            vals = {
                'customer_rank': 1,
                'cardcode': data.get('CardCode'),
                'series_id': customer_series.id,
                'name': data.get('name'),
                'company_type': 'company',
                'vat': data .get('vat'),
                # 'l10n_in_pan': data.get('pan'),
                'phone': data.get('phone'),
                'email': data.get('email'),
                'website': data.get('website'),
                'customer_group': customer_group.id,
                'property_payment_term_id': odoo_payment_terms_id.id,
                'contact_person': data.get('contact_person'),
                # 'company_id': branch.id if branch else False,
                # 'partner_state' : 'approved',
                # 'active' : True
                # 'child_ids': child_ids,
            }
            # admin_user = request.env['res.users'].sudo().search([('id', '=', 2)], limit=1)
            vals = {k: v for k, v in vals.items() if v is not None and v != '' and v is not False}
            # print(json.dumps(vals))
            if partner:
                partner.sudo().with_context(no_update_sap=True).write(vals)
                action = 'updated'
            else:
                partner = request.env['res.partner'].sudo().create(vals)
                action = 'created'
            if partner:
                # partner.json = data
                #child_ids Create Update
                for bp_adds in bp_addresses:
                    address_type = bp_adds.get('AddressType')
                    if address_type == 'bo_BillTo':
                        partner_type = 'invoice'
                    elif address_type == 'bo_ShipTo':
                        partner_type = 'delivery'
                    else:
                        partner_type = None
                    state_id_bp = 0
                    if bp_adds.get('State'):
                        state_id_bp = request.env['res.country.state'].sudo().search([('l10n_in_tin', '=', bp_adds.get('State'))],limit=1)
                        partner.sudo().with_context(no_update_sap=True).write({
                            'state_id': state_id_bp.id if state_id_bp != 0 else False,
                            'country_id': state_id_bp.country_id.id if state_id_bp != 0 else False
                        })
                        # partner.state_id = state_id_bp.id if state_id_bp != 0 else False
                        # partner.country_id = state_id_bp.country_id.id if state_id_bp != 0 else False
                    vals = {
                        'parent_id': partner.id,
                        'rownumber':bp_adds.get('RowNum'),
                        'cardcode':bp_adds.get('BPCode'),
                        'type': partner_type,
                        'name': bp_adds.get('AddressName'),
                        'contact_code': bp_adds.get('AddressName'),
                        'street': bp_adds.get('Street'),
                        'street2': bp_adds.get('Block'),
                        'city': bp_adds.get('City'),
                        'zip': bp_adds.get('ZipCode'),
                        'state_id': state_id_bp.id if state_id_bp != 0 else False,
                        'country_id': state_id_bp.country_id.id if state_id_bp != 0 else False,
                        # 'company_id': branch.id if branch else False,
                    }
                    vals = {
                        k: v for k, v in vals.items()
                        if (
                                k == 'rownumber'  # always keep rownumber
                                or (v is not None and v != '' and v is not False)
                        )
                    }
                    # print(vals)
                    existing_child = request.env['res.partner'].sudo().search([
                        ('parent_id', '=', partner.id), ('type', '=', vals['type']), ('rownumber', '=', vals['rownumber'])
                    ], limit=1)
                    if existing_child and vals['rownumber'] >= 0 and vals['type']:
                        existing_child.sudo().with_context(no_update_sap=True).write(vals)
                    else:
                        if vals['rownumber'] >= 0 and vals['type']:
                            request.env['res.partner'].sudo().create(vals)
                    if bp_adds.get('GSTIN'):
                        partner.sudo().with_context(no_update_sap=True).write({
                            'vat': bp_adds.get('GSTIN'),
                            # 'l10n_in_pan': bp_adds.get('GSTIN')[2:12] if bp_adds.get('GSTIN') else False,
                            'l10n_in_gst_treatment': 'regular' if bp_adds.get('GSTIN') else False
                        })

                #create or update bank account
                for bank_data in bp_bank_accounts:
                    bank_id = request.env['res.bank'].sudo().search([('bic', '=', bank_data.get('BankCode'))], limit=1)
                    bank_vals = {
                        'partner_id': partner.id,
                        # 'company_id': branch.id if branch else False,
                        'acc_number': bank_data.get('AccountNo'),
                        'bank_id': bank_id.id,
                        'branch': bank_data.get('Branch'),
                        'inernalkey': bank_data.get('InternalKey'),
                        'accountname': bank_data.get('AccountName'),
                        'bicswiftcode': bank_data.get('BICSwiftCode'),
                        # 'rownumber': idx,
                    }
                    bank_vals = {k: v for k, v in bank_vals.items() if v is not None and v != '' and v is not False}
                    # print(bank_vals)
                    existing_bank = request.env['res.partner.bank'].with_context(active_test=False).sudo().search([
                        ('partner_id', '=', partner.id),
                        ('acc_number', '=', bank_vals['acc_number'])
                    ], limit=1)
                    if existing_bank and bank_vals['acc_number']:
                        if existing_bank.active == False:
                            existing_bank.active = True
                        if existing_bank.active == True:
                            existing_bank.write(bank_vals)
                    else:
                        if bank_vals['acc_number']:
                            request.env['res.partner.bank'].sudo().create(bank_vals)

            return {
                'Result': 1,
                'status': 'success',
                'message': f'Customer {action} successfully',
                'partner_id': partner.id,
                'partner_name': partner.name
            }

        except Exception as e:
            return {'Result': 0, 'status': 'error', 'message': str(e)}
