# -*- coding: utf-8 -*-
# © 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.addons.weight_registry.models.weight_registry import REGISTRY_TYPE
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
from odoo.exceptions import UserError, ValidationError


class MoveLineWeightControlWzd(models.TransientModel):
    _name = 'move.line.weight.control.wzd'

    wzd_id = fields.Many2one('stock.picking.weight.control.wzd')
    weight_line = fields.Many2one('weight.registry.line')
    deposit_id = fields.Many2one('deposit', 'Source deposit')
    deposit_dest_id = fields.Many2one('deposit', 'Destination deposit')
    qty_weight = fields.Float('Weight qty')
    qty_flowmeter = fields.Float('Flowmeter qty')

class AvailableLinePickingsWzd(models.TransientModel):
    _name = 'available.line.picks.wzd'

    wzd_id = fields.Many2one('stock.picking.weight.control.wzd')
    product_id = fields.Many2one ('product.product')
    picking_id = fields.Many2one ('stock.picking')

    @api.multi
    def action_link_picking_id(self):
        self.ensure_one()
        self.wzd_id.state='lots'
        self.wzd_id.picking_id = self.picking_id
        self.wzd_id.product_id = self.product_id
        self.wzd_id.location_id = self.picking_id.location_id
        self.wzd_id.location_dest_id = self.picking_id.location_dest_id
        action = self.wzd_id.get_formview_action()
        action['target'] = 'new'
        return action


class AvailableLineMovesWzd(models.TransientModel):
    _name = 'available.line.moves.wzd'

    wzd_id = fields.Many2one('stock.picking.weight.control.wzd')
    product_id = fields.Many2one ('product.product')
    picking_id = fields.Many2one ('stock.picking')
    move_id = fields.Many2one('stock.move')
    location_id = fields.Many2one('stock.location')
    location_dest_id = fields.Many2one('stock.location')
    deposit_id = fields.Many2one('deposit')
    qty = fields.Float('Qty')
    lot_id = fields.Many2one('stock.production.lot')
    registry_line_id = fields.Many2one('weight.registry.line')
    used = fields.Boolean('Used')
    registry_line_id_qty = fields.Float('Weigth qty')
    registry_line_id_qty_flow = fields.Float('Flow qty')
    full_empty = fields.Boolean('Vaciado completo', help="Vacia toda la cantidad de la ubicación origen ", default=False)


    @api.onchange('location_id')
    def onchange_location_id(self):

        domain = [('product_id', '=', self.move_id.product_id.id), ('location_id', 'child_of', self.location_id.id)]
        quants = self.env['stock.quant'].search(domain)
        lot_id = quants.mapped('lot_id')

        if len(lot_id)==1 and lot_id:
            self.lot_id = lot_id
            if self.wzd_id.full_empty:
                self.qty = sum(quant.quantity for quant in quants)
            if not lot_id:
                return
        return {'domain': {
            'lot_id': [
                ('id', 'in', lot_id.ids)]}}


