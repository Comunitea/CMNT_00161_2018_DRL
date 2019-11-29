# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class StockLocation(models.Model):

    _inherit = 'stock.location'

    def _prepare_production_vals(self, product, location, qty):
        """
        Valores para la produción que representa una mezcla en el silo
        """
        bom = self.env['mrp.bom']._bom_find(product=product)
        merge_pt = self.env.ref('custom_stock.lot_merge_picking_type')

        return {
            'origin': 'MERGE LOTS',
            'product_id': product.id,
            'product_qty': qty,
            'product_uom_id': product.uom_id.id,
            'location_src_id': self.id,
            'location_dest_id': self.id,
            'bom_id': bom.id,
            'picking_type_id': merge_pt.id,
            # 'date_planned_start': fields.Datetime.to_string(self._get_date_planned(product_id, values)),
            # 'date_planned_finished': values['date_planned'],
            # 'procurement_group_id': False,
            # 'propagate': self.propagate,
            # 'company_id': values['company_id'].id,
            # 'move_dest_ids': values.get('move_dest_ids') and [(4, x.id) for x in values['move_dest_ids']] or False,
        }

    @api.multi
    def create_production_merge(self, merged_product):
        """
        Para cada ubicaciín ver si hay mas de un lote y si es así crear la
        producción de tipo mezcla
        """
        created_productions = self.env['mrp.production']
        for loc in self:

            # Busco Stock
            domain = [('location_id', '=', loc.id)]
            quants = self.env['stock.quant'].read_group(
                domain, fields=[], 
                groupby=[])
            
            if not quants:
                continue

            loc_qty = quants[0]['quantity']

            # Creo producción mezcla
            vals = self._prepare_production_vals(merged_product, loc, loc_qty)
            Production = self.env['mrp.production'].sudo().\
                with_context(merge=True)
            prod = Production.create(vals)
            created_productions += prod

            # Hago la reserva TODO QUIZAS FORZAR?
            prod.action_assign()

            # Creo el nuevo lote
            lot = self.env['stock.production.lot'].create(
                {'product_id': prod.product_id.id})
            
            # Asistente de Producir
            vals = {
                'production_id': prod.id,
                'product_id': prod.product_id.id,
                'product_qty': prod.product_qty,
                'product_uom_id': prod.product_uom_id.id,
                'lot_id': lot.id
            }
            wzd_prod = self.env['mrp.product.produce'].sudo().new(vals)
            wzd_prod._onchange_product_qty()
            wzd_prod.do_produce()

            # Finalizo la producción, este método hace el post_inventory
            # que finaliza los movimientos asociados
            prod.button_mark_done()
   
        return created_productions