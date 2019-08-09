# -*- coding: utf-8 -*-
# © 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from ..models.weight_control import REGISTRY_TYPE


class WeightPickLineWzd(models.TransientModel):
    _name = 'weight.pick.line.wzd'
    #_order = 'check_in'
    name = fields.Char('Name')
    wzd_id = fields.Many2one('weight.pick.wzd')
    weight_registry_id = fields.Many2one('weight.registry', string="Weight registry")
    fill = fields.Boolean('Fill', readonly=True)
    net = fields.Integer('Net weight', readonly=True)
    check_out_weight = fields.Integer('Check in weight')
    picking_id = fields.Many2one('stock.picking')
    registry_type = fields.Selection(REGISTRY_TYPE, string="Registy type")
    added = fields.Boolean('Selected')
    to_add = fields.Boolean('To add')
    to_unlink = fields.Boolean('To delete')

class WeightPickWzd(models.TransientModel):

    """Create a stock.batch.picking from stock.picking
    """

    _name = 'weight.pick.wzd'
    _description = 'Asistente para añadir registros de pesaje al albarán'

    picking_id = fields.Many2one('stock.picking')
    #move_lines = fields.One2many(related='picking_id.move_lines')
    #move_line_ids = fields.One2many(related='picking_id.move_lines_ids')
    picking_type_id = fields.Many2one(related='picking_id.picking_type_id')
    state = fields.Selection(related='picking_id.state')
    line_ids = fields.Many2many('weight.pick.line.wzd', 'wzd_id')
    old_line_ids = fields.Many2many('weight.pick.line.wzd', 'wzd_id')
    registry_type = fields.Selection(REGISTRY_TYPE, string="Registy type")

    def _prepare_w_lines(self, line):

        vals =  {
            'wzd_id': self.id,
            'name': line.display_name,
            'fill': line.fill,
            'net': line.net,
            'check_out_weight': line.check_out_weight,
            'picking_id': line.picking_id.id,
            'added': True if line.picking_id else False,
            'to_add': True if line.picking_id else False,
            'weight_registry_id': line.id,
            'registry_type': line.registry_type
        }
        print (vals)
        return vals

    def create_from_pick(self, picking_id):
        vals = {'picking_id': picking_id.id,
                'registry_type': picking_id.registry_type}
        wzd_id = self.create(vals)

        w_r_domain = [('registry_type', '=', picking_id.registry_type), '|', ('picking_id', '=', picking_id.id), ('picking_id', '=', False)]
        new_line_ids = self.env['weight.pick.line.wzd']
        w_r_ids = self.env['weight.registry'].search(w_r_domain)

        for w_r in w_r_ids:
            new_line_ids |= self.env['weight.pick.line.wzd'] .create(wzd_id._prepare_w_lines(w_r))

        vals = {
                'line_ids': [(6, 0, new_line_ids.ids)],
                }

        wzd_id.write(vals)

        return wzd_id

    @api.model
    def default_get(self, fields):
        return super().default_get(fields)
        defaults = super().default_get(fields)
        picking = self._context.get('active_id', False)
        picking_id = self.env['stock.picking'].browse(picking)
        defaults['picking_id'] = picking
        defaults['registry_type'] = picking_id.registry_type
        w_r_domain = [('registry_type', '=', picking_id.registry_type), '|', ('picking_id', '=', picking), ('picking_id', '=', False)]

        old_line_ids = self.env['weight.pick.line.wzd']
        new_line_ids = self.env['weight.pick.line.wzd']
        w_r_ids = self.env['weight.registry'].search(w_r_domain)

        for w_r in w_r_ids:
            new_line_ids |= self.env['weight.pick.line.wzd'] .create(self._prepare_w_lines(w_r))
        defaults['line_ids'] = [(6, 0, new_line_ids.ids)]

        for w_r in w_r_ids.filtered(lambda x: x.picking_id):
            old_line_ids |= self.env['weight.pick.line.wzd'] .create(self._prepare_w_lines(w_r))
        defaults['old_line_ids'] = [(6, 0, old_line_ids.ids)]

        print (defaults)
        return defaults


    @api.multi
    def action_apply_changes(self):
        str = ''
        if self.registry_type == 'incoming':
            location_field = 'deposit_id'
            location = self.env.ref('weight_registry.stock_location_incoming_deposit')

        elif self.registry_type == 'outgoing':
            location_field = 'deposit_dest_id'
            location = self.env.ref('weight_registry.stock_location_outgoing_deposit')

        pick = self.picking_id
        if len(pick.move_lines) == 1:
            move = pick.move_lines
        to_unlink = self.line_ids.filtered(lambda x: x.to_unlink).mapped('weight_registry_id')

        if to_unlink:
            to_unlink.mapped('picking_id').do_unreserve()
            vals = {'weight_registry_id': False, 'deposit_id': False}
            domain = [('weight_registry_id', 'in', to_unlink.ids )]
            self.env['stock.move'].search(domain).write(vals)
            self.env['stock.move.line'].search(domain).write(vals)
            to_unlink.write({'picking_id': False})


        for line in self.line_ids.filtered(lambda x: x.to_add):

            w_r = line.weight_registry_id
            vehicle_id = w_r.vehicle_id

            if w_r.product_id:
                move = pick.move_lines.filtered(lambda x: x.product_id == w_r.product_id)
            if len(move) != 1:
                raise ValidationError (_('Unable to map a move in this pick'))

            move.weight_registry_id = w_r
            ctx = self._context.copy()

            for deposit in vehicle_id.deposit_id:
                qty = deposit.capacity
                ctx.update(weight_registry_id=w_r.id, deposit_id=deposit.id, location=location, location_field=location_field)
                move_line_vals = move.with_context(ctx)._prepare_move_line_vals(quantity=qty)
                print (move_line_vals)
                self.env['stock.move.line'].create(move_line_vals)

            w_r.apply_net_to_qty_done()
            str = '{}, {}'.format(str, line.display_name)
            print (str)
            w_r.picking_id = self.picking_id


        # self.move_id.do_unreserve_for_pda()
        # route_vals = self.move_id.update_info_route_vals()
        # moves = self.env['stock.move']
        # for quant in self.quant_ids.filtered(lambda x: x.new_quantity>0.00):
        #     new_move_id = self.move_id._split(quant.new_quantity)
        #     new_move = self.env['stock.move'].browse(new_move_id)
        #     vals = route_vals.copy()
        #     vals.update(location_id=quant.quant_id.location_id.id)
        #     new_move.write(vals)
        #     new_move.check_new_location()
        #     moves |= new_move
        #
        # if self.move_id not in moves:
        #     self.move_id.action_cancel_for_pda()
        #
        # moves._action_assign()
        # return self.env['stock.picking.type'].return_action_show_moves(domain=[('id', 'in', moves.ids)])
        #


