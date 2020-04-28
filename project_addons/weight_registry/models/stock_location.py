# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from .weight_registry import REGISTRY_TYPE


class StockLocation(models.Model):

    _inherit = "stock.location"

    weight_control = fields.Boolean('Requires weight control', help="For filter in weight control links", default=False)

    def empty(self):
        inventory = self.env['stock.inventory'].create(
            {
                'name': 'Ajuste Silo automático',
                'location_id': self.id,
                'filter': 'product',
                'product_id': self.product_id.id,
            }
        )
        inventory.action_start()
        inventory.action_reset_product_qty()
        inventory.action_validate()
        self.product_id = None
        self.lot_id =  None
