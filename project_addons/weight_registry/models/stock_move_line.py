# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class StockMoveLine(models.Model):

    _inherit = "stock.move.line"

    # need_weight_registry = fields.Boolean(
    #     related='picking_id.need_weight_registry')
    # registry_type = fields.Selection(related='picking_id.registry_type')
    registry_line_id = fields.Many2one(
        'weight.registry.line', 'Wheigt Line',
        domain=[('move_line_ids', '=', False), ('used', '=', True)])
    weight_registry_id = fields.Many2one(
        'weight.registry', 'Weight Registry',
        related="registry_line_id.registry_id")

    _sql_constraints = [
        ('weight_registry_line_unique', 'unique(registry_line_id, move_id)',
         _('Cant associate the same weight registry line to diferent move \
             lines'))
    ]

    @api.onchange('registry_line_id')
    def onchange_registry_line(self):
        if self.registry_line_id:
            self.qty_done = self.registry_line_id.qty

