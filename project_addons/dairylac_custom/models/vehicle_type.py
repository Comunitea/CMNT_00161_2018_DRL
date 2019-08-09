# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, fields


class VehicleType(models.Model):

    _name = "vehicle.type"

    name = fields.Char('Name')
    code = fields.Char('Code')
