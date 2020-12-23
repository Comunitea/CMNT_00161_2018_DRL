# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

class ProductSecondaryUnit(models.Model):
    _inherit = 'product.secondary.unit'

    @api.multi
    def name_get(self):
        ##No quiero un nombre tan largo, internamente sigue siendo el mimso valor
        result = []
        for unit in self:
            factor = round(unit.factor, 3)
            result.append((unit.id, "{unit_name}-{factor}".format(
                unit_name=unit.name,
                factor=factor))
            )
        return result