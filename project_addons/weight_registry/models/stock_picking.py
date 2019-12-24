# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from .weight_registry import REGISTRY_TYPE


class StockPicking(models.Model):

    _inherit = "stock.picking"

    picking_ids = fields.Many2many('stock.picking', "pick_weight_rel", column1="picking_id", column2="weight_id",
                                   string="Albaranes asociados")
    weight_registry_ids = fields.Many2many('weight.registry',  "pick_weight_rel", column2="picking_id", column1="weight_id",string="Linked weight registry")
    weight_control = fields.Selection(related='picking_type_id.weight_control', store=True)