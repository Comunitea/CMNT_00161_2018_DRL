# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import format_date
from dateutil.relativedelta import relativedelta


class MilkPlanning(models.Model):

    _name = 'milk.planning'
    _order = 'date_start desc'

    @api.multi
    def name_get(self):
        result = []
        for planning in self:
            date_start = format_date(
                self.env, planning.date_start, self.env.user.lang)
            date_end = format_date(
                self.env, planning.date_end, self.env.user.lang)
            result.append(
                (planning.id, "%s - %s" %
                 (date_start, date_end)))
        return result

    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)
    milk_stock = fields.Float()
    milk_do_stock = fields.Float()
    milk_100_stock = fields.Float()
    cream_stock = fields.Float()
    milk_purchase_ids = fields.One2many(
        'milk.planning.purchase', 'planning_id',
        domain=[('purchase_type', '=', 'milk')])
    milk_do_purchase_ids = fields.One2many(
        'milk.planning.purchase', 'planning_id',
        domain=[('purchase_type', '=', 'milk_do')])
    milk_100_purchase_ids = fields.One2many(
        'milk.planning.purchase', 'planning_id',
        domain=[('purchase_type', '=', 'milk_100')])
    cream_purchase_ids = fields.One2many(
        'milk.planning.purchase', 'planning_id',
        domain=[('purchase_type', '=', 'cream')])
    raw_milk_sale_ids = fields.One2many(
        'milk.planning.sale', 'planning_id',
        domain=[('sale_type', '=', 'raw_milk')], readonly=True)
    raw_milk_do_sale_ids = fields.One2many(
        'milk.planning.sale', 'planning_id',
        domain=[('sale_type', '=', 'raw_milk_do')], readonly=True)
    raw_milk_100_sale_ids = fields.One2many(
        'milk.planning.sale', 'planning_id',
        domain=[('sale_type', '=', 'raw_milk_100')], readonly=True)
    skimmed_milk_sale_ids = fields.One2many(
        'milk.planning.sale', 'planning_id',
        domain=[('sale_type', '=', 'skimmed_milk')], readonly=True)
    cream_sale_ids = fields.One2many(
        'milk.planning.sale', 'planning_id',
        domain=[('sale_type', '=', 'cream')], readonly=True)
    milk_stock_ids = fields.One2many(
        'milk.planning.stock', 'planning_id',
        domain=[('stock_type', '=', 'milk')])
    milk_do_stock_ids = fields.One2many(
        'milk.planning.stock', 'planning_id',
        domain=[('stock_type', '=', 'milk_do')])
    milk_100_stock_ids = fields.One2many(
        'milk.planning.stock', 'planning_id',
        domain=[('stock_type', '=', 'milk_100')])
    cream_stock_ids = fields.One2many(
        'milk.planning.stock', 'planning_id',
        domain=[('stock_type', '=', 'cream')])

    def get_range(self):
        days = []
        day = self.date_start
        while day <= self.date_end:
            days.append(day)
            day = fields.Date.from_string(day) + relativedelta(days=1)
        return days

    def find_sales(self):
        for day in self.get_range():
            # La fecha del albaran es datetime,
            # asi que tenemos que buscar por la última hora del día.
            day_datetime_start = day.strftime('%m/%d/%Y') + ' 00:00:00'
            day_datetime_end = day.strftime('%m/%d/%Y') + ' 23:59:59'
            for product_name in ['raw_milk',
                                 'raw_milk_do',
                                 'raw_milk_100',
                                 'skimmed_milk',
                                 'cream']:
                product_id = self.env[
                    'product.product'].get_milk_product_by_name(
                        product_name).id
                moves = self.env['stock.move'].read_group(
                    [('sale_line_id', '!=', False),
                     ('picking_type_id.code', '=', 'outgoing'),
                     ('state', 'in',
                     ('waiting', 'confirmed',
                      'partially_available', 'assigned')),
                     ('date_expected', '>=', day_datetime_start),
                     ('date_expected', '<=', day_datetime_end),
                     ('product_id', '=', product_id)],
                    fields=['sale_line_id', 'product_uom_qty'],
                    groupby=['sale_line_id', 'product_uom_qty'],
                    lazy=False)
                contracts = self.env[
                    'contract.delivery.agreement'].search(
                     [('state', 'in',
                      ('draft',)),
                     ('delivery_date', '>=', day_datetime_start),
                     ('delivery_date', '<=', day_datetime_end),
                     ('product_id', '=', product_id)],
                    )

                move_quantity = 0
                contract_quantity = 0
                orders = []
                deliveries = []
                if moves:
                    order_lines = [x['sale_line_id'][0] for x in moves]
                    order_ids = self.env['sale.order.line'].browse(
                        order_lines).read(['order_id'])
                    orders = [x['order_id'][0] for x in order_ids]
                    move_quantity = sum([x['product_uom_qty'] for x in moves])
                if contracts:
                    deliveries = contracts.ids
                    contract_quantity = sum([x['quantity'] for x in contracts])
                total_quantity = move_quantity + contract_quantity
                self.env['milk.planning.sale'].create({
                    'day': day,
                    'confirmed_quantity': move_quantity,
                    'sale_type': product_name,
                    'planning_id': self.id,
                    'order_ids': [(6, 0, orders)],
                    'contract_quantity': contract_quantity,
                    'contract_ids': [(6, 0, deliveries)],
                    'quantity': total_quantity,
                })

    def generate_stocks(self):
        last_day_milk_stock = self.milk_stock
        last_day_milk_do_stock = self.milk_do_stock
        last_day_milk_100_stock = self.milk_100_stock
        last_day_cream_stock = self.cream_stock
        for day in self.get_range():

            raw_milk_100_sales = sum(self.raw_milk_100_sale_ids.filtered(
                lambda r: r.day == day).mapped('quantity'))
            raw_milk_do_sales = sum(self.raw_milk_do_sale_ids.filtered(
                lambda r: r.day == day).mapped('quantity'))
            raw_milk_sales = sum(self.raw_milk_sale_ids.filtered(
                lambda r: r.day == day).mapped('quantity'))
            skimmed_milk_sales = sum(self.skimmed_milk_sale_ids.filtered(
                lambda r: r.day == day).mapped('quantity'))
            milk_purchases = sum(self.milk_purchase_ids.filtered(
                lambda r: r.day == day).mapped('quantity'))
            milk_do_purchases = sum(self.milk_do_purchase_ids.filtered(
                lambda r: r.day == day).mapped('quantity'))
            milk_100_purchases = sum(self.milk_100_purchase_ids.filtered(
                lambda r: r.day == day).mapped('quantity'))

            remaining_milk_stock = last_day_milk_stock - raw_milk_sales - \
                skimmed_milk_sales * 0.895 + milk_purchases
            remaining_milk_do_stock = last_day_milk_do_stock - \
                                      raw_milk_do_sales + milk_do_purchases
            remaining_milk_100_stock = last_day_milk_100_stock - \
                                      raw_milk_100_sales + milk_do_purchases

            self.env['milk.planning.stock'].create({
                'day': day,
                'remaining_stock': remaining_milk_stock,
                'planning_id': self.id,
                'stock_type': 'milk'
            })
            self.env['milk.planning.stock'].create({
                'day': day,
                'remaining_stock': remaining_milk_do_stock,
                'planning_id': self.id,
                'stock_type': 'milk_do'
            })
            self.env['milk.planning.stock'].create({
                'day': day,
                'remaining_stock': remaining_milk_100_stock,
                'planning_id': self.id,
                'stock_type': 'milk_100'
            })


            cream_sales = sum(self.cream_sale_ids.filtered(
                lambda r: r.day == day).mapped('quantity'))
            cream_purchases = sum(self.cream_purchase_ids.filtered(
                lambda r: r.day == day).mapped('quantity'))
            skimmed_milk_cream = skimmed_milk_sales * 0.105

            remaining_cream_stock = last_day_cream_stock - cream_sales + \
                cream_purchases + skimmed_milk_cream

            self.env['milk.planning.stock'].create({
                'day': day,
                'remaining_stock': remaining_cream_stock,
                'planning_id': self.id,
                'stock_type': 'cream'
            })

            last_day_milk_stock = remaining_milk_stock
            last_day_cream_stock = remaining_cream_stock

    def calculate(self):
        self.env['milk.planning.stock'].search(
            [('planning_id', '=', self.id)]).unlink()
        self.env['milk.planning.sale'].search(
            [('planning_id', '=', self.id)]).unlink()
        self.find_sales()
        self.generate_stocks()


