from odoo import api, fields, models, _, Command

class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Journal Entry"

        # === Date fields === #
    invoice_date = fields.Date(
        default=fields.Date.context_today
    )