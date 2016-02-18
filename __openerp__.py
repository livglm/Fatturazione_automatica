# -*- encoding: utf-8 -*-
##############################################################################
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Fatturazione_automatica',
    'version': '0.2',
    'category': 'Generic Modules/Others',
    'license': 'AGPL-3',
    'description': """
Sale Automatic Workflow
=======================

Create workflows with more or less automatization and apply it on sales
orders.

A workflow can:

- Apply default values:
  * Packing Policy (partial, complete)
  * Shipping Policy (prepaid, manual, postpaid, picking)
  * Invoice On (ordered quantities, shipped quantities)
  * Set the invoice's date to the sale order's date

- Apply automatic actions:
  * Validate the order (only if paid, always, never)
  * Create an invoice
  * Validate the invoice
  * Confirm the picking

This module is used by Magentoerpconnect and Prestashoperpconnect.
It is well suited for other E-Commerce connectors as well.
""",
    'author': 'Massimiliano Mauro',
    'website': 'http://www.tidielle.com/',
    'depends': ['sale_payment_method','delivery',
                'stock',
                ],
    'data': ['views/stock_view.xml',
             'views/sale_view.xml',
             'views/sale_workflow.xml',
             'views/sale_workflow_process_view.xml',
             'views/account_invoice_view.xml',
             'views/res_view.xml',
             'views/test_report.xml',
             'account_report.xml',
             #'security/ir.model.access.csv',
            ],
    'installable': True,
}