class MilkPlanningStock(models.Model):

    _name = 'milk.planning.stock'
    _order = 'day'

    day = fields.Date()
    remaining_stock = fields.Float()
    stock_type = fields.Selection([('milk', 'Milk'),
                                   ('milk_do', 'Milk D.O.'),
                                   ('milk_100', 'Milk 100%'),
                                   ('cream', 'Cream')])
    planning_id = fields.Many2one('milk.planning')


class MilkPlanningPurchase(models.Model):

    _name = 'milk.planning.purchase'
    _order = 'day'

    partner_id = fields.Many2one(
        'res.partner', 'Supplier', domain=[('supplier', '=', True)])
    day = fields.Date(required=True)
    quantity = fields.Float()
    purchase_type = fields.Selection([('milk', 'Milk'),
                                   ('milk_do', 'Milk D.O.'),
                                   ('milk_do', 'Milk 100%'),
                                   ('cream', 'Cream')])
    planning_id = fields.Many2one('milk.planning')
    order_ids = fields.Many2many('purchase.order')
    has_order_ids = fields.Boolean(compute='_compute_has_order_ids')

    @api.depends('order_ids')
    def _compute_has_order_ids(self):
        for purchase in self:
            if purchase.order_ids:
                purchase.has_order_ids = True
            else:
                purchase.has_order_ids = False

    def action_create_order(self):
        if not self.partner_id:
            raise UserError(_('The order can not be created without \
establishing a supplier'))
        purchase_type = self.purchase_type
        if purchase_type == 'milk':
            purchase_type = 'raw_milk'  # Solo se compra leche cruda.
        product = self.env['product.product'].get_milk_product_by_name(
            purchase_type)
        vals = {'partner_id': self.partner_id.id}
        vals = self.env['purchase.order'].play_onchanges(vals, ['partner_id'])
        purchase = self.env['purchase.order'].create(vals)
        line_vals = {
            'product_id': product.id,
            'date_planned': self.day,
            'product_qty': self.quantity,
            'order_id': purchase.id,
            'price_unit': 0.0
        }
        line_vals = self.env['purchase.order.line'].play_onchanges(
            line_vals, ['product_id', 'date_planned', 'product_qty'])
        self.env['purchase.order.line'].create(line_vals)
        self.write({'order_ids': [(4, purchase.id)]})
        return self.action_view_orders()

    def action_view_orders(self):
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        if len(self.order_ids) == 1:
            action['views'] = [
                (self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = self.order_ids.id
        else:
            action['domain'] = [('id', 'in', self.order_ids.ids)]
        return action


class MilkPlanningSale(models.Model):

    _name = 'milk.planning.sale'
    _order = 'day'

    day = fields.Date()
    confirmed_quantity = fields.Float()
    contract_quantity = fields.Float()
    quantity = fields.Float()
    sale_type = fields.Selection(
        [('raw_milk', 'Raw milk'),
         ('raw_milk_do', 'Raw milk D.O.'),
         ('raw_milk_100', 'Raw milk 100%'),
         ('skimmed_milk', 'Skimmed milk'),
         ('cream', 'Cream milk')])
    planning_id = fields.Many2one('milk.planning')
    order_ids = fields.Many2many('sale.order')
    contract_ids = fields.Many2many('contract.delivery.agreement')
    has_order_ids = fields.Boolean(compute='_compute_has_order_ids')
    has_contract_ids = fields.Boolean(compute='_compute_has_contract_ids')

    @api.depends('order_ids')
    def _compute_has_order_ids(self):
        for sale in self:
            if sale.order_ids:
                sale.has_order_ids = True
            else:
                sale.has_order_ids = False

    @api.depends('contract_ids')
    def _compute_has_contract_ids(self):
        for sale in self:
            if sale.contract_ids:
                sale.has_contract_ids = True
            else:
                sale.has_contract_ids = False

    def action_view_orders(self):
        action = self.env.ref('sale.action_orders').read()[0]
        if len(self.order_ids) == 1:
            action['views'] = [
                (self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = self.order_ids.id
        else:
            action['domain'] = [('id', 'in', self.order_ids.ids)]
        return action

    def action_view_contracts(self):
        action = self.env.ref('custom_contract.open_deliver_calendar').read()[0]
        action['domain'] = [('id', 'in', self.contract_ids.ids)]
        return action
