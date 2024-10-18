from odoo import models, fields, api
import base64

import logging

from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)


class CustomerInvoiceReportWizard(models.TransientModel):
    _name = 'customer.invoice.report.wizard'
    _description = 'Customer Invoice Report Wizard'

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)


    def generate_report(self):
        self.ensure_one()

        # Check date validity
        if self.end_date < self.start_date:
            raise UserError("End Date must be greater than Start Date.")
        
        # Fetch the invoices
        invoices = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('partner_id', '=', self.partner_id.id),
            ('invoice_date', '>=', self.start_date),
            ('invoice_date', '<=', self.end_date),
        ])
        
        # Raise an error if no invoices found
        if not invoices:
            raise ValidationError("No invoices found for the selected criteria.")
        
        # Prepare the data to be passed
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'partner_id': self.partner_id.id,
            'invoices': invoices.ids,
        }
        _logger.info("Found %d invoices for partner: %s between %s and %s", len(invoices), self.partner_id.name, self.start_date, self.end_date)

        # Pass the invoice IDs and the data to the report
        return self.env.ref('customer_invoice_management.action_report_customer_invoice_summary').report_action(invoices.ids, data=data)

    




class CustomerInvoiceReport(models.AbstractModel):
    _name = 'report.customer_invoice_management.customer_invoice_report_summary_template'
    _table = 'report_cust_inv_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        # Fetch the partner, start_date, and end_date from the data dict
        partner_id = data.get('partner_id')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        invoices = data.get('invoices')
        _logger.info("CHECKING DATA %s", data)
        _logger.info("CHECKING DATA %s", docids)


        if not invoices:
            raise ValidationError("No document IDs provided for report generation.")

        # Get the partner object
        partner = self.env['res.partner'].browse(partner_id)
        
        # Fetch the invoice records using docids (this is automatically passed from the wizard)
        invoices = self.env['account.move'].browse(invoices)

        tax_dict = {}

        for account_line in invoices.mapped('invoice_line_ids'):
            for tax in account_line.tax_ids:
                if(tax.id in tax_dict):

                    tax_dict[tax.id][1] += account_line.price_subtotal
                    tax_dict[tax.id][2] += account_line.price_subtotal * (tax.amount / 100)

                else:
                    tax_dict[tax.id] = [
                                            tax.description,  # tax description
                                            account_line.price_subtotal,  # subtotal for the first time
                                            account_line.price_subtotal * (tax.amount / 100)  # tax amount for the first time
                                        ]

        _logger.info("CHECKING INVOICES %s", invoices)
        _logger.info("CHECKING TAXES %s", tax_dict)

        return {
            'docs': invoices,  # This is the invoice records
            'partner': partner,  # Pass the partner to use in the report
            'start_date': start_date,
            'end_date': end_date,
            'tax_dict': tax_dict,
        }