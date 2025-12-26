from odoo import api, fields, models


class MachineryDraftWizard(models.TransientModel):
    _name = 'machinery.draft.wizard'
    _description = 'Wizard to write remarks before setting Draft state'

    remarks = fields.Text(string="Remarks", required=True)

    def action_confirm_draft(self):
        main_record = self.env['machinery.progress'].browse(
            self.env.context.get('active_id')
        )
        main_record.write({'state': 'draft', 'remarks': self.remarks})
        return {'type': 'ir.actions.act_window_close'}
