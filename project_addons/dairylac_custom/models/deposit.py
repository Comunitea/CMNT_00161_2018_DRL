# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class Deposit(models.Model):

    _name = "deposit"

    @api.multi
    def name_get(self):
        result = []
        for dep in self:
            result.append((dep.id, '{}: {}'.format(
                dep.vehicle_id and
                dep.vehicle_id.display_name or dep.code, dep.order)))
        return result

    vehicle_id = fields.Many2one('vehicle')
    quantity = fields.Integer(string="Quantity")
    capacity = fields.Float("Capacity")
    code = fields.Char('Code', default='COD')
    order = fields.Integer('Order', default="1")
