# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):

    _inherit = 'mrp.production'

    orig_picking_id = fields.Many2one('stock.picking', 'Mixed From')

    def _get_merge_raw_vals(self):
        """
        Devuelve los valores para generar un movimiento de consumo,
        el cual tendrá como cantidad toda la de la producción que es todo lo
        que tenía que mover
        """
        return {
            'name': self.name,
            'date': self.date_planned_start,
            'date_expected': self.date_planned_start,
            'picking_type_id': self.picking_type_id.id,
            'product_id': self.product_id.id,
            'product_uom_qty': self.product_qty,
            'product_uom': self.product_uom_id.id,
            'location_id': self.location_src_id.id,
            'location_dest_id': self.product_id.property_stock_production.id,
            'raw_material_production_id': self.id,
            'company_id': self.company_id.id,
            'price_unit': self.product_id.standard_price,
            'procure_method': 'make_to_stock',
            'origin': self.name,
            'unit_factor': 1,
            # 'bom_line_id': bom_line.id,
            # 'sequence': bom_line.sequence,
            # 'propagate': self.propagate,
            # 'group_id': self.procurement_group_id.id,
            # 'warehouse_id': source_location.get_warehouse().id,
            # 'operation_id': bom_line.operation_id.id or alt_op,
        }
    
    # def _generate_finished_moves(self):
    #     res = super()._generate_finished_moves()
    #     if self._context.get('merge'):
    #         res.update(location_dest_id=self.location_id)

    @api.multi
    def _generate_moves(self):
        """
        Si la producción es creada desde mezcla crea los movimientos de consumo
        fijandose en todo lo que hay en el silo
        """
        if self._context.get('merge'):
            for prod in self:
                prod._generate_finished_moves()
                vals = self._get_merge_raw_vals()
                self.env['stock.move'].create(vals)

                # Check for all draft moves whether they are mto or not
                prod._adjust_procure_method()
                prod.move_raw_ids._action_confirm(32)
                return
        return super()._generate_moves()