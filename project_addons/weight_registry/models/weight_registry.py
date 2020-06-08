# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import datetime
from odoo import models, fields, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo.tools.float_utils import float_compare, float_round, float_is_zero

# import logging

# _logger = logging.getLogger('WHEIGHT_REGISTRY')


REGISTRY_TYPE = [
    ('incoming', 'Incoming'),
    ('outgoing', 'Outgoing'),
    ('production', 'Production'),
    ('internal', 'Internal'),
    ('wash', 'Wash'),
    ('other', 'Other'),
    ('none', 'None')]

WEIGHT_REGISTRY_STATES = [
    ('0', '1º Control'),
    ('1', '1º Control. Pick'),
    ('2', '2º Control. No albarán'),
    ('3', 'Pendiente de asignar'),
    ('4', 'Asignado')
]


class WeightRegistryType(models.Model):

    _name = "weight.registry.type"

    def _get_types(self):
        selection = []
        return selection

    code = fields.Char('Code')
    description = fields.Char('Description')
    move_type_id = fields.Selection(selection=_get_types, string="Move type")
    picking_ids = fields.Many2many('stock.picking', string="Linked pickings")

class WeightRegistry(models.Model):

    _name = "weight.registry"

    _order = "id desc"

    vehicle_id = fields.Many2one('vehicle', string="Vehicle", required=True)
    vehicle_ids = fields.Many2many('vehicle', string="Listado de matrículas", required=True)
    vehicle_str = fields.Char('Vehicles string')
    scale_weight = fields.Integer('weight')
    fill = fields.Boolean(
        'Fill', compute='_compute_worked_hours', store=True, readonly=True)
    check_in = fields.Datetime(
        string="Check In", default=fields.Datetime.now, required=True)
    check_out = fields.Datetime(string="Check Out")
    worked_hours = fields.Float(
        string='Worked Hours', compute='_compute_worked_hours',
        store=True, readonly=True)
    check_in_weight = fields.Integer('Check in weight')
    check_out_weight = fields.Integer('Check out weight')
    net = fields.Integer(
        'Net weight', compute='_compute_worked_hours',
        store=True, readonly=True)
    partner_id = fields.Many2one(
        'res.partner', 'Measured by', domain=[('driver', '=', True)])
    note = fields.Text('Notes')
    worked_hours = fields.Float(
        string='Worked Hours', compute='_compute_worked_hours',
        store=True, readonly=True)
    # move_line_ids = fields.One2many(
    #     'stock.move', 'weight_registry_id', string="Weight register")
    # picking_id = fields.Many2one('stock.picking')
    registry_type = fields.Selection(
        REGISTRY_TYPE, string="Registy type", required=False)
    product_id = fields.Many2one('product.product', 'Product')
    line_ids = fields.One2many('weight.registry.line', 'registry_id', 
                               'Registry Lines')

    used_line_ids = fields.One2many('weight.registry.line', 'registry_id', domain=[('used','=', True)], string='Used Registry Lines')
    picking_ids = fields.Many2many('stock.picking',  "stock_picking_weight_rel", string="Albaranes asociados")
    state = fields.Selection(selection=WEIGHT_REGISTRY_STATES, string='Estado', compute ="compute_state", store=True, help="")


    @api.depends('check_in_weight', 'check_out_weight', 'picking_ids', 'used_line_ids.move_line_id')
    def compute_state(self):
        for wc in self:
            if wc.check_out_weight:
                if wc.picking_ids:
                    if wc.used_line_ids.mapped('move_line_id'):
                        wc.state = '4'
                    else:
                        wc.state = '3'
                else:
                    wc.state = '2'
            elif wc.check_in_weight:
                if wc.picking_ids:
                    wc.state = '1'
                else:
                    wc.state = '0'

    # def apply_net_to_qty_done(self):
    #     for w_r in self.filtered(lambda x: x.check_out):
    #         qty_done = w_r.net
    #         if any(x.state == 'done' for x in w_r.mapped('move_line_ids')):
    #             raise exceptions.ValidationError(
    #                 _('Move {} is done.'.format(
    #                     w_r.mapped('move_line_ids').mapped('display_name'))))

    #         for mv in w_r.move_line_ids:
    #             for ml in mv.move_line_ids:
    #                 mv.qty_done = min(ml.product_uom_qty, qty_done)
    #                 qty_done -= mv.qty_done
    #             if qty_done:
    #                 mv.qty_done += qty_done

    # def unlink(self):
    #     self.action_unlink_weight()
    #     return super().unlink()

    # def action_unlink_weight(self):
    #     for w_r in self:
    #         w_r.mapped('picking_id').do_unreserve()
    #         w_r.picking_id = False

    @api.multi
    def action_show_wizard_control(self):

        return


    @api.onchange('vehicle_ids')
    def onchange_vehicle_ids(self):
        vehicle_str = ''
        for v in self.vehicle_ids:

            vehicle_str = "{} {}".format(vehicle_str, v.register)

        self.vehicle_str = vehicle_str

    def name_get(self):
        result = []
        for registry in self:
            if not registry.check_out:
                result.append((registry.id, _("%(empl_name)s [%(check_in)s] : %(weight)s Kg") % {
                    'empl_name': registry.vehicle_id.register,
                    'weight': registry.check_in_weight,
                    'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(registry,
                                                                                            fields.Datetime.from_string(
                                                                                                registry.check_in))),
                }))
            else:
                result.append((registry.id, _("%(empl_name)s [%(check_in)s] : %(weight_in)s Kg --> [%(check_out)s] : %(weight_out)s Kg") % {
                    'empl_name': registry.vehicle_id.register,
                    'weight_in': registry.check_in_weight,
                    'weight_out': registry.check_out_weight,
                    'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(registry,
                                                                                            fields.Datetime.from_string(
                                                                                                registry.check_in))),
                    'check_out': fields.Datetime.to_string(fields.Datetime.context_timestamp(registry,
                                                                                             fields.Datetime.from_string(
                                                                                                 registry.check_out))),
                }))
        return result

    @api.depends(
        'check_in', 'check_out', 'check_in_weight', 'check_out_weight')
    def _compute_worked_hours(self):
        for registry in self:
            if registry.check_out:
                # delta = datetime.strptime(
                #     registry.check_out,
                #     DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                #     registry.check_in, DEFAULT_SERVER_DATETIME_FORMAT)
                delta =  registry.check_out - registry.check_in
                registry.worked_hours = delta.total_seconds() / 3600.0

                registry.net = abs(
                    registry.check_in_weight - registry.check_out_weight)
                registry.fill = registry.check_out_weight > registry.check_in_weight


    def get_checkout_vals(self, date, weight=0.00, measured_by=False):
        if self.check_in_weight > weight:
            gross = self.check_in_weight
            tara = weight
        else:
            tara = self.check_in_weight
            gross = weight
        net = gross-tara

        vals = {'check_out': date,
                'weight_check_out': weight,
                'net': net,
                'registry_type': 'incoming' if self.check_in_weight > weight else 'outgoing'
                }
        return vals

    @api.constrains('check_in', 'check_out', 'vehicle_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared
            to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for registry in self:
            # we take the latest attendance before our check_in
            # time and check it doesn't overlap with ours
            last_reg_before_check_in = self.env['weight.registry'].search([
                ('vehicle_id', '=', registry.vehicle_id.id),
                ('check_in', '<=', registry.check_in),
                ('id', '!=', registry.id),
            ], order='check_in desc', limit=1)
            if last_reg_before_check_in and \
                    last_reg_before_check_in.check_out and \
                    last_reg_before_check_in.check_out > registry.check_in:
                raise exceptions.ValidationError(_(
                    "Cannot create new registry record for %(empl_name)s, the vehicle was already checked in on %(datetime)s") %
                    {'empl_name': registry.vehicle_id.register,
                     'datetime': fields.Datetime.to_string(
                        fields.Datetime.context_timestamp(
                            self, fields.Datetime.from_string(registry.check_in))),
                     })

            if not registry.check_out:
                # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
                no_check_out_registry = self.env['weight.registry'].search([
                    ('vehicle_id', '=', registry.vehicle_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', registry.id),
                ], order='check_in desc', limit=1)
                if no_check_out_registry:
                    raise exceptions.ValidationError(_(
                        "Cannot create new registry record for %(empl_name)s, the vehicle hasn't checked out since %(datetime)s") % {
                                                         'empl_name': registry.vehicle_id.register,
                                                         'datetime': fields.Datetime.to_string(
                                                             fields.Datetime.context_timestamp(self,
                                                                                               fields.Datetime.from_string(
                                                                                                   no_check_out_registry.check_in))),
                                                     })
            else:
                # we verify that the latest attendance with check_in time before our check_out time
                # is the same as the one before our check_in time computed before, otherwise it overlaps
                last_reg_before_check_out = self.env['weight.registry'].search([
                    ('vehicle_id', '=', registry.vehicle_id.id),
                    ('check_in', '<', registry.check_out),
                    ('id', '!=', registry.id),
                ], order='check_in desc', limit=1)
                if last_reg_before_check_out and last_reg_before_check_in != last_reg_before_check_out:
                    raise exceptions.ValidationError(_(
                        "Cannot create new registry record for %(empl_name)s, the vehicle was already checked in on %(datetime)s") % {
                                                         'empl_name': registry.vehicle_id.register,
                                                         'datetime': fields.Datetime.to_string(
                                                             fields.Datetime.context_timestamp(self,
                                                                                               fields.Datetime.from_string(
                                                                                                   last_reg_before_check_out.check_in))),
                                                     })
    @api.model
    def _estimate_qty_in_deposits(self, deposits, net):
        res = {}
        # _logger.info("DEPOSITS")
        # _logger.info(deposits)
        # import ipdb; ipdb.set_trace()
        # used_deposits = [dep for dep in deposits if dep['check']]
        # _logger.info("USED DEPOSITS")
        # _logger.info(used_deposits)
        used_deposit_ids = [int(dep['id']) for dep in deposits if dep['check']]
        used_deposits = self.env['deposit'].browse(used_deposit_ids)
        total_capacity = sum(used_deposits.mapped('capacity'))
        if not total_capacity:
            return res

        factor = net / total_capacity
        for dep in used_deposits:
            res[dep.id] = factor * dep.capacity
        return res

    @api.multi
    def recalc_weight_lines(self):
        for wc_id in self:
            deposit_ids = wc_id.line_ids.filtered(lambda x: x.used).mapped('deposit_id')
            total_capacity = sum(deposit_ids.mapped('capacity'))
            factor = wc_id.net/total_capacity
            for line in wc_id.line_ids.filtered(lambda x: x.used):
                line.qty = factor * line.deposit_id.capacity
        return True


    def generate_weight_lines(self, vehicle_ids, weight, deposits):
        deposit_qtys = self._estimate_qty_in_deposits(deposits, weight)

        for dep in deposits:
            deposit_id = int(dep['id'])
            qty = deposit_qtys.get(deposit_id, 0.0)
            vals = {
                'registry_id': weight,
                'deposit_id': deposit_id,
                'used': dep['check'],
                'qty': qty
            }
            self.env['weight.registry.line'].create(vals)
        return True

    @api.model
    def set_weight_registry(self, vehicle_id, weight, deposits, vehicles):
        res = True
        vehicle = self.env['vehicle'].browse(vehicle_id)
        reg = vehicle.vehicle_action_change(weight)
        if reg:
            vehicle_ids = [x['id'] for x in vehicles]
            reg.vehicle_ids = [(6, 0, vehicle_ids)]
            reg.onchange_vehicle_ids()
            if not reg.check_in_weight:
                reg.check_in_weight = weight
            else:
                reg.check_out_weight = weight

            if not deposits:
                return res
            deposit_qtys = self._estimate_qty_in_deposits(deposits, reg.net)
            if not reg.line_ids:
                ## En este caso las lineas se crean en el 2 pesaje
                for dep in deposits:
                    deposit_id = int(dep['id'])
                    qty = deposit_qtys.get(deposit_id, 0.0)
                    vals = {
                        'register': reg.vehicle_id.register,
                        'registry_id': reg.id,
                        'deposit_id': deposit_id,
                        'used': dep['check'],
                        'qty': qty
                    }
                    self.env['weight.registry.line'].create(vals)
            else:
                ## En este caso las lineas se crean antes del pesaje
                ## por lo tanto ya tengo un albarán y unos movimientos asovciados a la línea
                move_id = reg.picking_ids[0].move_lines
                if move_id.quantity_done == 0:
                    update_move_line = True
                product_id = move_id.product_id
                ##paso el pesaje neto a miles de litros
                available_total_qty = product_id.uom_id._compute_quantity(reg.net, move_id.product_uom)

                for line in reg.line_ids.filtered(lambda x: x.used):
                    qty = deposit_qtys.get(line.deposit_id.id, 0.0)
                    available_total_qty -= qty
                    line.qty = qty
                    if update_move_line:
                        line.move_line_id.write({'qty_done': qty})

                ## lo que sobra/falte lo meto en el último deposito
                line.qty += available_total_qty
                if update_move_line:
                    line.move_line_id.write({'qty_done': line.qty})
                    ## Escribo la cantidad total







            return res

    @api.model
    def set_weight_registry_bis(self, vehicle_id, weight, deposits):
        res = True
        vehicle = self.env['vehicle'].browse(vehicle_id)
        reg = vehicle.vehicle_action_change()
        if reg:
            if not reg.check_in_weight:
                reg.check_in_weight = weight
            else:
                reg.check_out_weight = weight

            if not deposits:
                return res

            deposit_qtys = self._estimate_qty_in_deposits(deposits, reg.net)
            for dep in deposits:
                deposit_id = int(dep['id'])
                qty = deposit_qtys.get(deposit_id, 0.0)
                vals = {
                    'registry_id':reg.id,
                    'deposit_id': deposit_id,
                    'used': dep['check'],
                    'qty': qty
                }
                self.env['weight.registry.line'].create(vals)
        return res

    @api.multi
    def create_new_wzd(self):
        return self._create_new_wzd()

    @api.multi
    def _create_new_wzd(self, picking_id=False, product_id=False):
        self.ensure_one()
        domain = [
            #('picking_type_id.weight_control', '=', self.registry_type),

                  ('picking_id.weight_registry_ids', '=', False),
                  ('date_expected', '<=', fields.Date.to_string(date.today() + relativedelta(days=7)))
                  ]
        moves = self.env['stock.move'].search(domain)

        wzd_vals = {'type': self.registry_type,
                    'registry_id': self.id,
                    'product': self.product_id,
                    'fill': self.fill,
                    'net': self.net,
                    #'qty_flowmeter': self.qty_flowmeter,
                    #'select_qty': False,
                    'select_pick': True,
                    }
        if not self.check_out:
            self.line_ids.unlink()
            deposit_ids = self.vehicle_ids.mapped('deposit_ids')
            for dep in deposit_ids:
                vals = {
                    'register': dep.vehicle_id.register,
                    'registry_id': self.id,
                    'deposit_id': dep.id,
                    'used': True,
                    'qty': dep.capacity
                }
                self.env['weight.registry.line'].create(vals)

        wzd_id = self.env['stock.picking.weight.control.wzd'].create(wzd_vals)
        if picking_id:
            new_line_val={'wzd_id': wzd_id.id,
                           'picking_id': picking_id.id,
                           'product_id': product_id.id}
            new_line = self.env['available.line.picks.wzd'].create(new_line_val)
            new_line.action_link_picking_id()

        else:
            for move in moves:
                new_line_val = {'wzd_id': wzd_id.id,
                                'picking_id': move.picking_id.id,
                                'product_id': move.product_id.id}
                self.env['available.line.picks.wzd'].create(new_line_val)

        action = wzd_id.get_formview_action()
        action['target'] = 'new'
        # return action
        action['res_id'] = wzd_id.id
        return action

class WeightRegistryLine(models.Model):

    _name = "weight.registry.line"

    registry_id = fields.Many2one('weight.registry', 'Weight Registry', required=True, ondelete="cascade")
    deposit_id = fields.Many2one('deposit', 'Deposit')
    capacity = fields.Float('Capacity', related='deposit_id.capacity')
    # One2many para que al asignarlo al stock.move.line, se asigne solo
    move_line_id = fields.Many2one('stock.move.line', 'Move')
    used = fields.Boolean('Used')
    empty = fields.Boolean('Empty', default=True)
    filled = fields.Boolean('Filled', related="registry_id.fill")
    qty = fields.Float('Estimated Qty')
    qty_flowmeter = fields.Float('Flow meter Qty')
    picking_id = fields.Many2one('stock.picking', string="Albarán asociado")

    def name_get(self):
        result = []
        for line in self:
            custom_name = \
                "%(veh)s[%(check_out)s] Nº: %(deposit)s (%(cap)s) - \
                    [%(qty)s / %(net)s]" % \
            {
                'veh': line.registry_id.vehicle_id.register,
                'check_out': line.registry_id.check_in,
                'deposit': line.deposit_id.number,
                'cap': line.deposit_id.capacity,
                'qty': line.qty,
                'net': line.registry_id.net,
            }
            result.append((line.id, custom_name))
        return result

    @api.multi
    def create_new_wzd(self):
        self.ensure_one()
        wzd_vals = {'type': self.type,
                    'registry_id': self.id,
                    'product': self.product_id,
                    'fill': self.fill,
                    'net': self.net,
                    'qty_flowmeter': self.qty_flowmeter,
                    'select_qty': self.select_qty,
                    'select_pick': True
                    }
        wzd_id = self.env['stock.picking.weight.control.wzd'].create(wzd_vals)
        action = wzd_id.get_formview_action()
        action['target'] = 'new'
        # return action
        action['res_id'] = wzd_id.id
        return action


    @api.multi
    def create_move_line(self, picking_id = False):
        ##SUPONGO UN PRODUCTO POR ALBARAN Y UN PRODUCTO POR PESADA
        registry_id = self[0].registry_id
        control_product_id = registry_id.product_id
        if not control_product_id:
            raise ValueError(_('Weigth registry must be linked to a product: {}'.format(registry_id.name)))

        move_line = picking_id.move_lines.filtered(lambda x: x.product_id == control_product_id)
        if len(move_line) != 1:
            raise ValueError(_('Incorrect number of products in picking: {}'.format(picking_id.name)))

        move_line._prepare_move_line_vals(self, quantity=None)





