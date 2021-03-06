# -*- coding: utf-8 -*-
# © 2019 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.addons.weight_registry.models.weight_registry import REGISTRY_TYPE
from odoo.tools.float_utils import float_compare, float_round, float_is_zero


class WeightPickLinkLineWzd(models.TransientModel):
    _name = 'weight.pick.link.line.wzd'

    wzd_id = fields.Many2one('weight.pick.link.wzd')
    weight_registry_id = fields.Many2one('weight.registry', string="Pesada")
    state = fields.Selection(related="weight_registry_id.state")
    picking_id = fields.Many2one(related="weight_registry_id.picking_id")

    def action_link_picking_id(self):
        picking_id = self.wzd_id.picking_id
        picking_id.weight_registry_id = self.weight_registry_id



class WeightPickLinkWzd(models.TransientModel):
    _name = 'weight.pick.link.wzd'

    picking_id = fields.Many2one('stock.picking', 'Albarán' )
    weight_registry_ids = fields.One2many('weight.pick.link.line.wzd', 'wzd_id', string='Pesadas disponibles', domain=[('picking_id', '=', False)])
