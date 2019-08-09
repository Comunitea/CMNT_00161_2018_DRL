# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StockMove(models.Model):

    _inherit = "stock.move"

    weight_registry_id = fields.Many2one('weight.registry', 'Registro de pesada')
    need_weight_registry = fields.Boolean(related='picking_id.need_weight_registry')
    registry_type = fields.Selection(related='picking_id.registry_type')

    def _action_done(self):
        if self.filtered(lambda x: x.picking_type_id.need_weight_registry and not x.weight_registry_id and not x.weight_registry_id.check_out):
            raise ValidationError(_('You have moves with weight_registry_id not set or without check out'))
        return super()._action_done()

    def action_show_details(self):
        res = super().action_show_details()
        if self.registry_type == 'incoming':
            res['context']['show_source_location'] = self.location_id.child_ids or self.need_weight_registry
        if self.registry_type == 'outgoing':
            res['context']['show_destination_location'] = self.location_dest_id.child_ids or self.need_weight_registry
        if self.need_weight_registry:
            res['context']['need_weight_registry'] = self.need_weight_registry
        return res

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super()._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        vals.update({'weight_registry_id': self._context.get('weight_registry_id', False)})
                     # 'deposit_id': self._context.get('deposit_id', False)})
        #if self._context.get('location_field', False):
        #    vals.update({self._context['location_field']: self._context.get('location')})
        print (vals)
        return vals


class StockMoveLine(models.Model):

    _inherit = "stock.move.line"

    weight_registry_id = fields.Many2one('weight.registry', 'Registro de pesada')
    need_weight_registry = fields.Boolean(related='picking_id.need_weight_registry')
    registry_type = fields.Selection(related='picking_id.registry_type')
    # deposit_id = fields.Many2one('deposit', 'Src deposit')
    # deposit_dest_id = fields.Many2one('deposit', 'Dest deposit')


