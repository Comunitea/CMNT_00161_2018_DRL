# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Milk planning',
    'version': '11.0.1.0.0',
    'category': 'Sales',
    'author': 'Comunitea',
    'maintainer': 'Comunitea',
    'website': 'www.comunitea.com',
    'license': 'AGPL-3',
    'depends': ['product', 'stock', 'sale', 'purchase', 'onchange_helper'],
    'data': [
        'views/res_config_settings.xml',
        'views/milk_planning.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
}
