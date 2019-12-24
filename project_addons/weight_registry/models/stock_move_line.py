# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round, float_compare, float_is_zero

class StockMoveLine(models.Model):

    _inherit = "stock.move.line"

    # need_weight_registry = fields.Boolean(
    #     related='picking_id.need_weight_registry')
    # registry_type = fields.Selection(related='picking_id.registry_type')
    registry_line_id = fields.Many2one(
        'weight.registry.line', 'Weight Line',
        domain=[('move_line_ids', '=', False), ('used', '=', True)])
    weight_registry_id = fields.Many2one(
        'weight.registry', 'Weight Registry',
        related="registry_line_id.registry_id")

    deposit_id = fields.Many2one('deposit', string="Source deposit")
    deposit_dest_id = fields.Many2one('deposit', string="Destiantion deposit")

    # _sql_constraints = [
    #     ('weight_registry_line_unique', 'unique(registry_line_id, move_id)',
    #      _('Cant associate the same weight registry line to diferent move \
    #          lines'))
    # ]

    @api.onchange('registry_line_id')
    def onchange_registry_line(self):
        if self.registry_line_id:
            self.qty_done = self.registry_line_id.qty


    def _action_done(self):

        for ml in self:
            # Check here if `ml.qty_done` respects the rounding of `ml.product_uom_id`.
            uom_qty = float_round(ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='HALF-UP')
            precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            qty_done = float_round(ml.qty_done, precision_digits=precision_digits, rounding_method='HALF-UP')
            if float_compare(uom_qty, qty_done, precision_digits=precision_digits) == 0:

                qty_done_float_compared = float_compare(ml.qty_done, 0, precision_rounding=ml.product_uom_id.rounding)
                if qty_done_float_compared > 0:
                    if ml.product_id.tracking != 'none':
                        picking_type_id = ml.move_id.picking_type_id
                        if picking_type_id:
                            if picking_type_id.use_create_lots:
                                # If a picking type is linked, we may have to create a production lot on
                                # the fly before assigning it to the move line if the user checked both
                                # `use_create_lots` and `use_existing_lots`.
                                if ml.lot_name and not ml.lot_id:
                                    ## Hago lo mismo, pero creo el lote y lo asigno antes para después no falle en caso del mismo lote para vaios moviemitnos

                                    lot_domain = [('product_id', '=', ml.product_id.id), ('name', '=', ml.lot_name)]
                                    lot = self.env['stock.production.lot'].search(lot_domain, limit=1)
                                    if lot:
                                        ml.write({'lot_id': lot.id})
                                    else:
                                        lot = self.env['stock.production.lot'].create(
                                            {'name': ml.lot_name, 'product_id': ml.product_id.id}
                                        )
                                    ml.write({'lot_id': lot.id})



class StockMove(models.Model):

    _inherit = "stock.move"

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """Auto-assign as done the quantity proposed for the lots"""

        res = super(StockMove, self)._prepare_move_line_vals(
            quantity, reserved_quant,
        )
        if self._context.get('from_wc', False):
            res.update(self._context.get('from_wc'))
        return res