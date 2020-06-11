# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, fields, _


class StockPicking(models.Model):

    _inherit = "stock.picking"

    conform = fields.Boolean('Se ajusta', help='Se ajusta a las especificaciones')
    specifications = fields.Char('Especificaciones', help='Ficha de especificaciones')
    not_conform_note = fields.Text('Motivo', help='En caso de que la partida NO se ajuste a las especificaciones, indicar el motivo del incumplimiento')

