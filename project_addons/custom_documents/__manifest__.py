# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'CMNT Custom Documents',
    'version': '11.0.1.0.0',
    'category': 'Custom Documents',
    'license': 'AGPL-3',
    'author': "Comunitea,",
    'website': 'https://www.comunitea.com',
    'depends': [
        'base',
        'web',
        'sale',
        'account',
    ],
    'data': [
        'views/report_invoice.xml',
        'views/res_company_view.xml'
    ],
    'installable': True,
}
