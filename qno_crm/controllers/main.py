from odoo import http
from odoo.http import request
import json
from datetime import datetime
from odoo.exceptions import UserError

VALID_API_KEY = ""


class ProductAPIController(http.Controller):

    def _get_valid_api_key(self):
        return request.env['ir.config_parameter'].sudo().get_param('sap.odoo.api.key')

    def _convert_time_to_float(self, time_str):
        """Converts HH:MM string to float (e.g., '09:30' → 9.5)"""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return hours + minutes / 60.0
        except Exception:
            return 0.0

    @http.route('/api/product', type='json', auth='public', methods=['POST'], csrf=False)
    def create_or_update_product(self, **post):
        api_log = None
        try:
            VALID_API_KEY = self._get_valid_api_key()

            # Validate API Key
            api_key = request.httprequest.headers.get('x-api-key')
            if api_key != VALID_API_KEY:
                return {
                    "Result": 0,
                    "Message": "Unauthorized: Invalid API Key",
                    "product_id": 0,
                    "product_name": "",
                    "error": "Invalid API Key"
                }, 401

            # Load and validate JSON
            data = json.loads(request.httprequest.get_data())
            api_log = request.env['api.log'].sudo().create({
                'name': '/api/product',
                'request_data': json.dumps(data)
            })
            if not data:
                if api_log:
                    api_log.sudo().write({
                        'response_data': json.dumps(
                            {
                                "Result": 0,
                                "Message": "Invalid JSON",
                                "product_id": 0,
                                "product_name": "",
                                "error": "Missing or malformed JSON"
                            }
                        )
                    })
                return {
                    "Result": 0,
                    "Message": "Invalid JSON",
                    "product_id": 0,
                    "product_name": "",
                    "error": "Missing or malformed JSON"
                }
            name = data.get('name')
            if not name:
                if api_log:
                    api_log.sudo().write({
                        'response_data': json.dumps(
                            {'Result': 0, 'status': 'error', 'message': 'Name is required'}
                        )
                    })
                return {'Result': 0, 'status': 'error', 'message': 'Name is required'}

            product = request.env['product.product'].with_context(active_test=False).sudo().search(
                [('default_code', '=', data.get('item_code'))],
                limit=1)

            if product:
                product.sudo().write({
                    'name': data.get('name'),
                    'type': data.get('type', 'consu'),
                    'list_price': data.get('list_price', 1.0),
                    'default_code': data.get('item_code'),
                    'description_purchase': data.get('description', ''),
                    'l10n_in_hsn_code': data.get('hsnCode', ''),
                    'sap_default_warehouse': data.get('defaultWarehouse', ''),
                    'measurementname': data.get('measurementName', ''),
                    # 'taxrate': data.get('TaxRate'),
                    # 'supplier_taxes_id': [(6, 0, tax_id.ids)],
                    # 'taxes_id': [(6, 0, tax_id.ids)],
                    # 'item_subgroup': data.get('U_Q_ITS'),
                    'invoice_policy': 'delivery',
                    # 'tracking': ManageBy,
                    # 'subcategory_id': subcategory_id.id if subcategory_id else False,

                })
                status = 'Updated'
            else:

                product = request.env['product.product'].sudo().create({
                    'name': data.get('name'),
                    'sale_ok': True,
                    'type': data.get('type', 'consu'),
                    'list_price': data.get('list_price', 1.0),
                    'default_code': data.get('item_code'),
                    # 'caratqty': carateqty,
                    # 'is_storable': True,
                    'description_purchase': data.get('description', ''),
                    # 'categ_id': categ_id.id,
                    'l10n_in_hsn_code': data.get('hsnCode', ''),
                    # 'taxrate': data.get('TaxRate'),
                    # 'active': active,
                    # 'supplier_taxes_id': [(6, 0, tax_id.ids)],
                    # 'taxes_id': [(6, 0, tax_id.ids)],
                    'invoice_policy': 'delivery',
                    # 'item_subgroup': data.get('U_Q_ITS'),
                    # 'tracking': ManageBy,
                })
                status = 'Created'
            # product.json = json.dumps(data)
            # product.date_api = datetime.now()
            if api_log:
                api_log.sudo().write({
                    'response_data': json.dumps(
                        {
                            "Result": 1,
                            "Message": "Success",
                            "Status": status,
                            "product_id": product.id,
                            "product_name": product.name,
                            "error": None
                        }),
                })
            return {
                "Result": 1,
                "Message": "Success",
                "Status": status,
                "product_id": product.id,
                "product_name": product.name,
                "error": None
            }

        except Exception as e:
            if api_log:
                api_log.sudo().write({
                    'response_data': json.dumps(
                        {
                            "Result": 0,
                            "Message": "Error occurred",
                            "product_id": 0,
                            "product_name": "",
                            "error": str(e)
                        }),
                })
            return {
                "Result": 0,
                "Message": "Error occurred",
                "product_id": 0,
                "product_name": "",
                "error": str(e)
            }

    @http.route('/api/branch', type='json', auth='public', methods=['POST'], csrf=False)
    def create_branch_warehouse_user(self, **post):
        api_log = None
        try:
            VALID_API_KEY = self._get_valid_api_key()
            # 1. API key check
            api_key = request.httprequest.headers.get('x-api-key')
            if api_key != VALID_API_KEY:
                return {'status': 'error', 'message': 'Unauthorized: Invalid API Key'}, 401

            # 2. Parse JSON
            data = json.loads(request.httprequest.get_data())
            api_log = request.env['api.log'].sudo().create({
                'name': '/api/branch',
                'request_data': json.dumps(data)
            })

            if not data:
                if api_log:
                    api_log.sudo().write({
                        'response_data': json.dumps(
                            {"Result": 0, 'status': 'error', 'message': 'Invalid or empty JSON'}),
                    })
                return {"Result": 0, 'status': 'error', 'message': 'Invalid or empty JSON'}

            name = data.get('name')
            phone = data.get('phone')
            city = data.get('city')
            zip_code = data.get('zip')
            street = data.get('street')
            street2 = data.get('street2')
            email = data.get('email')
            pan = data.get('pan')
            cardcode = data.get('CardCode')
            pricelist_id = data.get('pricelist_id')
            pricelist_name = data.get('pricelist_name')
            route = data.get('route')
            customer_group = data.get('customer_group')
            dairy_route_product = data.get('dairy_route_product')
            ice_cream_route_product = data.get('ice_cream_route_product')

            customer_group_id = request.env['customer.group'].sudo().search([('code', '=', data.get('customer_group'))],
                                                                            limit=1)

            state = 0
            if data.get('state_id'):
                state = request.env['res.country.state'].sudo().search([('l10n_in_tin', '=', data.get('state_id'))],
                                                                       limit=1)

            if not name:
                if api_log:
                    api_log.sudo().write({
                        'response_data': json.dumps(
                            {"Result": 0, 'status': 'error', 'message': 'Branch name is required'}),
                    })
                return {"Result": 0, 'status': 'error', 'message': 'Branch name is required'}

            branch = request.env['res.company'].sudo().search([('cardcode', '=', cardcode)], limit=1)
            if branch:
                partner_id = request.env['res.partner'].sudo().search([('id', '=', branch.partner_id.id)], limit=1)
                partner_id.sudo().with_context(no_update_sap=True).write({
                    'name': name,
                    'street': street,
                    'street2': street2,
                    'city': city,
                    'zip': zip_code,
                    'phone': phone,
                    'email': email,
                    'state_id': state.id if state != 0 else False,
                    'country_id': state.country_id.id if state else False,
                    'l10n_in_pan': pan,
                    'pricelist_id': pricelist_id,
                    'pricelist_name': pricelist_name,
                    'route': route,
                    'dairy_route_product': dairy_route_product,
                    'ice_cream_route_product': ice_cream_route_product
                })
                print(partner_id.name)
                if api_log:
                    api_log.sudo().write({
                        'response_data': json.dumps({
                            "Result": 1,
                            'status': 'success',
                            'message': 'Branch Updated',
                            'branch_id': branch.id,
                        }),
                    })
                return {
                    "Result": 1,
                    'status': 'success',
                    'message': 'Branch Updated',
                    'branch_id': branch.id,
                }
            else:
                # 3. Create Branch
                branch = request.env['res.company'].sudo().create({
                    'name': name,
                    'street': street,
                    'street2': street2,
                    'city': city,
                    'zip': zip_code,
                    'phone': phone,
                    'email': email,
                    'state_id': state.id,
                    'country_id': state.country_id.id,
                    'l10n_in_pan': pan,
                    'parent_id': 1,
                    'cardcode': cardcode,
                    'route': route
                })
                branch.partner_id.sudo().with_context(no_update_sap=True).write({
                    'cardcode': cardcode,
                    'company_id': branch.id,
                    'pricelist_id': pricelist_id,
                    'pricelist_name': pricelist_name,
                    'route': route,
                    'dairy_route_product': dairy_route_product,
                    'ice_cream_route_product': ice_cream_route_product,
                    'customer_group': customer_group_id.id if customer_group_id else False
                })
                # branch.partner_id.cardcode = cardcode
                # branch.partner_id.company_id = branch.id
                # branch.partner_id.pricelist_id = pricelist_id
                # branch.partner_id.pricelist_name = pricelist_name
                # branch.partner_id.pricelist_name = route
                # if customer_group_id: branch.partner_id.pricelist_name = route
                # branch.partner_id.dairy_route_product = dairy_route_product
                # branch.partner_id.ice_cream_route_product = ice_cream_route_product

                # 4. Create Warehouse linked to branch
                warehouse = request.env['stock.warehouse'].sudo().create({
                    'name': name,
                    'code': cardcode,
                    'company_id': branch.id,
                    'partner_id': branch.partner_id.id,
                })
                user_count = 0
                login = email
                if login:
                    user_count = request.env['res.users'].sudo().search_count([('login', '=', email)])
                    if user_count > 0:
                        login = cardcode
                else:
                    login = cardcode
                # 5. Create User linked to branch
                new_user = request.env['res.users'].sudo().create({
                    'name': name,
                    'login': login,
                    'partner_id': branch.partner_id.id,
                    'phone': phone,
                    'company_ids': [(6, 0, [branch.id])],
                    'company_id': branch.id,
                    'groups_id': [(6, 0, [
                        request.env.ref('base.group_user').id,
                        request.env.ref('sales_team.group_sale_salesman_all_leads').id,
                        request.env.ref('account.group_account_basic').id,
                        request.env.ref('stock.group_stock_user').id,
                        request.env.ref('purchase.group_purchase_user').id,
                    ])],
                })
                # 6. Assign branch to admin user
                admin_user = request.env.ref('base.user_admin')
                admin_user = request.env['res.users'].browse(2)
                admin_user.sudo().write({
                    'company_ids': [(4, branch.id)]
                })
                # 7. Create sequences for the new branch
                sequence_data = [
                    {
                        'name': f'{name} Sale Order',
                        'code': 'sale.order',
                        'prefix': f'{name[:2].upper()}/{branch.id}/SO/',
                        'padding': 5,
                    },
                    {
                        'name': f'{name} Purchase Order',
                        'code': 'purchase.order',
                        'prefix': f'{name[:2].upper()}/{branch.id}/PO/',
                        'padding': 5,
                    },
                    {
                        'name': f'{name} Receipt',
                        'code': 'stock.picking.in',
                        'prefix': f'{name[:2].upper()}/{branch.id}/IN/',
                        'padding': 5,
                    },
                    {
                        'name': f'{name} Delivery',
                        'code': 'stock.picking.out',
                        'prefix': f'{name[:2].upper()}/{branch.id}/OUT/',
                        'padding': 5,
                    },
                    {
                        'name': f'{name} Sales Invoice',
                        'code': 'account.move',
                        'prefix': f'{name[:2].upper()}/{branch.id}/INV/',
                        'padding': 5,
                    },
                ]

                for seq in sequence_data:
                    request.env['ir.sequence'].sudo().create({
                        'name': seq['name'],
                        'code': seq['code'],
                        'prefix': seq['prefix'],
                        'padding': seq['padding'],
                        'implementation': 'standard',
                        'company_id': branch.id,
                    })
                # 9. create new record in store management
                store_manage = request.env['vendor.pos'].sudo().create({
                    'branch_id': branch.id,
                })
                if api_log:
                    api_log.sudo().write({
                        'response_data': json.dumps({
                            'Result': 1,
                            'status': 'success',
                            'message': 'Branch, warehouse, and user created',
                            'branch_id': branch.id,
                            'warehouse_id': warehouse.id,
                            'user_id': new_user.id,
                        }),
                    })
                return {
                    'Result': 1,
                    'status': 'success',
                    'message': 'Branch, warehouse, and user created',
                    'branch_id': branch.id,
                    'warehouse_id': warehouse.id,
                    'user_id': new_user.id,
                }

        except Exception as e:
            if api_log:
                api_log.sudo().write({
                    'response_data': json.dumps({'Result': 0, 'status': 'error', 'message': str(e)}),
                })
            return {'Result': 0, 'status': 'error', 'message': str(e)}

    # @http.route('/api/customer', type='json', auth='public', methods=['POST'], csrf=False)
    # def create_customer(self, **post):
    #     outlet_type_labels = {
    #         'DF Outlet': 'df_outlet',
    #         'Non DF Outlet': 'non_df_outlet',
    #         'TOD Outlet': 'tod_outlet',
    #         'TOD & DF Outlet': 'tod_df_outlet',
    #         'Franchise': 'franchise'
    #     }
    #
    #     outlet_channel_type_labels = {
    #         'Grocery / Kirana / Provision Store': 'grocery',
    #         'Chemist': 'chemist',
    #         'Ice Cream Parlour': 'ice_cream',
    #         'Sweet Mart / Dairy Parlour': 'sweet_mart',
    #         'Modern Trade / Stand alone O/L': 'modern_trade',
    #         'Horeca / Caters': 'horeca',
    #         'Airport / Railway / Bus Stop': 'airport',
    #         'Institutions': 'institutions',
    #         'Vending': 'vending',
    #         'Cold Drink Shopy / Pan Parlour': 'cold_drink',
    #         'Bakery Shop': 'bakery',
    #         'Chhaswala Exclusive': 'exclusive',
    #         'Others': 'others'
    #     }
    #
    #     try:
    #         VALID_API_KEY = self._get_valid_api_key()
    #         api_key = request.httprequest.headers.get('x-api-key')
    #         if api_key != VALID_API_KEY:
    #             return {'Result': 0,'status': 'error', 'message': 'Unauthorized: Invalid API Key'}, 401
    #
    #         data = json.loads(request.httprequest.get_data())
    #         if not data:
    #             return {'Result': 0,'status': 'error', 'message': 'Invalid or empty JSON'}
    #
    #         name = data.get('name')
    #         if not name:
    #             return {'Result': 0,'status': 'error', 'message': 'Customer name is required'}
    #
    #         partner = request.env['res.partner'].sudo().search([('cardcode', '=', data.get('CardCode'))], limit=1)
    #         state=0
    #         if data.get('state_id'):
    #             state = request.env['res.country.state'].sudo().search([('l10n_in_tin', '=', data.get('state_id'))],limit=1)
    #         branch = None
    #         channel_bp = data.get('ChannelBP')
    #         if channel_bp:
    #             branch = request.env['res.company'].sudo().search([('cardcode', '=', channel_bp)], limit=1)
    #
    #         customer_group = request.env['customer.group'].sudo().search([('code','=',data.get('customer_group'))], limit=1)
    #         customer_series = request.env['customer.series'].sudo().search([('code','=',data.get('Series'))], limit=1)
    #         payment_terms_id = request.env['sap.payment.term'].sudo().search([('groupnum','=',data.get('PayTermsGrpCode'))], limit=1)
    #         odoo_payment_terms_id = request.env['account.payment.term'].sudo().search([('sap_ref','=',payment_terms_id.id)], limit=1)
    #         outlattype_label = data.get('U_Q_OutletType')  # e.g., 'DF Outlet'
    #         outlatchanneltype_label = data.get('U_Q_OutletChannelType')
    #
    #         outlattype = outlet_type_labels.get(outlattype_label, '')
    #         outlatchanneltype = outlet_channel_type_labels.get(outlatchanneltype_label, '')
    #
    #         if partner:
    #             partner.sudo().write({
    #                 'name': name,
    #                 'series_id': customer_series.id,
    #                 # 'street': data.get('street'),
    #                 # 'street2': data.get('street2'),
    #                 # 'city': data.get('city'),
    #                 # 'zip': data.get('zip'),
    #                 'state_id': state.id if state != 0 else False,
    #                 'country_id': state.country_id.id if state != 0 else False,
    #                 'vat': data.get('vat'),
    #                 'l10n_in_pan': data.get('pan'),
    #                 'phone': data.get('phone'),
    #                 'mobile': data.get('mobile'),
    #                 'email': data.get('email'),
    #                 'website': data.get('website'),
    #                 'customer_group': customer_group.id,
    #                 'company_id':branch.id if branch else False,
    #                 'pricelist_id':data.get('pricelist_id'),
    #                 'pricelist_name':data.get('pricelist_name'),
    #                 'contact_person':data.get('contact_person'),
    #                 'property_payment_term_id':odoo_payment_terms_id.id,
    #                 'outlattype': outlattype,
    #                 'outlatchanneltype': outlatchanneltype,
    #             })
    #             action = 'updated'
    #         #
    #             bp_addresses = data.get('BPAddresses', [])
    #             for addr in bp_addresses:
    #                 address_type = addr.get('AddressType')
    #                 state_id_bp = 0
    #                 if addr.get('State'):
    #                     state_id_bp = request.env['res.country.state'].sudo().search([('l10n_in_tin', '=', addr.get('State'))],limit=1)
    #                 vals = {
    #                     'parent_id': partner.id,
    #                     'cardcode':addr.get('BPCode'),
    #                     'type': 'invoice' if address_type == 'bo_BillTo' else 'delivery',
    #                     'name': addr.get('AddressName'),
    #                     'street': addr.get('Street'),
    #                     'street2': addr.get('Block'),
    #                     'city': addr.get('City'),
    #                     'zip': addr.get('ZipCode'),
    #                     'state_id': state_id_bp.id if state_id_bp != 0 else False,
    #                     'country_id': state_id_bp.country_id.id if state_id_bp != 0 else False,
    #                     # 'vat': addr.get('GSTIN'),
    #                     # 'l10n_in_gst_treatment': addr.get('GstType'),
    #                     'company_id': partner.company_id.id,
    #                     'contact_person':data.get('contact_person'),
    #                     'rownumber':addr.get('RowNum')
    #                 }
    #                 partner.vat = addr.get('GSTIN')
    #                 partner.l10n_in_pan = addr.get('GSTIN')[2:12] if addr.get('GSTIN') else False
    #                 partner.l10n_in_gst_treatment = 'regular' if addr.get('GSTIN') else False
    #
    #                 # Check if similar address exists already to avoid duplication
    #                 existing_child = request.env['res.partner'].sudo().search([
    #                     ('parent_id', '=', partner.id),
    #                     ('type', '=', vals['type']),
    #                     ('rownumber','=',vals['rownumber'])
    #                 ], limit=1)
    #
    #                 if existing_child:
    #                     existing_child.write(vals)
    #                 else:
    #                     request.env['res.partner'].sudo().create(vals)
    #
    #             bp_bank_accounts = data.get('BPBankAccounts', [])
    #             for idx, bank_data in enumerate(bp_bank_accounts):
    #                 bank_id = request.env['res.bank'].sudo().search([('bic','=',bank_data.get('BankCode'))],limit=1)
    #
    #             #
    #                 bank_vals = {
    #                     'partner_id': partner.id,
    #                     'company_id': branch.id if branch else False,
    #                     'acc_number': bank_data.get('AccountNo'),
    #                     'bank_id': bank_id.id,
    #                     'branch': bank_data.get('Branch'),
    #                     'inernalkey': bank_data.get('InternalKey'),
    #                     'accountname': bank_data.get('AccountName'),
    #                     'bicswiftcode': bank_data.get('BICSwiftCode'),
    #                     'rownumber': idx,
    #                 }
    #                 # Check if same account exists to avoid duplication
    #                 existing_bank = request.env['res.partner.bank'].with_context(active_test=False).sudo().search([
    #                     ('partner_id', '=', partner.id),
    #                     ('acc_number', '=', bank_vals['acc_number'])
    #                 ], limit=1)
    #                 if existing_bank:
    #                     if existing_bank.active== False:
    #                         existing_bank.active = True
    #                     if existing_bank.active==True:
    #                         existing_bank.write(bank_vals)
    #                 else:
    #                     request.env['res.partner.bank'].sudo().create(bank_vals)
    #             partner.partner_state = 'approved'
    #             partner.json = data
    #         else:
    #             partner.json = data
    #             partner = request.env['res.partner'].sudo().create({
    #                 'cardcode': data.get('CardCode'),
    #                 'series_id': customer_series.id,
    #                 'name': name,
    #                 'company_type': 'company',
    #                 # 'street': data.get('street'),
    #                 # 'street2': data.get('street2'),
    #                 # 'city': data.get('city'),
    #                 # 'zip': data.get('zip'),
    #                 'state_id': state.id if state != 0 else False,
    #                 'country_id': state.country_id.id if state != 0 else False,
    #                 'vat': data.get('vat'),
    #                 'l10n_in_pan': data.get('pan'),
    #                 'phone': data.get('phone'),
    #                 'mobile': data.get('mobile'),
    #                 'email': data.get('email'),
    #                 'website': data.get('website'),
    #                 'customer_rank': 1,
    #                 'customer_group': customer_group.id,
    #                 'company_id': branch.id if branch else False,
    #                 'pricelist_id':data.get('pricelist_id'),
    #                 'pricelist_name':data.get('pricelist_name'),
    #                 'outlattype': outlattype,
    #                 'outlatchanneltype': outlatchanneltype,
    #             })
    #             action = 'created'
    #             bp_addresses = data.get('BPAddresses', [])
    #             for addr in bp_addresses:
    #                 address_type = addr.get('AddressType')
    #                 state_id_bp = 0
    #                 if addr.get('State'):
    #                     state_id_bp = request.env['res.country.state'].sudo().search(
    #                         [('l10n_in_tin', '=', addr.get('State'))], limit=1)
    #
    #                 vals = {
    #                     'parent_id': partner.id,
    #                     'cardcode': addr.get('BPCode'),
    #                     'type': 'invoice' if address_type == 'bo_BillTo' else 'delivery',
    #                     'name': addr.get('AddressName'),
    #                     'street': addr.get('Street'),
    #                     'street2': addr.get('Block'),
    #                     'city': addr.get('City'),
    #                     'zip': addr.get('ZipCode'),
    #                     'state_id': state_id_bp.id if state_id_bp != 0 else False,
    #                     'country_id': state_id_bp.country_id.id if state_id_bp != 0 else False,
    #                     # 'vat': addr.get('GSTIN'),
    #                     # 'l10n_in_gst_treatment': addr.get('GstType'),
    #                     'company_id': partner.company_id.id,
    #                     'contact_person': data.get('contact_person')
    #                 }
    #                 partner.vat = addr.get('GSTIN')
    #                 partner.l10n_in_pan = addr.get('GSTIN')[2:12]
    #                 partner.l10n_in_gst_treatment = 'regular'
    #
    #                 # Check if similar address exists already to avoid duplication
    #                 existing_child = request.env['res.partner'].sudo().search([
    #                     ('parent_id', '=', partner.id),
    #                     ('type', '=', vals['type']),
    #                     ('name', '=', vals['name'])
    #                 ], limit=1)
    #
    #                 if existing_child:
    #                     existing_child.write(vals)
    #                 else:
    #                     request.env['res.partner'].sudo().create(vals)
    #
    #             bp_bank_accounts = data.get('BPBankAccounts', [])
    #             for idx, bank_data in enumerate(bp_bank_accounts):
    #                 bank_id = request.env['res.bank'].sudo().search([('bic', '=', bank_data.get('BankCode'))], limit=1)
    #
    #                 #
    #                 bank_vals = {
    #                     'partner_id': partner.id,
    #                     'company_id': branch.id if branch else False,
    #                     'acc_number': bank_data.get('AccountNo'),
    #                     'bank_id': bank_id.id,
    #                     'branch': bank_data.get('Branch'),
    #                     'inernalkey': bank_data.get('InternalKey'),
    #                     'accountname': bank_data.get('AccountName'),
    #                     'bicswiftcode': bank_data.get('BICSwiftCode'),
    #                     'rownumber': idx,
    #                 }
    #                 # Check if same account exists to avoid duplication
    #                 existing_bank = request.env['res.partner.bank'].with_context(active_test=False).sudo().search([
    #                     ('partner_id', '=', partner.id),
    #                     ('acc_number', '=', bank_vals['acc_number'])
    #                 ], limit=1)
    #                 if existing_bank:
    #                     if existing_bank.active == False:
    #                         existing_bank.active = True
    #                     if existing_bank.active == True:
    #                         existing_bank.write(bank_vals)
    #                 else:
    #                     request.env['res.partner.bank'].sudo().create(bank_vals)
    #             partner.active=True
    #             partner.partner_state='approved'
    #
    #         return {
    #             'Result': 1,
    #             'status': 'success',
    #             'message': f'Customer {action} successfully',
    #             'partner_id': partner.id,
    #             'partner_name': partner.name
    #         }
    #
    #     except Exception as e:
    #         return {'Result': 0,'status': 'error', 'message': str(e)}

    @http.route('/api/scheme', type='json', auth='public', methods=['POST'], csrf=False)
    def create_or_update_scheme(self, **post):
        api_log = None
        api_log = request.env['api.log'].sudo().create({
            'name': '/api/scheme'})
        try:
            # Validate API Key
            VALID_API_KEY = self._get_valid_api_key()
            api_key = request.httprequest.headers.get('x-api-key')
            if api_key != VALID_API_KEY:
                return {'result': 0, 'status': 'error', 'message': 'Unauthorized: Invalid API Key'}, 401

            data = json.loads(request.httprequest.get_data())
            api_log.sudo().write({
                'request_data': json.dumps(data)
            })
            if not data:
                if api_log:
                    api_log.sudo().write({
                        'response_data': json.dumps(
                            {'result': 0, 'status': 'error', 'message': 'Invalid or empty JSON'}),
                    })
                return {'result': 0, 'status': 'error', 'message': 'Invalid or empty JSON'}, 400

            scheme_id = data.get('scheme_id')
            if not scheme_id:
                if api_log:
                    api_log.sudo().write({
                        'response_data': json.dumps(
                            {'result': 0, 'status': 'error', 'message': 'scheme_id is required'}),
                    })
                return {'result': 0, 'status': 'error', 'message': 'scheme_id is required'}, 400

            # Try to find existing scheme by scheme_id
            scheme = request.env['promotion.scheme'].sudo().search([('scheme_id', '=', scheme_id)], limit=1)

            # product = request.env['product.product'].sudo().search([('default_code', '=', data.get('product_id'))],limit=1)
            # free_product = request.env['product.product'].sudo().search([('default_code', '=', data.get('free_product_id'))], limit=1)
            product_codes = data.get('product_id', [])
            product_ids = []
            if isinstance(product_codes, list):
                for code in product_codes:
                    product = request.env['product.product'].with_context(active_test=False).sudo().search(
                        [('default_code', '=', code)], limit=1)
                    if product:
                        product_ids.append(product.id)
            free_product_codes = data.get('free_product_id', [])
            free_product_ids = []
            if isinstance(free_product_codes, list):
                for code in free_product_codes:
                    product = request.env['product.product'].with_context(active_test=False).sudo().search(
                        [('default_code', '=', code)], limit=1)
                    if product:
                        free_product_ids.append(product.id)

            category = request.env['product.category'].sudo().search([('name', '=', data.get('category_id'))], limit=1)
            if not category and data.get('category_id'):
                category = request.env['product.category'].sudo().create({'name': data.get('category_id')})

            free_category = request.env['product.category'].sudo().search(
                [('name', '=', data.get('free_product_category_id'))], limit=1)
            if not free_category and data.get('free_product_category_id'):
                free_category = request.env['product.category'].sudo().create(
                    {'name': data.get('free_product_category_id')})

            vals = {
                'scheme_type': data.get('scheme_type'),
                'product_id': [(6, 0, product_ids)],
                'min_quantity': data.get('min_quantity'),
                'min_cart_value': data.get('min_cart_value'),
                'cart_discount_amount': data.get('cart_discount_amount'),
                'cart_discount_percentage': data.get('cart_discount_percentage'),
                'disc_per_piece_amount': data.get('disc_per_piece_amount'),
                'disc_per_piece_percentage': data.get('disc_per_piece_percentage'),
                'free_product_id': [(6, 0, free_product_ids)],
                'free_product_quantity': data.get('free_product_quantity'),
                'free_product_amount': data.get('free_product_amount'),
                'category_id': category.id,
                'free_product_category_id': free_category.id,
                'scheme_description': data.get('scheme_description'),
                'active': data.get('active', True),
                'date_from': data.get('date_from'),
                'date_to': data.get('date_to'),
                'customer_group': data.get('customer_group'),
                'time_from': self._convert_time_to_float(data.get('time_from', '00:00')),
                'time_to': self._convert_time_to_float(data.get('time_to', '00:00')),
            }

            if scheme:
                scheme.sudo().write(vals)
                action = 'updated'
            else:
                vals.update({'scheme_id': scheme_id})
                scheme = request.env['promotion.scheme'].sudo().create(vals)
                action = 'created'
            if api_log:
                api_log.sudo().write({
                    'response_data': json.dumps(
                        {
                            'result': 1,
                            'status': 'success',
                            'message': f'Scheme {action} successfully',
                            'id': scheme.id,
                            'name': scheme.name
                        }),
                })
            return {
                'result': 1,
                'status': 'success',
                'message': f'Scheme {action} successfully',
                'id': scheme.id,
                'name': scheme.name
            }

        except Exception as e:
            if api_log:
                api_log.sudo().write({'result': 0, 'status': 'error', 'message': str(e)})
            return {'result': 0, 'status': 'error', 'message': str(e)}

    @http.route('/api/pricelist', type='json', auth='public', methods=['POST'], csrf=False)
    def craeteorupdatepricelist(self, **post):
        try:
            VALID_API_KEY = self._get_valid_api_key()
            api_key = request.httprequest.headers.get('x-api-key')
            if api_key != VALID_API_KEY:
                return {'result': 0, 'status': 'error', 'message': 'Unauthorized: Invalid API Key'}, 401

            data = json.loads(request.httprequest.get_data())
            pricelists = data.get('data', [])

            for pl in pricelists:
                pricelist_id = pl.get('ID')
                pricelist_name = pl.get('Name')
                item_list = pl.get('ItemList', [])
                customers = pl.get('Customers', [])

                # Update list_price if MRP
                if pricelist_id == 7:
                    for item in item_list:
                        item_code = item.get('ItemCode')
                        price = item.get('Price', 0)
                        products = request.env['product.product'].with_context(active_test=False).sudo().search(
                            [('default_code', '=', item_code)],
                            limit=1)
                        for p in products:
                            p.product_tmpl_id.list_price = price

                if customers:
                    card_codes = [customer.get('CardCode') for customer in customers]
                    customers = request.env['res.partner'].sudo().search(
                        [('cardcode', 'in', card_codes), ('customer_rank', '=', 0)])
                else:
                    customers = request.env['res.partner'].sudo().search([
                        ('pricelist_id', '=', pricelist_id),
                        ('customer_rank', '=', 0)
                    ])

                for customer in customers:
                    company_id = request.env['res.company'].sudo().search([('partner_id', '=', customer.id)], limit=1)
                    if not customer:
                        continue

                    for item in item_list:
                        item_code = item.get('ItemCode')
                        price = item.get('Price', 0)
                        spacialprice = item.get('specialprice', 0)
                        product = request.env['product.product'].with_context(active_test=False).sudo().search(
                            [('default_code', '=', item_code)],
                            limit=1)

                        if not product:
                            continue

                        supplier_info = request.env['product.supplierinfo'].sudo().search([
                            ('product_tmpl_id', '=', product.product_tmpl_id.id),
                            ('partner_id', '=', customer.id),
                            ('pricelist_id', '=', pricelist_id)
                        ], limit=1)

                        if supplier_info:
                            supplier_info.write({
                                'price': price,
                                'pricelist_name': pricelist_name,
                                'spacialprice': spacialprice
                            })
                        else:
                            request.env['product.supplierinfo'].sudo().create({
                                'product_tmpl_id': product.product_tmpl_id.id,
                                'partner_id': customer.id,
                                'min_qty': 1,
                                'price': price,
                                'spacialprice': spacialprice,
                                'pricelist_id': pricelist_id,
                                'pricelist_name': pricelist_name,
                                'company_id': company_id.id if company_id else False
                            })

            for pl in pricelists:
                pricelist_id = pl.get('ID')
                item_list = pl.get('ItemList', [])
                active_customers = request.env['res.partner'].sudo().search([
                    ('customer_rank', '>', 0),
                    ('active', '=', True),
                    ('parent_id', '=', False),
                    ('sap_pricelist_id.code', '=', pricelist_id)
                ])
                if not active_customers:
                    continue
                pricelist_id_serch = request.env['customer.pricelist.sap'].sudo().search([('code', '=', pricelist_id)],
                                                                                         limit=1)

                for ac in active_customers:

                    for item in item_list:
                        item_code = item.get('ItemCode')
                        price = item.get('Price', 0)
                        spacialprice = item.get('specialprice', 0)
                        product = request.env['product.product'].with_context(active_test=False).sudo().search(
                            [('default_code', '=', item_code)],
                            limit=1)
                        if not product:
                            continue

                        pricelist_rec = request.env['customer.item.pricelist'].sudo().search([
                            ('customer_id', '=', ac.id),
                            ('product_id', '=', product.id)
                        ], limit=1)

                        if pricelist_rec:
                            # Update existing record
                            pricelist_rec.write({
                                'price': price,
                                'pricelist_id': pricelist_id_serch.id
                            })
                        else:
                            # Create new record
                            request.env['customer.item.pricelist'].sudo().create({
                                'customer_id': ac.id,
                                'product_id': product.id,
                                'price': price,
                                'pricelist_id': pricelist_id_serch.id
                            })

            return {
                'result': 1,
                'status': 'success',
                'message': 'Pricelist data processed successfully',
            }

        except Exception as e:
            return {'result': 0, 'status': 'error', 'message': str(e)}

    @http.route('/api/purchase/cancel', type='http', auth='public', methods=['POST'], csrf=False)
    def cancel_purchase_order(self, **post):
        api_log = None
        try:
            VALID_API_KEY = self._get_valid_api_key()

            # API key check
            api_key = request.httprequest.headers.get('x-api-key')
            if api_key != VALID_API_KEY:
                return request.make_response(
                    json.dumps({"status": "error", "message": "Unauthorized: Invalid API Key"}),
                    headers=[("Content-Type", "application/json")]
                )

            # Parse raw JSON body
            data = json.loads(request.httprequest.get_data())
            api_log = request.env['api.log'].sudo().create({
                'name': '/api/purchase/cancel',
                'request_data': json.dumps(data)
            })

            po_ids = data.get("id", [])
            if not po_ids:
                if api_log:
                    api_log.sudo().write({
                        'response_data': json.dumps(
                            {"status": "error", "message": "No purchase order IDs provided"}),
                    })
                return request.make_response(
                    json.dumps({"status": "error", "message": "No purchase order IDs provided"}),
                    headers=[("Content-Type", "application/json")]
                )

            results = []
            for po_id in po_ids:
                po = request.env['purchase.order'].sudo().browse(po_id)
                if not po.exists():
                    results.append({"id": po_id, "status": "error", "message": "Purchase Order not found"})
                    continue

                if po.state in ['cancel']:
                    results.append(
                        {"id": po_id, "status": "error", "message": f"Cannot cancel PO in state: {po.state}"})
                    continue

                try:
                    po.button_cancel()
                    results.append({"id": po_id, "status": "success", "message": f"PO {po.name} cancelled"})
                except UserError as e:
                    results.append({"id": po_id, "status": "error", "message": str(e)})
                except Exception as e:
                    results.append({"id": po_id, "status": "error", "message": f"Unexpected error: {str(e)}"})
            if api_log:
                api_log.sudo().write({
                    'response_data': json.dumps(
                        {"status": "done", "results": results}),
                })
            return request.make_response(
                json.dumps({"status": "done", "results": results}),
                headers=[("Content-Type", "application/json")]
            )

        except Exception as e:
            if api_log:
                api_log.sudo().write({
                    'response_data': json.dumps(
                        {"status": "error", "message": f"Unexpected error: {str(e)}"}),
                })
            return request.make_response(
                json.dumps({"status": "error", "message": f"Unexpected error: {str(e)}"}),
                headers=[("Content-Type", "application/json")]
            )

    @http.route('/api/purchase/update', type='http', auth='public', methods=['POST'], csrf=False)
    def update_purchase_orders(self, **post):
        """
        Update Multiple Purchase Orders via API
        JSON Input:
        {
          "data": [
            {"id": 27, "partner_id": 15, "notes": "Updated Vendor"},
            {"id": 28, "date_order": "2025-08-22 10:00:00", "notes": "Rescheduled order"}
          ]
        }
        """
        api_log = None
        try:
            VALID_API_KEY = self._get_valid_api_key()

            # API key check
            api_key = request.httprequest.headers.get('x-api-key')
            if api_key != VALID_API_KEY:
                return request.make_response(
                    json.dumps({"status": "error", "message": "Unauthorized: Invalid API Key"}),
                    headers=[("Content-Type", "application/json")],
                    status=401
                )

            # Parse request body
            body = json.loads(request.httprequest.get_data())
            records = body.get("data", [])
            api_log = request.env['api.log'].sudo().create({
                'name': '/api/purchase/update',
                'request_data': json.dumps(body)
            })
            if not records:
                if api_log:
                    api_log.sudo().write({
                        'response_data': json.dumps(
                            {"status": "error", "message": "No records provided"}),
                    })
                return request.make_response(
                    json.dumps({"status": "error", "message": "No records provided"}),
                    headers=[("Content-Type", "application/json")],
                    status=400
                )

            results = []
            for rec in records:
                po_id = rec.get("id")
                if not po_id:
                    results.append({"status": "error", "message": "Missing id"})
                    continue

                values = {k: v for k, v in rec.items() if k != "id"}
                if "sap_inv_num" in values and values.get("sap_inv_num"):
                    values["status"] = "dispatch"
                if "inv_number" in rec:
                    values["inv_number"] = rec["inv_number"]

                po = request.env['purchase.order'].sudo().browse(po_id)
                if not po.exists():
                    results.append({"id": po_id, "status": "error", "message": f"Purchase Order {po_id} not found"})
                    continue

                if po.state in ['cancel']:
                    response_msg = f"Cannot update PO in state: {po.state}"
                    po.sudo().write({
                        "update_json": json.dumps(values, indent=2),
                        "update_response": response_msg
                    })
                    results.append({"id": po_id, "status": "error", "message": response_msg})
                    continue

                try:
                    po.sudo().write(values)

                    response_msg = f"PO {po.name} updated successfully"
                    po.sudo().write({
                        "update_json": json.dumps(values, indent=2),
                        "update_response": response_msg
                    })

                    results.append({"id": po_id, "status": "success", "message": response_msg})

                except UserError as e:
                    response_msg = str(e)
                    po.sudo().write({
                        "update_json": json.dumps(values, indent=2),
                        "update_response": response_msg
                    })
                    results.append({"id": po_id, "status": "error", "message": response_msg})

                except Exception as e:
                    response_msg = f"Unexpected error: {str(e)}"
                    po.sudo().write({
                        "update_json": json.dumps(values, indent=2),
                        "update_response": response_msg
                    })
                    results.append({"id": po_id, "status": "error", "message": response_msg})
            if api_log:
                api_log.sudo().write({
                    'response_data': json.dumps(
                        {"status": "done", "results": results}),
                })
            return request.make_response(
                json.dumps({"status": "done", "results": results}),
                headers=[("Content-Type", "application/json")]
            )

        except Exception as e:
            if api_log:
                api_log.sudo().write({
                    'response_data': json.dumps(
                        {"status": "error", "message": f"Unexpected error: {str(e)}"}),
                })
            return request.make_response(
                json.dumps({"status": "error", "message": f"Unexpected error: {str(e)}"}),
                headers=[("Content-Type", "application/json")],
                status=500
            )

    # @http.route('/api/pricelist', type='json', auth='public', methods=['POST'], csrf=False)
    # def craeteorupdatepricelist(self):
    #     try:
    #         # Validate API Key
    #         VALID_API_KEY = self._get_valid_api_key()
    #         api_key = request.httprequest.headers.get('x-api-key')
    #         if api_key != VALID_API_KEY:
    #             return {'result': 0, 'status': 'error', 'message': 'Unauthorized: Invalid API Key'}, 401
    #
    #         data = json.loads(request.httprequest.get_data())
    #
    #         # Extract top-level info
    #         pricelist_id = data.get('ID')
    #         pricelist_name = data.get('Name')
    #         item_list = data.get('ItemList', [])
    #         customers = data.get('Customers', [])
    #
    #         for customer in customers:
    #             cardcode = customer.get('CardCode')
    #             partner = request.env['res.partner'].sudo().search([('cardcode', '=', cardcode)], limit=1)
    #             company_id = request.env['res.company'].sudo().search([('cardcode', '=', cardcode)], limit=1)
    #             if not partner:
    #                 continue  # Skip if customer not found
    #
    #             for item in item_list:
    #                 item_code = item.get('ItemCode')
    #                 price = item.get('Price', 1.0)
    #                 product = request.env['product.product'].sudo().search([('default_code', '=', item_code)], limit=1)
    #                 if not product:
    #                     continue  # Skip if product not found
    #
    #                 # Check if supplier info already exists
    #                 supplier_info = request.env['product.supplierinfo'].sudo().search([
    #                     ('product_tmpl_id', '=', product.product_tmpl_id.id),
    #                     ('partner_id', '=', partner.id),
    #                     ('pricelist_id', '=', pricelist_id)
    #                 ], limit=1)
    #
    #                 if supplier_info:
    #                     supplier_info.write({
    #                         'price': price,
    #                         'pricelist_name': pricelist_name,
    #                     })
    #                 else:
    #                     request.env['product.supplierinfo'].sudo().create({
    #                         'product_tmpl_id': product.product_tmpl_id.id,
    #                         'partner_id': partner.id,
    #                         'min_qty': 1,
    #                         'price': price,
    #                         'pricelist_id': pricelist_id,
    #                         'pricelist_name': pricelist_name,
    #                         'company_id': company_id.id if company_id else False
    #                     })
    #
    #         return {
    #             'result': 1,
    #             'status': 'success',
    #             'message': 'Pricelist data processed successfully',
    #         }
    #
    #     except Exception as e:
    #         return {'result': 0, 'status': 'error', 'message': str(e)}

    @http.route('/api/customer_series', type='json', auth='public', methods=['POST'], csrf=False)
    def create_or_update_customer_series_api(self, **post):
        api_log = None
        try:
            VALID_API_KEY = self._get_valid_api_key()

            # Validate API Key
            api_key = request.httprequest.headers.get('x-api-key')
            if api_key != VALID_API_KEY:
                return {
                    "Result": 0,
                    "Message": "Unauthorized: Invalid API Key",
                    "series_id": 0,
                    "series_name": "",
                    "error": "Invalid API Key"
                }

            # Load and validate JSON
            data = json.loads(request.httprequest.get_data())
            api_log = request.env['api.log'].sudo().create({
                'name': '/api/pos/customer_series',
                'request_data': json.dumps(data)
            })

            if not data:
                if api_log:
                    api_log.sudo().write({
                        'response_data': json.dumps(
                            {
                                "Result": 0,
                                "Message": "Invalid JSON",
                                "series_id": 0,
                                "series_name": "",
                                "error": "Missing or malformed JSON"
                            }),
                    })
                return {
                    "Result": 0,
                    "Message": "Invalid JSON",
                    "series_id": 0,
                    "series_name": "",
                    "error": "Missing or malformed JSON"
                }

            # Check if series exists
            customer_series = request.env['customer.series'].sudo().search(
                [('code', '=', data.get('code'))],
                limit=1
            )

            if customer_series:
                customer_series.sudo().write({
                    'name': data.get('name'),
                    'code': data.get('code'),
                })
                status = 'Updated'
            else:
                customer_series = request.env['customer.series'].sudo().create({
                    'name': data.get('name'),
                    'code': data.get('code'),
                })
                status = 'Created'

            if api_log:
                api_log.sudo().write({
                    'response_data': json.dumps(
                        {
                            "Result": 1,
                            "Message": "Success",
                            "Status": status,
                            "series_id": customer_series.id,
                            "series_name": customer_series.name,
                            "error": None
                        }),
                })
            return {
                "Result": 1,
                "Message": "Success",
                "Status": status,
                "series_id": customer_series.id,
                "series_name": customer_series.name,
                "error": None
            }

        except Exception as e:
            if api_log:
                api_log.sudo().write({
                    'response_data': json.dumps(
                        {
                            "Result": 0,
                            "Message": "Error occurred",
                            "series_id": 0,
                            "series_name": "",
                            "error": str(e)
                        }),
                })
            return {
                "Result": 0,
                "Message": "Error occurred",
                "series_id": 0,
                "series_name": "",
                "error": str(e)
            }

    @http.route('/api/customer_group', type='json', auth='public', methods=['POST'], csrf=False)
    def create_or_update_customer_group(self, **post):
        api_log = None
        try:
            VALID_API_KEY = self._get_valid_api_key()

            # Validate API Key
            api_key = request.httprequest.headers.get('x-api-key')
            if api_key != VALID_API_KEY:
                return {
                    "Result": 0,
                    "Message": "Unauthorized: Invalid API Key",
                    "group_id": 0,
                    "group_name": "",
                    "error": "Invalid API Key"
                }

            # Load and validate JSON
            data = json.loads(request.httprequest.get_data())
            api_log = request.env['api.log'].sudo().create({
                'name': '/api/pos/customer_group',
                'request_data': json.dumps(data)
            })

            if not data:
                if api_log:
                    api_log.sudo().write({
                        'response_data': json.dumps(
                            {
                                "Result": 0,
                                "Message": "Invalid JSON",
                                "group_id": 0,
                                "group_name": "",
                                "error": "Missing or malformed JSON"
                            }),
                    })
                return {
                    "Result": 0,
                    "Message": "Invalid JSON",
                    "group_id": 0,
                    "group_name": "",
                    "error": "Missing or malformed JSON"
                }

            # Check if group exists
            customer_group = request.env['customer.group'].sudo().search(
                [('code', '=', data.get('code'))],
                limit=1
            )

            if customer_group:
                customer_group.sudo().write({
                    'group_name': data.get('group_name'),
                    'grouptype': data.get('grouptype'),
                    'locked': data.get('locked'),
                })
                status = 'Updated'
            else:
                customer_group = request.env['customer.group'].sudo().create({
                    'code': data.get('code'),
                    'group_name': data.get('group_name'),
                    'grouptype': data.get('grouptype'),
                    'locked': data.get('locked'),
                })
                status = 'Created'

            if api_log:
                api_log.sudo().write({
                    'response_data': json.dumps(
                        {
                            "Result": 1,
                            "Message": "Success",
                            "Status": status,
                            "group_id": customer_group.id,
                            "group_name": customer_group.group_name,
                            "error": None
                        }),
                })
            return {
                "Result": 1,
                "Message": "Success",
                "Status": status,
                "group_id": customer_group.id,
                "group_name": customer_group.group_name,
                "error": None
            }

        except Exception as e:
            if api_log:
                api_log.sudo().write({
                    'response_data': json.dumps(
                        {
                            "Result": 0,
                            "Message": "Error occurred",
                            "group_id": 0,
                            "group_name": "",
                            "error": str(e)
                        }),
                })
            return {
                "Result": 0,
                "Message": "Error occurred",
                "group_id": 0,
                "group_name": "",
                "error": str(e)
            }

    @http.route('/api/payment_term', type='json', auth='public', methods=['POST'], csrf=False)
    def create_or_update_sap_payment_term(self, **post):
        api_log = None
        try:
            VALID_API_KEY = self._get_valid_api_key()

            # Validate API Key
            api_key = request.httprequest.headers.get('x-api-key')
            if api_key != VALID_API_KEY:
                return {
                    "Result": 0,
                    "Message": "Unauthorized: Invalid API Key",
                    "payment_term_id": 0,
                    "payment_term_name": "",
                    "error": "Invalid API Key"
                }

            # Load and validate JSON
            data = json.loads(request.httprequest.get_data())
            api_log = request.env['api.log'].sudo().create({
                'name': '/api/pos/sap_payment_term',
                'request_data': json.dumps(data)
            })

            if not data:
                if api_log:
                    api_log.sudo().write({
                        'response_data': json.dumps(
                            {
                                "Result": 0,
                                "Message": "Invalid JSON",
                                "payment_term_id": 0,
                                "payment_term_name": "",
                                "error": "Missing or malformed JSON"
                            }),
                    })
                return {
                    "Result": 0,
                    "Message": "Invalid JSON",
                    "payment_term_id": 0,
                    "payment_term_name": "",
                    "error": "Missing or malformed JSON"
                }

            # Check if payment term exists
            sap_payment_term = request.env['sap.payment.term'].sudo().search(
                [('groupnum', '=', data.get('groupnum'))],
                limit=1
            )

            if sap_payment_term:
                sap_payment_term.sudo().write({
                    'pymntgroup': data.get('pymntgroup'),
                    'extradays': data.get('extradays'),
                })
                status = 'Updated'
            else:
                sap_payment_term = request.env['sap.payment.term'].sudo().create({
                    'groupnum': data.get('groupnum'),
                    'pymntgroup': data.get('pymntgroup'),
                    'extradays': data.get('extradays'),
                })
                status = 'Created'

            if api_log:
                api_log.sudo().write({
                    'response_data': json.dumps(
                        {
                            "Result": 1,
                            "Message": "Success",
                            "Status": status,
                            "payment_term_id": sap_payment_term.id,
                            "payment_term_name": sap_payment_term.pymntgroup,
                            "error": None
                        }),
                })
            return {
                "Result": 1,
                "Message": "Success",
                "Status": status,
                "payment_term_id": sap_payment_term.id,
                "payment_term_name": sap_payment_term.pymntgroup,
                "error": None
            }

        except Exception as e:
            if api_log:
                api_log.sudo().write({
                    'response_data': json.dumps(
                        {
                            "Result": 0,
                            "Message": "Error occurred",
                            "payment_term_id": 0,
                            "payment_term_name": "",
                            "error": str(e)
                        }),
                })
            return {
                "Result": 0,
                "Message": "Error occurred",
                "payment_term_id": 0,
                "payment_term_name": "",
                "error": str(e)
            }
