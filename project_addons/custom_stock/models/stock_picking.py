# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.multi
    def compute_first_product_id(self):
        for pick in self:
            move = pick.move_lines
            if move:
                pick.first_product_id = move[0].product_id

    operator_id = fields.Many2one("delivery.carrier", string="Operator")
    driver_id = fields.Many2one("res.partner", string="Driver", domain="[('id', 'in', available_driver_ids)]")
    available_driver_ids = fields.Many2many(related='carrier_id.driver_ids')
    first_product_id = fields.Many2one('product.product', 'Product', compute="compute_first_product_id")

    @api.onchange('operator_id')
    def onchange_operator_id(self):
        self.carrier_id = self.operator_id

    @api.multi
    def action_done(self):
        """
        Buscar las ubicaciones que necesitan mezclarse (las que son silo
        y tienen mas de un lote en ella), y para cada una de estas ubicacines
        crear la produción que hará la mezcla
        """
        res = super().action_done()
        for pick in self:
            locs2merge = pick.get_merge_locations()
            if locs2merge:
                # TODO ESTO QUIZÁ NO HACE FALTA Y SIEMPRE SE COGE EL ÚNICO
                # PRODUCTO DEL SILO
                merged_product = pick._get_merged_product()
                prods = locs2merge.create_production_merge(merged_product)
                prods.write({'orig_picking_id': self.id})
        return res
    
    @api.multi
    def _get_merged_product(self):
        """
        Devuelve de un albarán el producto adecuado como resultado de la mezcla
        """
        self.ensure_one()
        products = self.move_line_ids.mapped('product_id')
        return products[0]
    
    @api.multi
    def get_merge_locations(self):
        """
        Devuelve ubicaciones que son silo y tienen mas de un lote asignado
        """
        self.ensure_one()
        res = self.env['stock.location']
        # Obtener ubicaciones que son silo
        locs =  self.move_line_ids.mapped('location_dest_id').filtered(
            lambda l: l.location_type_q == '2'
        )
        
        for loc in locs:
            domain = [('location_id', '=', loc.id), ('quantity', '>', 0)]
            quants = self.env['stock.quant'].read_group(
                domain, fields=['product_id', 'lot_id'], 
                groupby=['lot_id'])
            if len(quants) > 1:  # Mas de un lote
                res += loc
        return res

