# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError


class ContractContract(models.Model):

    _inherit = "contract.contract"

    contract_type = fields.Selection(default="sale")
    recurring_invoices = fields.Boolean(default=False)
    price_agreement_ids = fields.One2many(
        "contract.price.agreement", "contract_id", "Price agreements", states={'confirmed': [('readonly', True)]}, copy=True
    )
    delivery_agreement_ids = fields.One2many(
        "contract.delivery.agreement", "contract_id", "Delivery dates", states={'confirmed': [('readonly', True)]}, copy=True
    )
    quality_demand_ids = fields.One2many(
        "contract.quality.demand", "contract_id", "Quality demands", states={'confirmed': [('readonly', True)]}, copy=True
    )
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed")],
        readonly=True,
        default="draft",
    )
    available_product_ids = fields.Many2many(
        string='Available Products',
        comodel_name='product.product',
        compute='_compute_available_product_ids',
    )
    sale_order_ids = fields.One2many(
        "sale.order", "contract_id", "Sale orders"
    )
    sale_count = fields.Integer(compute="_compute_sale_count")
    picking_count = fields.Integer(compute="_compute_picking_count")
    delivery_count = fields.Integer(compute="_compute_delivery_count")
    carrier_id = fields.Many2one(comodel_name="delivery.carrier", string="Transportista")

    @api.multi
    def _compute_sale_count(self):
        for rec in self:
            rec.sale_count = len(rec.sale_order_ids.filtered(lambda x: x.state in ['sale', 'sent', 'done']))
            
    def _compute_delivery_count(self):
        for rec in self:
            rec.delivery_count = len(rec.delivery_agreement_ids.filtered(lambda x: x.state in ['draft']))
            
    @api.multi
    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = len(rec._get_related_pickings())

    @api.multi
    @api.depends('price_agreement_ids')
    def _compute_available_product_ids(self):
        for contract in self:
            contract.update({
                'available_product_ids': [(6, 0, contract.price_agreement_ids.mapped('product_id').ids)]
            })

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
            "commitment_date": delivery_line.load_date,
            "contract_id": self.id,
            "carrier_id": self.carrier_id and self.carrier_id.id,
            "payment_mode_id": self.payment_mode_id.id,
            "order_line": [
                (0, 0, sale_line_vals) for sale_line_vals in sale_line_vals_list
            ],
        }
        
    @api.multi
    def action_show_pickings(self):
        self.ensure_one()
        tree_view_ref = (
            'stock.vpicktree'
        )
        form_view_ref = (
            'stock.view_picking_form'
        )
        tree_view = self.env.ref(tree_view_ref, raise_if_not_found=False)
        form_view = self.env.ref(form_view_ref, raise_if_not_found=False)
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Pickings',
            'res_model': 'stock.picking',
            'view_type': 'form',
            'view_mode': 'tree,kanban,form,calendar',
            'domain': [('id', 'in', self._get_related_pickings().ids)],
        }
        if tree_view and form_view:
            action['views'] = [(tree_view.id, 'tree'), (form_view.id, 'form')]
        return action

    
    @api.multi
    def action_show_sales(self):
        self.ensure_one()
        tree_view_ref = (
            'sale.view_order_tree'
        )
        form_view_ref = (
            'sale.view_order_form'
        )
        tree_view = self.env.ref(tree_view_ref, raise_if_not_found=False)
        form_view = self.env.ref(form_view_ref, raise_if_not_found=False)
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Sales',
            'res_model': 'sale.order',
            'view_type': 'form',
            'view_mode': 'tree,kanban,form,calendar,pivot,graph,activity',
            'domain': [('id', 'in', self.sale_order_ids.ids), ('state', 'in', ('sale', 'sent', 'done'))],
        }
        if tree_view and form_view:
            action['views'] = [(tree_view.id, 'tree'), (form_view.id, 'form')]
        return action

    @api.multi
    def action_show_deliveries(self):
        self.ensure_one()
        form_view_ref = (
            'custom_contract.view_contract_delivery_form'
        )
        calendar_view_ref = (
            'custom_contract.view_contract_delivery_calendar'
        )
    
        form_view = self.env.ref(form_view_ref, raise_if_not_found=False)
        calendar_view = self.env.ref(calendar_view_ref, raise_if_not_found=False)
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Deliveries',
            'res_model': 'contract.delivery.agreement',
            'view_type': 'form',
            'view_mode': 'calendar',
            'domain': [('id', 'in', self.delivery_agreement_ids.ids), ('state', '=', 'draft')],
        }
        if form_view and calendar_view:
            action['views'] = [ (calendar_view.id, 'calendar'), (form_view.id, 'form')]
        return action


    @api.multi
    def _get_related_invoices(self):
        res = super()._get_related_invoices()
        res |= self.sale_order_ids.mapped('invoice_ids')
        return res
    
    @api.multi
    def _get_related_pickings(self):

        res = self.sale_order_ids.mapped('picking_ids').filtered(lambda r: r.state not in ('draft', 'cancel'))
        return res

