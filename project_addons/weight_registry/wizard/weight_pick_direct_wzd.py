# -*- coding: utf-8 -*-
# © 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.addons.weight_registry.models.weight_registry import REGISTRY_TYPE
from odoo.tools.float_utils import float_compare, float_round, float_is_zero


class WeightPickLinkLineWzd(models.TransientModel):
    _name = 'weight.pick.direct.line.wzd'

    wzd_id = fields.Many2one('weight.pick.direct.wzd')
    deposit_id = fields.Many2one('deposit', 'Deposit')
    vehicle_id = fields.Many2one('vehicle', 'Vehículo')
    checked = fields.Boolean('Checked')
    capacity = fields.Float("Capacity")
    code = fields.Char("Code", default="COD")

class WeightPickLinkWzd(models.TransientModel):
    _name = 'weight.pick.direct.wzd'

    picking_id = fields.Many2one('stock.picking', 'Albarán' )
    vehicle_id = fields.Many2one('vehicle', 'Vehículo')
    weight = fields.Float('Peso')
    line_ids = fields.One2many('weight.pick.direct.line.wzd', 'wzd_id', string='Depositos',)

    @api.multi
    def assign_2_weigt(self):
        vehicle_ids_v = []
        deposit_ids = []
        vehicle_id = self.picking_id.vehicle_ids[0]
        vehicle_ids = self.picking_id.vehicle_ids
        if not vehicle_ids[0].vehicle_type_id.master:
            raise ValidationError(_('First register must be master'))
        for v_id in vehicle_ids:
            vals = {'id': v_id.id, 'register': v_id.register}
            vehicle_ids_v.append(vals)
        for line in self.line_ids:
            v_dep = {'id': line.deposit_id.id, 'check': line.checked}
            deposit_ids.append((v_dep))
        new_w = self.env['weight.registry'].set_weight_registry(vehicle_id.id, self.weight, deposit_ids, vehicle_ids_v)
        #new_w = self.env['weight.registry'].set_weight_registry(vehicle_id.id, weight, deposit_ids, vehicle_ids)
        if new_w:
            self.picking_id.write({'weight_registry_ids': [(4, new_w.id)]})

        if new_w.check_out_weight:
            return self.picking_id.link_and_fill_from_weight_wzd()
        # self.picking_id.link_and_fill_from_weight_wzd()
