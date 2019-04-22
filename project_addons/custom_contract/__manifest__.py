# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Contract customizations',
    'version': '11.0.1.0.0',
    'summary': '',
    'category': 'Contract Management',
    'author': 'Comunitea',
    'license': 'AGPL-3',
    'depends': [
        'contract',
        'contract_sale_generation',
    ],
    'data': [
        'views/account_analytic_account.xml',
        'security/ir.model.access.csv'],
    'installable': True,
}
