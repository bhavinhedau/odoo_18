from odoo import models, fields

class DateRangeWizard(models.TransientModel):
    _name = 'date.range.wizard'
    _description = 'Date Range Wizard'

    date_from = fields.Date(string="From Date", required=True)
    date_to = fields.Date(string="To Date", required=True)

    def action_apply(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Records',
            'res_model': 'machinery.progress',
            'view_mode': 'list,form',
            'domain': [
                ('create_date', '>=', self.date_from),
                ('create_date', '<=', self.date_to),
            ],
        }
