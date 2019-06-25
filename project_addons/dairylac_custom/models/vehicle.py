# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

class Vehicle(models.Model):

    _name = "vehicle"

    @api.multi
    def name_get(self):
        return [(vehicle.id, "{}: {}".format(vehicle.register, vehicle.description)) for vehicle in self]


    register = fields.Char('Register')
    vehicle_type_id = fields.Many2one('vehicle.type', "Type of vehicle")
    description = fields.Char("Description")
    letter_code_q = fields.Char("Letter code Q")
    deposit_id = fields.One2many('deposit', 'vehicle_id', string ="Deposit " \
                                                                     "Used")
    total_deposits = fields.Integer(compute='_get_total_deposits', store=False)
    total_quantity = fields.Float(compute='_get_total_quantity', store=False)
    driver_ids = fields.Many2many('res.partner', string="Drivers", domain=[('driver', '=', True)])


    @api.multi
    def action_view_vh_deposit(self):
        w_reg = self.mapped('deposit_id')
        action = self.env.ref('dairylac_custom.show_deposit_action_vehicle').read()[0]
        action['context'] = {'default_vehicle_id': self.id}
        if len(w_reg) > 1:
            action['domain'] = [('id', 'in', w_reg.ids)]
        elif len(w_reg) == 1:
            action['views'] = [(self.env.ref('dairylac_custom.weight_registry_view_form').id, 'form')]
            action['res_id'] = w_reg.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def _get_total_deposits(self):
        for vh in self:
            vh.deposit_id_count = len(vh.deposit_id)

    @api.multi
    def _get_total_quantity(self):
        for vh in self:
            for linea in vh.deposit_id:
                vh.total_quantity += linea.capacity * linea.quantity

