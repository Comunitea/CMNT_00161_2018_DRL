# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api,fields, models
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
    @api.depends('location_id', 'location_dest_id', 'product_id')
    def _is_letra_Q(self):
        for move in self:
            if move.product_id.subject_q:
                if move.location_id.location_type_q and \
                        move.location_dest_id.location_type_q:
                    move.is_letra_q = True
            else:
                move.is_letra_q = False

    emptied = fields.Boolean('Emptied')
    is_letra_q = fields.Boolean("Letra Q Move", compute="_is_letra_Q",
                                store=True)


class StockMoveLine(models.Model):

    _inherit = 'stock.move.line'
    @api.depends('location_id', 'location_dest_id', 'product_id')
    def _is_letra_Q(self):
        for move in self:
            if move.product_id.subject_q:
                if move.location_id.location_type_q and \
                        move.location_dest_id.location_type_q:
                    move.is_letra_q = True
            else:
                move.is_letra_q = False

    emptied = fields.Boolean('Emptied')
    is_letra_q = fields.Boolean("Letra Q Move", compute="_is_letra_Q",
                                store=True)
