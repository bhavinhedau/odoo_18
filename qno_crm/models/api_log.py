from odoo import models, fields

class ApiLog(models.Model):
    _name = 'api.log'
    _description = 'API Request/Response Log'
    _order = 'log_datetime desc'

    name = fields.Char(string="API Name", required=True)
    request_data = fields.Text(string="Request JSON")
    response_data = fields.Text(string="Response JSON")
    log_datetime = fields.Datetime(string="Log Time", default=fields.Datetime.now, required=True)