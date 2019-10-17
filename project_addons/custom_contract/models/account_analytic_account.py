# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api,fields, models
import odoo.addons.decimal_precision as dp



class AccountAnalyticAccount(models.Model):

    _inherit = 'account.analytic.account'


    type = fields.Selection(default='sale')
    recurring_invoices = fields.Boolean(default=False)
    price_agreement_ids = fields.One2many(
        'account.analytic.account.price.agreement',
        'analytic_account_id',
        'Price agreements')
    delivery_agreement_ids = fields.One2many(
        'contract.delivery.agreement',
        'analytic_account_id',
        'Delivery Dates ')
    state = fields.Selection([
        ('draft', "Draft"),
        ('confirmed', "Confirmed"), ],
        readonly=True, default="draft")

    def validate(self):

        for delivery in self.delivery_agreement_ids:
            values = self.prepare_sale_order_vals(delivery)
            so = self.env['sale.order'].create(values)
            so.action_confirm()
        self.state = 'confirmed'

    def set_to_draft(self):
        sales = self.env['sale.order'].search(
            [('analytic_account_id', '=', self.id)])
        sales.action_cancel()
        self.state = 'draft'

    def prepare_sale_order_vals(self, delivery_line):
        sale_line_vals_list = list(dict())
        price_line = self.price_agreement_ids.filtered(
            lambda price_line: price_line.product_id.id ==
                               delivery_line.product_id.id)
        if price_line:
            price = price_line[0].price_unit
        else:
            price = 0
        sale_line_vals_list.append({
            'product_id': delivery_line.product_id.id,
            'name': delivery_line.product_id.name,
            'product_uom_qty': delivery_line.quantity,
            'price_unit': price,
        })
        return {
            'partner_id': self.partner_id.id,
            'partner_shipping_id': delivery_line.partner_shipping_id.id,
            'requested_date': delivery_line.delivery_date,
            'analytic_account_id': self.id,
            'payment_mode_id': self.payment_mode_id.id,
            'order_line': [(0, 0, sale_line_vals)
                           for sale_line_vals in sale_line_vals_list]
        }

class AccountAnalyticAccountPriceAgreement(models.Model):

    _name = 'account.analytic.account.price.agreement'

    product_id = fields.Many2one('product.product', 'Product')
    price_unit = fields.Float(digits=dp.get_precision('Product Price'),)
    analytic_account_id = fields.Many2one('account.analytic.account')


class ContractDeliveryAgreement(models.Model):

    _name = 'contract.delivery.agreement'

    display_name = fields.Char(compute='_compute_display_name', store=True,
                              index=True)
    product_id = fields.Many2one('product.product', 'Product')
    quantity = fields.Float(digits=dp.get_precision(
        'Product Unit of Measure'))
    delivery_date =  fields.Date('Delivery Date')
    analytic_account_id = fields.Many2one('account.analytic.account')
    partner_shipping_id = fields.Many2one('res.partner')
    state = fields.Selection(related="analytic_account_id.state")

    @api.depends('product_id', 'quantity')
    def _compute_display_name(self):

        for partner in self:
            partner.display_name = partner.product_id.name + \
                                   ": " + str(partner.quantity)