# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from .weight_registry import REGISTRY_TYPE


class StockPickingType(models.Model):

    _inherit = "stock.picking.type"

    weight_control = fields.Selection(selection=REGISTRY_TYPE, help="This types may be linked to weight registry", default='none')

