# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields

class Vehicle(models.Model):

    _name = "deposit"

    vehicle_id = fields.Many2one('vehicle')
    quantity = fields.Integer(string ="Quantity")
    capacity = fields.Float("Capacity")
