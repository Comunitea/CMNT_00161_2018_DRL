# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class StockProductionLot(models.Model):

    _inherit = 'stock.production.lot'

    def _prepare_production_vals(self, product_qualify, qty, location, location_dest):
        """
        Valores para la produción que representa uan calificación de producto
        """
        bom = self.env['mrp.bom']._bom_find(product=product_qualify)
        qualify_pt = self.env.ref('custom_stock.lot_qualify_picking_type')

        return {
            'origin': 'QUALIFY PRODUCT',
            'product_id': product_qualify.id,
            'product_qty': qty,
            'product_uom_id': product_qualify.uom_id.id,
            'location_src_id': location.id,
            'location_dest_id': location_dest.id,
            'bom_id': bom.id,
            'picking_type_id': qualify_pt.id,
            # 'date_planned_start': fields.Datetime.to_string(self._get_date_planned(product_id, values)),
            # 'date_planned_finished': values['date_planned'],
            # 'procurement_group_id': False,
            # 'propagate': self.propagate,
            # 'company_id': values['company_id'].id,
            # 'move_dest_ids': values.get('move_dest_ids') and [(4, x.id) for x in values['move_dest_ids']] or False,
        }

    @api.multi
    def create_production_qualify(self, product_qualify, location_dest) :
        """
        Para cada lote ver si hay mas de un lote y si es así crear la
        producción de tipo mezcla
        """
        created_productions = self.env['mrp.production']
        for lot in self:

            # Busco Stock
            domain = [('lot_id', '=', lot.id), ('quantity', '>', 0)]
            quants = self.env['stock.quant'].read_group(
                domain, fields=['location_id', 'quantity'], 
                groupby=['location_id'])
            
            if not quants:
                continue

            lot_qty = quants[0]['quantity']
            lot_location = quants[0]['location_id']
            lot_location_id = self.env['stock.production.lot'].browse(lot_location[0])
            # Creo producción califiación
            vals = self._prepare_production_vals(product_qualify, lot_qty, lot_location_id, location_dest)
            Production = self.env['mrp.production'].sudo()
            prod = Production.create(vals)
            created_productions += prod

            # Hago la reserva TODO QUIZAS FORZAR?
            prod.action_assign()

            # Creo el nuevo lote
            lot = self.env['stock.production.lot'].create(
                {'product_id': prod.product_id.id,
                 'name': lot.name})
            
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