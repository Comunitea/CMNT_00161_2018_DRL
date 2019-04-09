# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Custom modification for Dairylac',
    'version': '11.0.1.0.0',
    'category': 'Uncategorized',
    'license': 'AGPL-3',
    'author': "Comunitea,",
    'website': 'https://www.comunitea.com',
    'depends': [
        'base',
        'delivery'
    ],
    'data': [
    'views/res_partner_view.xml',
    'views/vehicle_view.xml',
    'views/deposit_view.xml',
    'views/delivery_carrier_view.xml'

    ],
    'installable': True,
}
