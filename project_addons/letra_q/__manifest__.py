# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Letra Q',
    'version': '11.0.1.0.0',
    'summary': '',
    'category': 'Warehouse Management',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'depends': [
        'stock',
        'weight_registry',
    ],
    'data': [
        'views/product_view.xml',
        'views/stock_view.xml',
        'views/letra_q_exporter.xml',
        'views/res_country.xml',
        'wizard/export_moves_letra_q.xml',
        'security/ir.model.access.csv'
        ],
    'installable': True,
}
