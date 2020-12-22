# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class DeliveryCarrier(models.Model):

    _inherit = 'delivery.carrier'

    carrier_code = fields.Char('Carrier Code')

    vehicle_ids = fields.Many2many('vehicle', string="Listado de matrículas", required=False, copy=False)
    driver_ids = fields.Many2many(
        "res.partner", string="Drivers", domain=[("driver", "=", True)]
    )