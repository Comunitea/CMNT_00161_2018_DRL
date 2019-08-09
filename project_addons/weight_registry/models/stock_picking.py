# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, fields
from .weight_control import REGISTRY_TYPE


class StockPickingType(models.Model):

    _inherit = "stock.picking.type"

    need_weight_registry = fields.Boolean(
        "Weight registry", help="If check, need weight to do an action done")
    registry_type = fields.Selection(REGISTRY_TYPE, string="Registy type")


class StockPicking(models.Model):

    _inherit = "stock.picking"

    need_weight_registry = fields.Boolean(
        related='picking_type_id.need_weight_registry')
    weight_registry_ids = fields.One2many('weight.registry', 'picking_id')
    registry_type = fields.Selection(related='picking_type_id.registry_type')
    weight_control_state = fields.Selection(
        string="Weight state", compute='_compute_weight_state',
        selection=[('checked_out', "Check out"), ('checked_in', "Check in")])
    weight_registry_count = fields.Integer(
        string="W. registry count", compute="_get_w_registry_count")

    def _get_w_registry_count(self):
        for pick in self:
            pick.weight_registry_count = len(pick.weight_registry_ids)

    #@api.depends('weight_registry_ids.check_in', 'weight_registry_ids.check_out', 'weight_registry_ids')
    def _compute_weight_state(self):
        for w_r_id in self:
            if all(w_r.check_out for w_r in w_r_id.weight_registry_ids):
                w_r_id.weight_control_state = 'checked_out'
            else:
                w_r_id.weight_control_state = 'checked_in'

    def button_weight_to_pick_wzd(self):
        self.ensure_one()
        action = self.env.ref(
            'weight_registry.act_view_weight_pick_wzd').read()[0]

        wzd_id = self.env['weight.pick.wzd'].create_from_pick(self)
        action['res_id'] = wzd_id.id
        return action
