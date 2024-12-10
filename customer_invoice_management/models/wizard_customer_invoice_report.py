from odoo import models, fields, api, _
import base64

import logging
import datetime

from odoo.exceptions import UserError, ValidationError
_logger = logging.getLogger(__name__)


class CustomerInvoiceReportWizard(models.TransientModel):
    _name = 'customer.invoice.report.wizard'
    _description = 'Customer Invoice Report Wizard'

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    partner_ids = fields.Many2many('res.partner', string='Customer')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    email_body = fields.Text(string="Email Body")


    def generate_and_send_invoice_report(self):
        invoice_report = self.env.ref('customer_invoice_management.action_report_customer_invoice_summary')
        _logger.warning('######################################### CUSTOMER')
        _logger.warning(self.partner_ids)
        if(self.partner_ids):
            if(len(self.partner_ids.ids) == 1):
                invoices = self.env['account.move'].search([
                    ('move_type', '=', 'out_invoice'),
                    ('partner_id', 'in', self.partner_ids.ids),
                    ('invoice_date', '>=', self.start_date),
                    ('invoice_date', '<=', self.end_date),
                ])
            else:
                raise ValidationError(_("You can choose only one customer."))
        else:
            raise ValidationError(_("You have to choose a customer."))
        # Raise an error if no invoices found
        if not invoices:
            raise ValidationError(_("No invoices found for the selected criteria."))
        
        # Prepare the data to be passed
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'partner_id': self.partner_ids.ids,
            'invoices': invoices.ids,
        }
        generated_report = self.env['ir.actions.report']._render_qweb_pdf(invoice_report, [self.id], data=data)
        data_record = base64.b64encode(generated_report[0])
        ir_values = {
            'name': _('Invoice Report %s - %s',self.start_date, self.end_date) ,
            'type': 'binary',
            'datas': data_record,
            'mimetype': 'application/pdf',
            'res_model': 'customer.invoice.report.wizard',
            }
        invoice_report_attachment_id = self.env[
            'ir.attachment'].sudo().create(
            ir_values)

        _logger.warning('#########################################')
        template = self.env.ref('customer_invoice_management.invoice_report_email_template')
        email_values = template.generate_email(self.ids,['subject', 'body_html',
             'email_from',
             'email_cc', 'email_to', 'partner_to', 'reply_to',
             'auto_delete', 'scheduled_date'])

        

        _logger.warning('WARNING: DATA RECORD 0--  %s', template)
        _logger.warning('WARNING: DATA RECORD 1--  %s', email_values[self.id].get('body_html', ''))
        _logger.warning('#########################################')

        report_action = {
            'name': ('Send Invoice'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'customer.invoice.report.preview',
            'views': [[False, 'form']],
            'target': 'new',
            'context': {'default_attachment_ids' : [(6, 0, invoice_report_attachment_id.ids)],
                        'default_subject' : email_values[self.id]['subject'],
                        'default_body' : email_values[self.id]['body_html'],
                        'default_email_to' : email_values[self.id]['email_to'],
                        },
        }
        return report_action
        


    def generate_report(self):
        self.ensure_one()

        # Check date validity
        if self.end_date < self.start_date:
            raise UserError("End Date must be greater than Start Date.")
        
        # Fetch the invoices
        if(self.partner_ids.ids):
            invoices = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('partner_id', 'in', self.partner_ids.ids),
                ('invoice_date', '>=', self.start_date),
                ('invoice_date', '<=', self.end_date),
            ])
        else:
            invoices = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('invoice_date', '>=', self.start_date),
                ('invoice_date', '<=', self.end_date),
            ])
        
        # Raise an error if no invoices found
        if not invoices:
            raise ValidationError(_("No invoices found for the selected criteria."))
        
        # Prepare the data to be passed
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'partner_id': self.partner_ids.ids,
            'invoices': invoices.ids,
        }
        _logger.info("Found %d invoices for partner: %s between %s and %s", len(invoices), self.partner_ids.mapped('name'), self.start_date, self.end_date)

        # Pass the invoice IDs and the data to the report
        return self.env.ref('customer_invoice_management.action_report_customer_invoice_summary').report_action(invoices.ids, data=data)

    




class CustomerInvoiceReport(models.AbstractModel):
    _name = 'report.customer_invoice_management.customer_invoice_report_summary_template'
    _table = 'report_cust_inv_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        # Fetch the partner, start_date, and end_date from the data dict
        partner_ids = data.get('partner_ids')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        invoices = data.get('invoices')
        _logger.info("CHECKING DATA %s", data)
        _logger.info("CHECKING DATA %s", docids)


        if not invoices:
            raise ValidationError(_("No document IDs provided for report generation."))

        # Get the partner object
        partner = self.env['res.partner'].browse(partner_ids)
        
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
        if(isinstance(start_date, str)):
            start_date = (datetime.datetime.strptime(start_date, '%Y-%m-%d')).strftime('%d %b %Y')
            end_date = (datetime.datetime.strptime(end_date, '%Y-%m-%d')).strftime('%d %b %Y')
        else:
            start_date = start_date.strftime('%d %b %Y') 
            end_date = end_date.strftime('%d %b %Y')


        return {
            'docs': invoices,  # This is the invoice records
            'partner': partner,  # Pass the partner to use in the report
            'start_date': start_date,
            'end_date': end_date,
            'tax_dict': tax_dict,
        }

class CustomerInvoiceReportPreview(models.TransientModel):
    _name = 'customer.invoice.report.preview'
    _description = 'Customer Invoice Report Preview'
    _inherits = {'mail.compose.message':'composer_id'}

    report_wizard_id = fields.Many2one('customer.invoice.report.wizard')
    email_to = fields.Char(string="Recipient")

    def send_and_print_action(self):
        email_template = self.env.ref(
            'customer_invoice_management.invoice_report_email_template')
        
        if email_template:
            email_values = {
                'email_to': self.email_to,
                'email_cc': False,
                'scheduled_date': False,
                'recipient_ids': [],
                'partner_ids': [],
                'auto_delete': True,
                'body_html': self.body,
            }
            if(self.attachment_ids):
                email_template.attachment_ids = [(6, 0, self.attachment_ids.ids)]
            email_template.send_mail(
                self.id, email_values=email_values, force_send=True)



class GlobalInvoiceReportWizard(models.TransientModel):
    _name = 'global.invoice.report.wizard'
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)


    def generate_global_report(self):
        self.ensure_one()

        # Check date validity
        if self.end_date < self.start_date:
            raise UserError("End Date must be greater than Start Date.")

        # Define the domain
        domain = [
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice'),
            ('invoice_date', '>=', self.start_date),
            ('invoice_date', '<=', self.end_date)
        ]

        # Use read_group to aggregate data
        result = self.env['account.move'].read_group(
            domain=domain,
            fields=['amount_total:sum', 'amount_untaxed:sum', 'amount_tax:sum'],
            groupby=['partner_id']
        )

        # Format the result for the report
        formatted_result = [
            {
                'partner': group.get('partner_id', ('Unknown', 'Unknown'))[1] if group.get('partner_id') else 'No Partner',
                'amount_total': group.get('amount_total', 0.0),
                'amount_untaxed': group.get('amount_untaxed', 0.0),
                'amount_tax': group.get('amount_tax', 0.0),
            }
            for group in result
        ]
        return formatted_result

    def action_print_global_invoice_report(self):
        # This method triggers the report
        return self.env.ref('customer_invoice_management.action_global_invoice_report').report_action(self)