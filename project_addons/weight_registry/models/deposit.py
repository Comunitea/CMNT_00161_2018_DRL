# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class Deposit(models.Model):

    _inherit = "deposit"

    @api.model
    def get_app_vals(self, qty=0.0):
        dep_val = {

            'id': self.id,
            'code': self.code,
            'number': self.number,
            'capacity': self.capacity,
            'vehicle_id': self.vehicle_id.id,
            'register': self.vehicle_id.register
        }
        return dep_val