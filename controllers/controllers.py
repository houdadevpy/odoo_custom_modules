# -*- coding: utf-8 -*-
# from odoo import http


# class CustomerInvoiceManagement(http.Controller):
#     @http.route('/customer_invoice_management/customer_invoice_management', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/customer_invoice_management/customer_invoice_management/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('customer_invoice_management.listing', {
#             'root': '/customer_invoice_management/customer_invoice_management',
#             'objects': http.request.env['customer_invoice_management.customer_invoice_management'].search([]),
#         })

#     @http.route('/customer_invoice_management/customer_invoice_management/objects/<model("customer_invoice_management.customer_invoice_management"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('customer_invoice_management.object', {
#             'object': obj
#         })
