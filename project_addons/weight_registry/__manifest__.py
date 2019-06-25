# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Control weight registry for Dairylac',
    'version': '11.0.1.0.0',
    'category': 'Uncategorized',
    'license': 'AGPL-3',
    'author': "Comunitea,",
    'website': 'https://www.comunitea.com',
    'depends': [
        'base',
        'stock',
        'dairylac_custom'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/weight_registry_security.xml',
        'views/vehicle_view.xml',
        'views/weight_registry.xml',
        'views/stock_views.xml',
        'wizard/weight_to_pick_wzd.xml'

    ],
    'installable': True,
}
