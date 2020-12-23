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
    show_details = fields.Boolean('Show_details')

    @api.multi
    def assign_2_weigt(self):
        vehicle_ids_v = []
        deposit_ids = []
        ##miro si hay alguna pesada para este
        weight_registry_id = self.picking_id.weight_registry_id

        vehicle_id = self.picking_id.vehicle_ids.filtered(lambda x: x.master)[0]
        if not vehicle_id:
            raise ValidationError ("No encunetro un vehiculo principal")
        vehicle_ids = self.picking_id.vehicle_ids
        if not vehicle_ids[0].vehicle_type_id.master:
            raise ValidationError(_('First register must be master'))
        for v_id in vehicle_ids:
            vals = {'id': v_id.id, 'register': v_id.register}
            vehicle_ids_v.append(vals)
        for line in self.line_ids:
            v_dep = {'id': line.deposit_id.id, 'check': line.checked}
            deposit_ids.append((v_dep))
        domain = [('vehicle_id', '=', vehicle_id.id), ('check_out', '=', False)]
        reg_id = self.env['weight.registry'].search(domain, limit=1, order="id desc")
        if vehicle_id.weight_registry_state == 'check_out':
            ## Si el vehiculo está fuera, entonces
            ## compruebo el albarán
            if self.picking_id.weight_registry_id:
                raise ValidationError ('No puedes tener un vehiculo fuera y el albarán con registro')
            if self.picking_id.weight_registry_state != 'checked_in':
                raise ValidationError ('Error de estado de pesaje. El estado del vehiculo y del albarán deben coincidir.')
            #Hago la entrada, esto mete el vehiculo y debería cambiarme el estado del albarán
            new_w = self.env['weight.registry'].set_weight_registry(vehicle_id.id, self.weight, deposit_ids,
                                                                        vehicle_ids_v, self.picking_id)
            #self.picking_id.weight_registry_id = reg_id

            return

        new_w = self.env['weight.registry'].set_weight_registry(vehicle_id.id, self.weight, deposit_ids, vehicle_ids_v, self.picking_id)
        #new_w = self.env['weight.registry'].set_weight_registry(vehicle_id.id, weight, deposit_ids, vehicle_ids)
        if new_w:
            self.picking_id.weight_registry_id = new_w
            if new_w.check_out:
                return self.picking_id.link_and_fill_from_weight_wzd()
        # self.picking_id.link_and_fill_from_weight_wzd()
