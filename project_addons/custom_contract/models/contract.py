# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class ContractContract(models.Model):

    _inherit = "contract.contract"

    contract_type = fields.Selection(default="sale")
    recurring_invoices = fields.Boolean(default=False)
    price_agreement_ids = fields.One2many(
        "contract.price.agreement", "contract_id", "Price agreements"
    )
    delivery_agreement_ids = fields.One2many(
        "contract.delivery.agreement", "contract_id", "Delivery Dates "
    )
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed")],
        readonly=True,
        default="draft",
    )

    def validate(self):

        for delivery in self.delivery_agreement_ids:
            values = self.prepare_sale_order_vals(delivery)
            so = self.env["sale.order"].create(values)
            so.action_confirm()
        self.state = "confirmed"

    def set_to_draft(self):
        sales = self.env["sale.order"].search([("contract_id", "=", self.id)])
        sales.action_cancel()
        self.state = "draft"

    def prepare_sale_order_vals(self, delivery_line):
        sale_line_vals_list = list(dict())
        price_line = self.price_agreement_ids.filtered(
            lambda price_line: price_line.product_id.id
            == delivery_line.product_id.id
        )
        if price_line:
            price = price_line[0].price_unit
        else:
            price = 0
        sale_line_vals_list.append(
            {
                "product_id": delivery_line.product_id.id,
                "name": delivery_line.product_id.name,
                "product_uom_qty": delivery_line.quantity,
                "price_unit": price,
            }
        )
        return {
            "partner_id": self.partner_id.id,
            "partner_shipping_id": delivery_line.partner_shipping_id.id,
            "requested_date": delivery_line.delivery_date,
            "contract_id": self.id,
            "payment_mode_id": self.payment_mode_id.id,
            "order_line": [
                (0, 0, sale_line_vals) for sale_line_vals in sale_line_vals_list
            ],
        }


class ContractPriceAgreement(models.Model):

    _name = "contract.price.agreement"

    product_id = fields.Many2one("product.product", "Product")
    price_unit = fields.Float(digits=dp.get_precision("Product Price"))
    contract_id = fields.Many2one("contract.contract")


class ContractDeliveryAgreement(models.Model):

    _name = "contract.delivery.agreement"

    display_name = fields.Char(
        compute="_compute_display_name", store=True, index=True
    )
    product_id = fields.Many2one("product.product", "Product")
    quantity = fields.Float(digits=dp.get_precision("Product Unit of Measure"))
    quantity_document = fields.Float(
        digits=dp.get_precision("Product Unit of Measure"),
        compute="_compute_quantity_document",
    )
    delivery_date = fields.Date("Delivery Date")
    contract_id = fields.Many2one("contract.contract")
    partner_shipping_id = fields.Many2one("res.partner", required=True)
    state = fields.Selection(related="contract_id.state")

    def _compute_quantity_document(self):
        for delivery in self:
            delivery.quantity_document = delivery.quantity * 1000

    @api.onchange("product_id")
    def product_id_change_check_contract_lines(self):
        if self.product_id and self.contract_id.price_agreement_ids:
            product_line = self.contract_id.price_agreement_ids.filtered(
                lambda r: r.product_id.id == self.product_id.id
            )
            if not product_line:
                raise UserError(
                    _("El producto no se encuentra en el contrato.")
                )

    @api.depends("product_id", "quantity")
    def _compute_display_name(self):

        for partner in self:
            partner.display_name = (
                partner.product_id.name + ": " + str(partner.quantity)
            )
