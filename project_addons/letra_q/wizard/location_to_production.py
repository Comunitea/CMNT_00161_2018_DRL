# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _,fields, models,api


class LocationToProduction(models.TransientModel):
    _name = 'location.to.production'

    location_id = fields.Many2one(
        string='Location origin',
        comodel_name='stock.location',
        ondelete='restrict',
        default=lambda self:self._context.get('active_id')
    )
    product_id = fields.Many2one(
        string='Product',
        comodel_name='product.product',
        related='location_id.product_id'
    )
    date_done = fields.Datetime(
        string='Date done',
        default=fields.Datetime.now,
    )
    quantity = fields.Float(
        string='Quantity',
    )
    destination_q = fields.Selection(
        [('1', 'Leche concentrada'),
         ('2', 'Leche en polvo'),
         ('3', 'Leche fermentada'),
         ('4', 'Leche líquida'),
         ('5', 'Leches infantiles'),
         ('6', 'Natas y mantequillas'),
         ('7', 'Preparados lácteos'),
         ('8', 'Queso, cuajada y requesón'),
         ('9', 'Combustible'),
         ('10', 'Esparcimineto en tierra'),
         ('11', 'Fábrica de alimento de animales de compañía'),
         ('12', 'Fabricación de abonos y enmiendas del suelo'),
         ('13', 'Planta de biogás'),
         ('14', 'Planta de compostaje'),
         ('15', 'Planta de transformación de subproductos'),
         ('16', 'Planta incineradora/coinciniradora'),],
        'Destination')
    move_type = fields.Selection(
        string='Move Type',
        selection=[
            ('production', 'Production'), 
            ('move', 'Silo o Tanque')
            ],
        default='production',
        required=True
    )
    location_dest_id = fields.Many2one(
        string='Location destination',
        comodel_name='stock.location',
        ondelete='restrict',
        domain="[('location_type_q', 'in',[1,2])]"
    )
    
    emptied = fields.Boolean(
        string='Emptied'
    )
    location_quantity = fields.Float(
        string='Quantity',
        related='location_id.quantity'
    )
    message = fields.Char(
        string='Message'
    )   


    @api.onchange('location_id')
    def onchange_location_id(self):
    
        self.product_id = self.location_id.product_id.id
    
    @api.onchange('emptied', 'quantity')
    def onchange_emptied(self):
        if self.emptied:
            adjust = self.location_quantity - self.quantity
            self.message = "Se ha marcado como vaciado el tanque de origen.\r\n Se generará un movimiento de ajuste por %f miles de litros" % adjust
        else:
             self.message = ""

    @api.onchange('location_dest_id')
    def onchange_location_dest_id(self):
    
        if self.location_dest_id and self.location_dest_id.product_id and self.location_dest_id.product_id != self.product_id:
            self.location_dest_id = False
            res = {}
            res['warning'] = {'title': _('Warning')}
            res['warning']['message'] = _(
                    "El product conternido en la ubicación de destino:"
                    "%s : %s no es compatible con el producto de la ubicación "
                    "seleccionada como origen."
                ) % (self.location_dest_id.name, self.location_dest_id.product_id.name)
            return res 


    
    def create_picking(self):
        if self.move_type == 'production':
            vals = {
                'location_id': self.location_id.id,
                'location_dest_id': self.env['ir.model.data'].xmlid_to_res_id("stock.location_production"),
                'picking_type_id': self.env['ir.model.data'].xmlid_to_res_id("letra_q.send_to_production_type"),
                'scheduled_date': self.date_done   
            }
        elif self.move_type == 'move':
             vals = {
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'picking_type_id': self.env['ir.model.data'].xmlid_to_res_id("stock.picking_type_internal"),
                'scheduled_date': self.date_done   
            }
        
        picking_id = self.env['stock.picking'].create(vals)
        vals = {
            'location_id': self.location_id.id,
            'location_dest_id': picking_id.location_dest_id.id,
            'product_id': self.product_id.id,
            'product_uom_qty': self.quantity,
            'picking_id': picking_id.id,
            'destination_q': self.destination_q,

        }
        move = self.env['stock.move'].new(vals)

        move.onchange_product_id()
        vals = move._convert_to_write(move._cache)
        self.env['stock.move'].create(vals)
        picking_id.action_confirm()
        picking_id.action_assign()
        if self.emptied:
            picking_id.move_line_ids.write({'emptied': True})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'res_id': picking_id.id,
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('stock.view_picking_form').id,
            'target': 'current',
        }
