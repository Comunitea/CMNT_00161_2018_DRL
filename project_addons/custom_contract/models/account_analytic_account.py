# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountAnalyticAccount(models.Model):

    _inherit = 'account.analytic.account'

    type = fields.Selection(default='sale')
    recurring_invoices = fields.Boolean(default=False)
    price_agreement_ids = fields.One2many(
        'account.analytic.account.price.agreement',
        'analytic_account_id',
        'Price agreements')


class AccountAnalyticAccountPriceAgreement(models.Model):

    _name = 'account.analytic.account.price.agreement'

    product_id = fields.Many2one('product.product', 'Product')
    price_unit = fields.Float()
    analytic_account_id = fields.Many2one('account.analytic.account')
