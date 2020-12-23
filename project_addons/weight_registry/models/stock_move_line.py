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
    registry_line_id_qty = fields.Float('Weigth qty')
    registry_line_id_qty_flow = fields.Float('Flow qty')


    # _sql_constraints = [
    #     ('weight_registry_line_unique', 'unique(registry_line_id, move_id)',
    #      _('Cant associate the same weight registry line to diferent move \
    #          lines'))
    # ]

    @api.onchange('registry_line_id')
    def onchange_registry_line(self):
        if self.registry_line_id:
            self.registry_line_id_qty_flow = self.registry_line_id.qty_flowmeter
            self.registry_line_id_qty = self.registry_line_id.qty




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
            if ml.emptied:
                ml.location_id.empty()
        res =  super(StockMoveLine, self)._action_done()
            
        return res

    @api.multi
    def _compute_secondary_unit_qty_available(self):
        for line in self.filtered('secondary_uom_id'):
            if line.qty_done:
                qty = line.qty_done
            else:
                qty = line.product_uom_qty
            qty = qty / (
                line.secondary_uom_id.factor or 1.0)
            line.secundary_uom_qty = float_round(
                qty, precision_rounding=line.uom_id.rounding)

class StockMove(models.Model):

    _inherit = "stock.move"

    @api.multi
    def default_control_uom_id(self):
        self.write({'weight_control_uom_id': self.env["ir.config_parameter"].sudo().get_param("weight_registry.weight_control_default_uom_id"),
                    'flow_control_uom_id': self.env["ir.config_parameter"].sudo().get_param("weight_registry.flow_control_default_uom_id")})
        return True

    @api.multi
    def _compute_secondary_unit_qty_available(self):
        for line in self.filtered('secondary_uom_id'):
            if line.product_id.weight_control and line.move_line_ids and line.move_line_ids[0].weight_registry_id:
                line.secondary_uom_qty = line.move_line_ids[0].weight_registry_id.net
            else:
                line.secondary_uom_qty = sum(x.secondary_uom_qty for x in line.move_line_ids)

    registry_line_id_qty = fields.Float('Weigth qty', compute="compute_wc_qties")
    registry_line_id_qty_flow = fields.Float('Flow qty', compute="compute_wc_qties")
    weight_control = fields.Selection(related='picking_type_id.weight_control')
    weight_control_uom_id = fields.Many2one('uom.uom', default=lambda self: self.default_control_uom_id())
    flow_control_uom_id = fields.Many2one('uom.uom', default=lambda self: self.default_control_uom_id())
    secondary_uom_qty = fields.Float(compute="_compute_secondary_unit_qty_available")
    weight_registry_id = fields.Many2one('weight.registry', 'Weight Registry')
    @api.multi
    def compute_wc_qties(self):
        for move in self:
            move.registry_line_id_qty = sum(x.registry_line_id_qty for x in move.move_line_ids)
            move.registry_line_id_qty_flow = sum(x.registry_line_id_qty_flow for x in move.move_line_ids)


    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """Auto-assign as done the quantity proposed for the lots"""

        res = super(StockMove, self)._prepare_move_line_vals(
            quantity, reserved_quant,
        )
        if self._context.get('from_wc', False):
            res.update(self._context.get('from_wc'))
        return res

    def _action_done(self):
        for move in self:
            if move.picking_type_id.weight_control != 'none' and any(x.registry_line_id == False for x in move.move_line_ids):
                    raise ValidationError (_('You need to check the assigned weight control for this move'))
        return super()._action_done()
