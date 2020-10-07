# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_id = fields.Many2one('contract.contract')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _get_display_price(self, product):
        if self.order_id.contract_id.price_agreement_ids:
            product_line = self.order_id.contract_id.price_agreement_ids\
                .filtered(
                lambda r: r.product_id.id == self.product_id.id)
            if product_line:
                return product_line.price_unit
        return super()._get_display_price(product)

    @api.onchange('product_id')
    def product_id_change_check_contract(self):
        if self.product_id and self.order_id.contract_id.price_agreement_ids:
            product_line = self.order_id.contract_id.price_agreement_ids\
                .filtered(
                lambda r: r.product_id.id == self.product_id.id)
            if not product_line:
                raise UserError(_('El producto no se encuentra en el contrato.'))
