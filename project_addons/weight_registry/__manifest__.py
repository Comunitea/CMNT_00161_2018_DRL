# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Control weight registry for Dairylac',
    'version': '12.0.1.0.0',
    'category': 'Uncategorized',
    'license': 'AGPL-3',
    'author': "Comunitea,",
    'website': 'https://www.comunitea.com',
    'depends': [
        'base',
        'stock',
        'dairylac_custom',
        'delivery',
        'web'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/weight_registry_security.xml',
        'views/assets.xml',
        'views/product_view.xml',
        'views/vehicle_view.xml',
        'views/weight_registry.xml',
        'views/stock_views.xml',
        'views/stock_picking.xml',
        'wizard/link_weight_moves_wzd.xml',
        'wizard/link_pick_to_weight.xml'
    ],
    'installable': True,
    'qweb': [
        "static/src/xml/weight_control.xml",
    ],
}
