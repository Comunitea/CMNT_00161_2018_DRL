# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _,fields, models,api


class QualifyLot(models.TransientModel):
    _name = 'qualify.lot'

    lot_id = fields.Many2one(
        string='Lot origin',
        comodel_name='stock.production.lot',
        ondelete='restrict',
        default=lambda self:self._context.get('active_id'),
        readonly=True
    )
    product_id = fields.Many2one(
        string='Product Qualified',
        comodel_name='product.product',
    )

    date_done = fields.Datetime(
        string='Date done',
        default=fields.Datetime.now,
    )
    quantity = fields.Float(
        string='Quantity',
        related='lot_id.product_qty'
    )
    
    location_dest_id = fields.Many2one(
        string='Location destination',
        comodel_name='stock.location',
        ondelete='restrict',
    )
    

    def qualify_product(self):
        prod_id =self.lot_id.create_production_qualify(self.product_id, self.location_dest_id)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'res_id': prod_id.id,
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('mrp.mrp_production_form_view').id,
            'target': 'current',
        }
