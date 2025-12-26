# -*- coding: utf-8 -*-
from os import write

from odoo import models, fields, api
import json
import requests
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    doc_entry = fields.Char(string="SAP DocEntry")
    sap_sync_response = fields.Text(string="SAP Sync Response")
    json = fields.Text(string="SAP JSON")

    # Header Level UDFs  Domestic Fields

    sales_type = fields.Selection([('1','INDIRECT EXPORT SALES'),('2','LOCAL SALES A/C'),
                                   ('3','OGS SALES A/C'),('4','DIRECT EXPORT A/C'),
                                   ('5','SALES RETURN'),('6','INTER BRANCH SALES')],
                                  string="Sales Type")

    transporter_code = fields.Char(string="Transport Code",size=155)
    Name_Of_Transpt = fields.Char(string="Name Of Transporter",size=50)
    une_invf = fields.Char(string="Freight Charges",size=16)
    freightterm = fields.Selection([('1','Paid'),('2','To Pay'),('3','Paid By Customer'),('4','To Pay By Customer')],string="Freight Term")
    delinst = fields.Char(string="Delivery Instruction")
    indentyype = fields.Selection([('yes','YES'),('no','NO')],string="Indentor")
    indentagent = fields.Char(stirng="Indenting Agent Code",size=50)
    indentname = fields.Char(string="Indenting Agent Name",size=30)
    commper = fields.Float(string="Commission (%)")
    commrs = fields.Float(string="Commission (RS)")
    consigtype = fields.Selection([('other','Other'),('customer','Customer')],string="Consignee Type")
    consigneecode = fields.Char(string="Consignee Code",size=15)
    consigneeshipiD = fields.Char(string="Consignee Ship To ID",size=40)
    consigneename = fields.Char(string="Consignee Name",size=50)
    consigneeadd = fields.Char(string="Consignee Address")
    ordertype = fields.Selection([('local','LOCAL'),('export','EXPORT')],string="Order Type")





    # Header Level UDFs export additional Fields

    conorg = fields.Char(string="Country Of Origin Of Goods",size=30)
    bldate = fields.Datetime(string="BL Date")
    bl_type = fields.Selection([('1','ORIGINAL BL'),('2','SEAWAY BL'),('3','EXPRESS BL'),
                                ('4','SURRENDER BL'),('5','SWITCH BL')],string="BL Type")

    bl_special_instruction = fields.Char(string="BL Special Instruction")
    portload = fields.Char(string="Port Of Loading",size=30)
    portdis = fields.Char(string="Port Of Discharge",size=30)
    orgnl_doc_courier = fields.Char(string="Original Doc Courier Type")
    finaldesc = fields.Char(string="Final Destination Country",size=30)
    finaldes = fields.Char(string="Final Destination",size=30)
    delins = fields.Char(string="Delivery Instructions")
    inco_term = fields.Char(string="Inco Term",size=50)
    notify_party = fields.Char(string="Notify Party")

    # PIGMENT FIELD
    excisetran = fields.Char(string="Excise Transaction Category", size=30)
    precarr = fields.Char(string="Pre-Carrier Receipt", size=30)


    # sap fields tab calculation

    # @api.onchange('commper')
    # def _onchange_commper(self):
    #     for order in self:
    #         if order.commper and order.amount_untaxed:
    #             order.commrs = (order.amount_untaxed * order.commper) / 100
    #         else:
    #             order.commrs = 0.0

    def action_post_to_sap(self):
        for order in self:
            order.apicaller_sapso()

    def apicaller_sapso(self):
        for order in self:
            if not (order.partner_id.cardcode and order.order_line and order.date_order):
                continue

            data = {
                "U_Q_OdooNum": order.name,
                "CardCode": order.partner_id.cardcode,
                "DocDate": order.date_order.strftime('%Y-%m-%d') if order.date_order else None,
                "DocDueDate": order.date_order.strftime('%Y-%m-%d') if order.date_order else None,
                "U_Q_OdooID": order.id,
                # "Series": 6519,
                "BPL_IDAssignedToInvoice": order.company_id.sap_branch_id,
                "DocumentLines": [
                    {
                        "U_OdooLine": line.id,
                        "ItemCode": line.product_id.default_code,
                        "Quantity": line.product_uom_qty,
                        "UnitPrice": line.price_unit,
                        "U_Q_OdooID": line.order_id.id,
                        "DiscountPercent": line.discount,
                    }
                    for line in order.order_line
                ],
            }
            order.write({
                'json': json.dumps(data)
            })

            try:
                url = self.env['ir.config_parameter'].sudo().get_param('sap.sale.order.url')
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url, data=json.dumps(data), headers=headers)
                result_json = response.json()

                order.sap_sync_response = json.dumps(result_json)

                if result_json.get('Message') == 'Success':
                    order.doc_entry = result_json.get('DocEntry')
                    continue

                sap_raw = result_json.get('Response') or ''
                try:
                    sap_json = json.loads(sap_raw)
                    sap_msg = sap_json.get('error', {}).get('message', {}).get('value', sap_raw)
                except:
                    sap_msg = sap_raw

                raise UserError(f"SAP Error: {sap_msg}")

            except Exception as e:
                order.sap_sync_response = str(e)
                order.doc_entry = None
                raise UserError(str(e))


