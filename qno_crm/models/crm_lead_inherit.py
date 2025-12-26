from odoo import models, fields, api
from odoo.tools import html2plaintext


class CrmLead(models.Model):
    _inherit = "crm.lead"

    description_plaintext = fields.Text(
        string="Notes",
        compute='_compute_description_plaintext',
        store=True
    )

    @api.depends('description')
    def _compute_description_plaintext(self):
        for lead in self:
            if lead.description:
                lead.description_plaintext = html2plaintext(lead.description)
            else:
                lead.description_plaintext = False
       
