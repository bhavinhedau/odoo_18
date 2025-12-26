from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
import json
import requests

class ResPartnernherit(models.Model):
    _inherit = 'res.partner'

    cardcode = fields.Char(string='CardCode',copy=False)
    rownumber = fields.Integer(string='Row Number',default=0)
    contact_code = fields.Char(string="Contacts",copy=False)
    contact_person = fields.Char(string="Contact Person")

    @api.model
    def _check_vat_number(self, country_code, vat_number):
        #by pass the GST validation
        return True

    def get_customer_json(self):
        data = False
        for record in self:

            bp_addresses=[]
            bank_data=[]
            BPFiscalTaxIDCollection=[]
            address_parts = filter(None, [
                record.street,
                record.street2,
                record.city,
                record.state_id.name if record.state_id else None,
                record.zip,
                record.country_id.name if record.country_id else None
            ])
            full_address = ', '.join(address_parts)

            ContactEmployees = [{
                # "Name": record.contact_person,
                # "FirstName": "Sarthik",
                # "MiddleName": ".",
                # "LastName": ".",
                # "Position": ".",
                "Address": full_address,
                "MobilePhone": record.phone,
                "E_Mail": record.email
            }]
            # print(ContactEmployees)
            for child in record.child_ids.filtered(lambda a: a.type in ['invoice', 'delivery']):
                address = {
                    "RowNum": child.rownumber,
                    "BPCode": "",
                    "AddressType": "bo_BillTo" if child.type == 'invoice' else "bo_ShipTo",
                    "AddressName": child.contact_code,
                    "Street": child.street or "",
                    "Block": child.street2 or "",
                    "BuildingFloorRoom": "",
                    "ZipCode": child.zip or "",
                    "City": child.city or "",
                    "Country": child.country_id.code if child.country_id else "",
                    "State": child.state_id.code if child.state_id else "",
                }

                if child.vat:
                    address["GSTIN"] = child.vat
                    address["GstType"] = "gstRegularTDSISD"

                bp_addresses.append(address)

            for bank in record.bank_ids:
                bank_data.append({
                    "Branch": bank.branch,
                    "Country": 'IN',
                    "BankCode": bank.bank_id.bic,
                    "AccountNo": bank.acc_number,
                    "InternalKey": '',
                    "AccountName": bank.accountname,
                    "BICSwiftCode": bank.bicswiftcode
                })
            # print(bank_data)
            for child in record.child_ids.filtered(lambda a: a.type in ['invoice']):
                BPFiscalTaxIDCollection.append({
                    "Address": child.name if child.name else record.name,
                    "TaxId0": record.l10n_in_pan,
                    "TaxId13": record.l10n_in_pan,
                    "BPCode": "",
                    "AddrType": "bo_ShipTo"
                })
            data = {
                "U_Q_OdooID": record.id,
                "Series": record.series_id.code,
                "CardName": record.name,
                "AliasName": "",
                "CardForeignName": "",
                "CardType": "cCustomer",
                "CreditLimit": record.credit_limit or 0.0,
                "GroupCode": record.customer_group.code,
                "PayTermsGrpCode": record.property_payment_term_id.sap_ref.groupnum if record.property_payment_term_id else 0,
                # "SalesPersonCode": record.user_id.id if record.user_id else -1,
                "Currency":  "##",
                "Cellular": record.phone or "",
                "EmailAddress": record.email or "",
                "Valid": "tYES" if record.active else "tNO",
                "BPAddresses": bp_addresses,
                "ContactEmployees": ContactEmployees,
                "BPBranchAssignment": [],
                "BPBankAccounts": bank_data,
                "BPFiscalTaxIDCollection": BPFiscalTaxIDCollection,
                "ChannelBP": record.company_id.cardcode,
                "PriceListNum":record.sap_pricelist_id.code

            }
        # print(json.dumps(data))
        return data

    def export_to_sap(self):
        for record in self:
            data = record.get_customer_json()
            print(data)
    def update_to_sap(self):
        pass

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    rownumber = fields.Integer(string='Row Number',default=0,copy=False)
    branch = fields.Char(string="Branch")
    inernalkey = fields.Integer(string="InternalKey")
    accountname = fields.Char(string="AccountName")
    bicswiftcode = fields.Char(string="IFSC Code")