class SaleOrderLine(models.Model):
    _inherit="sale.order.line"

    # MLLP PHARMA

    u_grade = fields.Selection([('0','IP Powder'),('1','BP Powder'),('2','EP Powder'),('3','USP Powder'),('4','IP Crystal'),('5','BP Crystal'),
                              ('6','BP/EP Powder'),('7','BP/EP Crystal'),('8','USP Crystal'),('9','IP Semi Crystal'),
                              ('10','BP/EP Semi Crystal'),('11','USP Semi Crystal'),('12','N-Acetyl Para Aminophenol'),('13','IP & EP/BP'),
                              ('14','IP & USP'),('15','USP & EP/BP'),('16','IP, EP/BP, USP'),('17','Chemical'),('18','IP/Chemical'),
                              ('19','IP/USP/Chemical'),('20','B.P'),('21','E.P'),('22','I.P'),('23','U.S.P'),
                              ('24','Acetaminophen/ Paracetamol JP')],string="Grade")
    u_pharma = fields.Char(string="Item Grade")
    bp_catalog_no = fields.Char(string="BP Catalog No")
    freight_term = fields.Selection([('1','Paid'),('2','To Pay'),('3','Paid By Customer'),('4','To Pay By Customer')],string="Freight Term")
    freightag = fields.Float(string="Agreed Freight")
    intval = fields.Float(string="Interest(%)")
    intcost = fields.Float(string="Interest Cost")
    commper = fields.Float(string="Commission(%)")
    commrs = fields.Float(string="Commission(rs)",compute='_onchange_commper',store=True)
    netreal = fields.Float(string="Net Realisation",compute='_compute_net_realisation',store=True)
    packtype = fields.Selection([('1','Bag'),('2','Box'),('3','Drum'),('4','Loose In Tanker'),('5','Loose In Truck')],string="Packing Type")
    u_netwtpkg = fields.Float(string="Net Weight Packing(KG)")
    totalbox =fields.Char(string="Total No Box",compute='_compute_totalbox',store=True)
    pallet_req = fields.Selection([('0','Yes'),('1','No')],string="Pallet Requirement")
    pallettype = fields.Selection([('1','30'),('2','15'),('3','105'),('4','45'),('5','10'),('6','20')],string="Pallet Type")
    palletdim = fields.Char(string="Pallet Dimensions",size=60)
    customerhsn = fields.Char(string="Customer HSN")
    marks_nos = fields.Text(string="Marks & Nos")
    adv_lic = fields.Selection([('1','YES'),('2','No')],string="Advance License?")
    lictype = fields.Selection([('1','Drawback Scheme'),('2','Drawback Scheme with STR benefit'),('3','EPCG License'),
                                ('4','Authorization License'),('5','Drawback Scheme-Ashish'),],string="License Type")
    licno = fields.Char(string="License No",size=60)
    license_date = fields.Datetime(string="License Date")

    # PIGMNET FIELD

    u_gradeII =fields.Char(string="Pigment Grade",size=30)
    application_of_test = fields.Selection([('0','SALES ORDER'),('1','AR INVOICE'),('2','AR CREDIT MEMO'),('3','PURCHASE ORDER'),
                                            ('4','AP INVOICE'),('5','AP CREDIT MEMO'),('6','GRPO'),('7','NA'),],
                                           string="Application Of Test")
    pss_css_or_direct_dispatch = fields.Char(string="PSS/CSS Require Or Direct Dispatch",size=150)
    pss_css_status = fields.Char(string="PSS/CSS Status",size=150)
    quality_reference_remark = fields.Char(string="Quality Reference Remark",size=200)
    distcode = fields.Char(string="Distance Code",size=10)
    transporter_code = fields.Char(string="Transporter Code",size=155)
    une_tpnm = fields.Char(string="Transporter Name",size=100)
    une_remk = fields.Char(string="Remarks",size=100)
    itemspecs = fields.Char(string="Item Specification")
    u_check = fields.Char(string="Check SlM Qty")
    rodtep = fields.Char(string="Rod Tep",size=30)
    packing_type_of_bag = fields.Char(string="Packing Type of Bag",size=100)
    bag_label = fields.Char(string="Bag Label")
    net_weight_packing_of_bag = fields.Char(string="Net Weight Packing (Per KG) of Bag",size=100)
    total_no_bag = fields.Char(string="Total No Bag",size=100)
    bag_dimensions = fields.Char(string="Bag Dimensions",size=100)
    packing_type_of_box = fields.Char(string="Packing Type of Box",size=100)
    net_weight_packing_of_box = fields.Char(string="Net Weight Packing (Per KG) of Box",size=100)
    box_label = fields.Char(string="Box Label")
    totalbox = fields.Selection([('0','Import'),('1','Export')],string="Total No Box")
    box_dimensions = fields.Char(string="Box Dimensions",size=100)
    packing_type_of_pallet = fields.Char(string="Packing Type Of Pallet",size=100)
    pallet_tr_weight = fields.Char(string="Pallet Tr Weight",size=100)
    net_weight_packing_of_pallet = fields.Char(string="NET WEIGHT PACKING (PER KG) OF PALLET",size=100)
    pallet_label = fields.Char(string="Pallet Label")
    total_no_pallet = fields.Char(string="Total No Pallet",size=100)
    q_returnitem = fields.Char(string="Q Return Item",size=20)



    @api.depends('u_netwtpkg', 'product_uom_qty')
    def _compute_totalbox(self):
        for rec in self:
            if rec.product_uom_qty and rec.u_netwtpkg:
                rec.totalbox = rec.product_uom_qty / rec.u_netwtpkg

    @api.depends('price_unit', 'commrs', 'intcost', 'freightag')
    def _compute_net_realisation(self):
        for rec in self:
            rec.netreal = (
                    (rec.price_unit or 0.0)
                    - (rec.commrs or 0.0)
                    - (rec.intcost or 0.0)
                    - (rec.freightag or 0.0)
            )

    @api.depends('commper','price_unit')
    def _onchange_commper(self):
        print("_onchange_commper")
        for rec in self:
            if rec.commper and rec.price_unit:
                rec.commrs = (rec.price_unit * rec.commper) / 100