class ContractPriceAgreement(models.Model):

    _name = "contract.price.agreement"

    product_id = fields.Many2one("product.product", "Product")
    price_unit = fields.Float(digits=dp.get_precision("Product Price"))
    contract_id = fields.Many2one("contract.contract")

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id and self.product_id.lst_price:
            self.price_unit = self.product_id.lst_price

    @api.multi
    @api.constrains('product_id', 'contract_id')
    def _check_product_id_contract_id(self):
        for agreement in self:
            if agreement.product_id and agreement.contract_id.delivery_agreement_ids and\
                    agreement.product_id.id in agreement.contract_id.delivery_agreement_ids.mapped('product_id').ids:
                raise ValidationError(
                    _('The product is already in the price agreements list.'))

class ContractDeliveryAgreement(models.Model):

    _name = "contract.delivery.agreement"

    display_name = fields.Char(
        compute="_compute_display_name", store=True, index=True
    )
    product_id = fields.Many2one("product.product", "Product", required=True)
    quantity = fields.Float(digits=dp.get_precision("Product Unit of Measure"))
    quantity_document = fields.Float(
        digits=dp.get_precision("Product Unit of Measure"),
        compute="_compute_quantity_document",
    )
    delivery_date = fields.Date("Delivery Date", required=True)
    load_date = fields.Date("Load Date", required=True)
    contract_id = fields.Many2one("contract.contract")
    partner_shipping_id = fields.Many2one("res.partner", required=True)
    state = fields.Selection(related="contract_id.state")
    available_product_ids = fields.Many2many(related="contract_id.available_product_ids")
    price_unit = fields.Float(digits=dp.get_precision("Product Price"), required=True)

    def _compute_quantity_document(self):
        for delivery in self:
            delivery.quantity_document = delivery.quantity

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

class ContractQualityDemand(models.Model):

    _name = "contract.quality.demand"

    contract_id = fields.Many2one("contract.contract")
    product_id = fields.Many2one("product.product", "Product")
    available_product_ids = fields.Many2many(related="contract_id.available_product_ids")
    available_qc_test_ids = fields.Many2many(compute="_compute_available_qc_test")
    qc_test_id = fields.Many2one(
        "qc.test"
    )
    qc_test_question_id = fields.Many2one(
        "qc.test.question"
    )
    price_change = fields.Selection([
        ('bonus', _('Bonus')),
        ('discount', _('Discount')),
    ])
    comparative_sign = fields.Selection([
        ('greaterThan', _('>')),
        ('equal', _('=')),
        ('lowerThan', _('<')),
    ])
    standard_value = fields.Float("Standard Value", digits=dp.get_precision('Quality Control'))
    tolerance = fields.Float("Tolerance", digits=dp.get_precision('Quality Control'))
    value = fields.Float("Value", digits=dp.get_precision('Quality Control'))

    @api.depends("product_id")
    def _compute_available_qc_test(self):
        for demand in self:
            if demand.product_id:
                test_ids = self.env['qc.test'].search([
                    '|',
                    ('type', '=', 'generic'),
                    ('object_id', '!=', False)
                ]).filtered(lambda x: x.type == 'generic' or x.type == 'related' and \
                    x.object_id._name == 'product.product' and x.object_id.id == demand.product_id.id)

                demand.update({
                    'available_qc_test_ids': [(6, 0, test_ids.ids)]
                })