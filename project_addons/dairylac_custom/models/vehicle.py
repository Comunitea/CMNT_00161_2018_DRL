# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

class Vehicle(models.Model):

    _name = "vehicle"

    register = fields.Text('Register')
    vehicle_type = fields.Text("Type of vehicle")
    description = fields.Text("Description")
    letter_code_q = fields.Text("Letter code Q")

    deposit_id = fields.One2many('deposit', 'quantity', string ="Deposit Used")

    total_deposits = fields.Integer(compute='_get_total_deposits', store=False)
    total_quantity = fields.Float(compute='_get_total_quantity', store=False)



    @api.multi
    def _get_total_deposits(self):
        for vh in self:
            for linea in vh.deposit_id:
                vh.total_deposits += linea.quantity
        return


    @api.multi
    def _get_total_quantity(self):
        for vh in self:
            for linea in vh.deposit_id:
                vh.total_quantity += linea.capacity * linea.quantity
        return
