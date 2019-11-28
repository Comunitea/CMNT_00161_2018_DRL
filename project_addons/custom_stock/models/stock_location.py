# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class StockLocation(models.Model):

    _inherit = 'stock.location'

    def _prepare_production_vals(self, product, location, qty):
        merge_location = self.env.ref('custom_stock.lot_merge_production')

        return {
            'origin': 'MERGE LOTS',
            'product_id': product.id,
            'product_qty': qty,
            'product_uom_id': product.uom_id.id,
            'location_src_id': self.id,
            'location_dest_id': merge_location.id,
            # 'bom_id': bom.id,
            # 'date_planned_start': fields.Datetime.to_string(self._get_date_planned(product_id, values)),
            # 'date_planned_finished': values['date_planned'],
            # 'procurement_group_id': False,
            # 'propagate': self.propagate,
            # 'picking_type_id': self.picking_type_id.id or values['warehouse_id'].manu_type_id.id,
            # 'company_id': values['company_id'].id,
            # 'move_dest_ids': values.get('move_dest_ids') and [(4, x.id) for x in values['move_dest_ids']] or False,
        }

    @api.multi
    def create_production_merge(self, merged_product):
        # import pdb; pdb.set_trace()
        for loc in self:
            domain = [('location_id', '=', loc.id)]
            quants = self.env['stock.quant'].read_group(
                domain, fields=[], 
                groupby=[])
            
            if not quants:
                continue

            loc_qty = quants[0]['quantity']
            vals = self._prepare_production_vals(merged_product, loc, loc_qty)
            Production = self.env['mrp.production'].sudo()
            Production.create(vals)


        return