class StockPickwightControlWzd(models.TransientModel):

    _name = 'stock.picking.weight.control.wzd'
    _description = 'Asistente para empaquetar'

    state = fields.Selection(selection=[('not_check_out','Parcial'), ('picks', 'Albaranes'), ('lots', 'Lotes'), ('moves', 'Movimientos')], string='Estado', default='picks')
    type = fields.Selection(selection=REGISTRY_TYPE, string='Type', default='none')
    registry_id = fields.Many2one('weight.registry')
    product_id = fields.Many2one('product.product')
    #registry_line_ids = fields.Many2many('weight.registry.line')
    registry_line_ids = fields.One2many(related="registry_id.used_line_ids")

    product = fields.Many2many ('product.product', string="Linked product")#, domain=[('weight_control', '=', True)])
    fill = fields.Boolean('Fill')
    net = fields.Integer('Net weight')
    select_qty = fields.Selection(selection=[('none', 'None'), ('weight', 'From weight'), ('flowmeter', 'From flowmeter')], string="Qty from ...", default='weight')
    location_id = fields.Many2one('stock.location', string="Source location")
    location_dest_id = fields.Many2one('stock.location', string="Destination location")

    select_pick = fields.Boolean()
    available_pickings = fields.One2many('available.line.picks.wzd', 'wzd_id', string="Available pickings")
    available_moves = fields.One2many('available.line.moves.wzd', 'wzd_id', string="Available lines")
    picking_id = fields.Many2one('stock.picking')
    lot_ids = fields.Many2many('stock.production.lot')
    full_empty = fields.Boolean('Vaciado completo', help="Vacia toda la cantidad de las ubicaciones origen por defecto", default=False)

    unique_lot_id = fields.Many2one('stock.production.lot', 'Lote único')
    unique_location_id = fields.Many2one('stock.location', 'Ubicación origen')
    unique_location_dest_id = fields.Many2one('stock.location', 'Ubicación destino')

    @api.onchange('unique_location_id')
    def onchange_location_id(self):
        if self.unique_location_id.product_id != self.product_id:
            raise UserError(_('En el silo  %s no existe stock del producto %s solicitado en este movimiento.') % (self.unique_location_id.name, self.product_id.name))

        self.unique_lot_id = self.unique_location_id.lot_id.id
        total_qty = 0
        for line in self.available_moves.filtered(lambda x: x.used):
            move = line.move_id
            line_need = move.product_uom._compute_quantity(line.qty, move.product_id.uom_id, rounding_method='HALF-UP')
            total_qty = total_qty + line_need
            self.unique_location_id
            # Hacemos que si es menor que q la cantidad (en miles de litros lo marque como vaciado
            # Lo ideal serañ tener la capácidad de los silos y hacerlo por %
            if self.unique_location_id.quantity - total_qty <= 1:
                line.full_empty = True
            else:
                line.full_empty = False


    @api.multi
    def button_back(self):

        if self.state == 'moves':
            self.state = 'lots'

        elif self.state == 'lots':
            self.state = 'picks'
        action = self.get_formview_action()
        action['target'] = 'new'
        return action

    @api.model
    def create_future_lines(self):
        self.available_moves.unlink()
        self.location_id = self.picking_id.location_id
        self.location_dest_id = self.picking_id.location_dest_id
        move_id = self.picking_id.move_lines.filtered(lambda x:x.product_id == self.product_id)
        move_id.ensure_one()
        lot_id = default_location_id = default_dest_location_id = False
        if self.type=='incoming':
            default_location_id = self.location_id.id
            self.unique_location_id = self.location_id
        elif self.type=='outgoing':
            default_dest_location_id = self.location_dest_id.id
            self.unique_location_dest_id = self.location_dest_id

        for line in self.registry_line_ids:

            #PRIMERO LO PASO A LA UNIDAD
            ## qty = line.qty * move_id.product_id.product_tmpl_id.get_weight_factor(move_id.product_uom)
            domain = [('template_id', '=', move_id.product_id.product_tmpl_id.id), ('category_id', '=', move_id.product_id.uom_id.category_id.id)]
            uom_id = self.env['uom.uom'].search(domain, limit=1)
            if not line.move_line_id:
                qty_kgrs = line.qty
                ## CONVIERTO LOS KGRS DE LV A LITROS
                # se cambia la uso de la segunda unidad
                #line_qty está en Kilos y es como debe estar configurada la segunda unidad de stock
                qty_litros = line.qty * (
                    move_id.product_id.stock_secondary_uom_id.factor or 1.0)
                qty_litros = float_round(
                    qty_litros, precision_rounding=move_id.product_id.uom_id.rounding)
                
                # qty_litros = uom_id._compute_quantity(line.qty,
                #                                    move_id.product_id.uom_id,
                #                                    rounding_method='HALF-UP')
                ##CONVIERTO LOS LITROS A MILES DE LITROS
                #qty_mlitros = move_id.product_id.uom_id._compute_quantity(qty_litros, move_id.product_uom)
                ## Propongo Cantidad como

            if line.move_line_id:
                #qty_mlitros = line.move_line_id.registry_line_id_qty_flow
                qty = line.move_line_id.qty_done
                lot_id = line.lot_id
            elif self.select_qty == 'weight' and not line.move_line_id:
                qty = qty_litros

            else:
                qty = 0.0

            val = {'wzd_id': self.id,
                   'product_id': move_id.product_id.id,
                   'move_id': move_id.id,
                   'location_id': default_location_id,
                   'location_dest_id': default_dest_location_id,
                   'deposit_id': line.deposit_id.id,
                   'lot_id': lot_id,
                   'registry_line_id_qty': line.qty,
                   'registry_line_id_qty_flow': qty_litros,
                   'qty': qty,
                   'registry_line_id': line.id,
                   'used': True
                   }
            self.env['available.line.moves.wzd'].create(val)
        return True

    @api.multi
    def action_assign_lots(self):
        self.ensure_one()
        self.create_future_lines()
        self.state = 'moves'
        action = self.get_formview_action()
        action['target'] = 'new'
        return action


    @api.multi
    def action_assign_product(self):

        if self.product_id.tracking != 'none' and self.unique_lot_id == False and (any(not line.lot_id for line in self.available_moves)):
            raise ValidationError ('Tienes movimientos sin lote asignado')
        if self.unique_location_dest_id == False and (any(not line.location_dest_id for line in self.available_moves)):
            raise ValidationError('Tienes movimientos sin destino')
        if self.unique_location_id == False and (any(not line.location_id for line in self.available_moves)):
            raise ValidationError('Tienes movimientos sin origen')

        self.picking_id.move_lines._do_unreserve()
        reserved_availability = {move: move.reserved_availability for move in self.picking_id.move_lines}
        roundings = {move: move.product_id.uom_id.rounding for move in self.picking_id.move_lines}
        assigned_moves = self.env['stock.move']
        partially_available_moves = self.env['stock.move']
        new_move_lines = self.env['stock.move.line']

        total_qty = 0
        for line in self.available_moves.filtered(lambda x: x.used):
            move = line.move_id
            rounding = roundings[move]
            missing_reserved_uom_quantity = move.product_uom_qty - move.reserved_availability
            missing_reserved_quantity = move.product_uom._compute_quantity(missing_reserved_uom_quantity,
                                                                           move.product_id.uom_id,
                                                                           rounding_method='HALF-UP')
            line_need = move.product_uom._compute_quantity(line.qty, move.product_id.uom_id, rounding_method='HALF-UP')
            missing_reserved_quantity = line_need
            ctx = self._context.copy()

            lot_id = self.unique_lot_id or line.lot_id  or False
            location_dest_id = self.unique_location_dest_id and self.unique_location_dest_id.id or line.location_dest_id.id
            location_id = self.unique_location_id and self.unique_location_id.id or line.location_id.id
            if line.registry_line_id.registry_id.registry_type == 'incoming':
                deposit_dest_id = False
                deposit_id = line.deposit_id.id
            else:
                deposit_dest_id = line.deposit_id.id
                deposit_id = False
            from_wc = {
                'lot_id': lot_id.id,
                'emptied': line.full_empty,
                'registry_line_id': line.registry_line_id.id,
                'location_dest_id': location_dest_id,
                'location_id': location_id,
                'qty_done': line_need,
                'registry_line_id_qty': line.registry_line_id_qty,
                'registry_line_id_qty_flow': line.registry_line_id_qty_flow,
                'deposit_dest_id': deposit_dest_id,
                'deposit_id' : deposit_id
            }
            if lot_id:
                from_wc.update(lot_name = lot_id.name)
            ctx.update(from_wc=from_wc)
            if move.location_id.should_bypass_reservation() or move.location_id.weight_control:
                new_move_line = self.env['stock.move.line'].create(move.with_context(ctx)._prepare_move_line_vals(quantity=line_need))
                new_move_lines |= new_move_line
                assigned_moves |= move
                line.write({'move_line_id': new_move_line.id})

            else:
                if move.procure_method == 'make_to_order':
                    continue
                # If we don't need any quantity, consider the move assigned.ssss

                if float_is_zero(line_need, precision_rounding=rounding):
                    assigned_moves |= move
                    continue
                forced_package_id = move.package_level_id.package_id or None
                available_quantity = self.env['stock.quant']._get_available_quantity(move.product_id, move.location_id, line.lot_id or None,
                                                                                     package_id=forced_package_id)
                if available_quantity <= 0:
                    continue

                # taken_quantity = move.with_context(ctx)._update_reserved_quantity(line_need,
                #                                                                 available_quantity,
                #                                                                 line.location_id or self.unique_location_id,
                #                                                                 lot_id=line.lot_id or self.unique_lot_id or None,
                #                                                                 package_id=forced_package_id, strict=False)

                # Simplificado desde _update_reserved_quantity de stockmove
                taken_quantity = min(available_quantity, line_need)
                taken_quantity_move_uom = move.product_id.uom_id._compute_quantity(taken_quantity, move.product_uom, rounding_method='DOWN')
                taken_quantity = move.product_uom._compute_quantity(taken_quantity_move_uom, move.product_id.uom_id, rounding_method='HALF-UP')
                quants = []
                location_id = line.location_id or self.unique_location_id
                try:
                    if not float_is_zero(taken_quantity, precision_rounding=move.product_id.uom_id.rounding):
                        quants = self.env['stock.quant']._update_reserved_quantity(
                            move.product_id, location_id,taken_quantity, lot_id=line.lot_id or self.unique_lot_id or None,
                            package_id=forced_package_id, owner_id=None, strict=False
                        )
                except UserError:
                    taken_quantity = 0

                for reserved_quant, quantity in quants:
                    new_move_line = self.env['stock.move.line'].create(move._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant))

                new_move_line.update({
                    'emptied': line.full_empty,
                    'registry_line_id': line.registry_line_id.id,
                    'qty_done': line_need,
                    'registry_line_id_qty': line.registry_line_id_qty,
                    'registry_line_id_qty_flow': line.registry_line_id_qty_flow,
                    'deposit_dest_id': deposit_dest_id,
                    'deposit_id' : deposit_id
                    })
                new_move_lines |= new_move_line
                if float_is_zero(taken_quantity, precision_rounding=rounding):
                    continue
                if float_compare(line_need, taken_quantity, precision_rounding=rounding) == 0:
                    assigned_moves |= move
                else:
                    partially_available_moves |= move


        if not (assigned_moves + partially_available_moves):
            raise ValidationError (_('No se encontrado stock en la ubicación {} para estos movimientos'.format(self.location_id.name)))

        partially_available_moves.write({'state': 'partially_available'})
        assigned_moves.write({'state': 'assigned'})
        self.picking_id._check_entire_pack()
        if assigned_moves or partially_available_moves:
            self.picking_id.weight_registry_ids = [(6, 0, [self.registry_id.id])]
            action = self.picking_id.get_formview_action()
            return action
        else:
            return self.registry_id.get_formview_action()




