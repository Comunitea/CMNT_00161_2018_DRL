# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Custom Stock',
    'version': '12.0.1.0.0',
    'summary': '',
    'category': 'Stock',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'depends': [
        'stock',
        'mrp',
        'letra_q'
    ],
    'data': [
        'data/stock_data.xml',
        'views/mrp_production.xml',
    ],
    'installable': True,
}
