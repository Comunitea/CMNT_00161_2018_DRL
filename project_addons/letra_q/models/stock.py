# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models
import odoo.addons.decimal_precision as dp


class StockLocation(models.Model):

    _inherit = 'stock.location'

    location_type_q = fields.Selection(
        [('1', 'tanque'),
         ('2', 'silo'),
         ('3', 'cisterna'),
         ('4', 'línea de Producción'),
         ('5', 'agente no nacional'),
         ('6', 'rechazo'),
         ('7', 'intermediario'),
         ('8', 'agente nacional')],
         'Type of Location', required=False)
    code_q = fields.Char(string='Código Letra Q')



class StockMove(models.Model):

    _inherit = 'stock.move'

    emptied = fields.Boolean('Emptied')