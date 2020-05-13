# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _


class OperationsLog(models.Model):

    _name = 'operations.log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed")],
        readonly=True,
        default="draft",
    )
    name = fields.Char(default=lambda r: fields.Date.today())
    user_id = fields.Many2one('res.users', default=lambda r: r.env.user.id)
    move_ids = fields.One2many('operations.log.move', 'operations_log_id')

    def create_picking(self):
        for move in self.move_ids:
            move.create_picking()
        self.write({'state': 'confirmed'})


class OperationsLogMove(models.Model):
    _name = 'operations.log.move'
    _order = 'date_done'

    operations_log_id = fields.Many2one('operations.log')
    location_id = fields.Many2one(
        string='Location origin',
        comodel_name='stock.location',
        ondelete='restrict',
    )
    product_id = fields.Many2one(
        string='Product',
        comodel_name='product.product',
    )
    date_done = fields.Datetime(
        string='Date done',
        default=fields.Datetime.now,
    )
    quantity = fields.Float(
        string='Quantity',
    )
    destination_q_prod = fields.Selection(
        [('1', 'Leche concentrada'),
         ('2', 'Leche en polvo'),
         ('3', 'Leche fermentada'),
         ('4', 'Leche líquida'),
         ('5', 'Leches infantiles'),
         ('6', 'Natas y mantequillas'),
         ('7', 'Preparados lácteos'),
         ('8', 'Queso, cuajada y requesón'),
         ],
        'Destino producción')
    destination_q_scrap = fields.Selection(
        [('10', 'Esparcimiento en tierra'),
        ('9', 'Combustible'),
         ('11', 'Fábrica de alimento de animales de compañía'),
         ('12', 'Fabricación de abonos y enmiendas del suelo'),
         ('13', 'Planta de biogás'),
         ('14', 'Planta de compostaje'),
         ('15', 'Planta de transformación de subproductos'),
         ('16', 'Planta incineradora/coinciniradora'),],
        'Destino rechazo')
    move_type = fields.Selection(
        string='Move Type',
        selection=[
            ('to_production', 'Salida a Production'), 
            ('from_production', 'Entrada desde Production'), 
            ('move', 'Silo o Tanque'),
            ('scrap', 'Rechazo',)
            ],
        default='to_production',
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
        string='Location Quantity',
        readonly=True,
        #compute="_compute_location_quantity",
        #related='location_id.quantity'
    )
    new_lot_id = fields.Many2one(
        string='New Lot',
        comodel_name='stock.production.lot',
        domain="[('product_id', '=', product_id)]",
        context="{'default_product_id': product_id}"
    )
    message = fields.Char(
        string='Message'
    )   

    @api.onchange('location_id')
    def onchange_location_id(self):
        if self.location_id:
            self.product_id = self.location_id.product_id.id
            qty =  self.location_id.quantity
            for move in self.operations_log_id.move_ids.filtered(lambda m: m.product_id==self.product_id and m.location_id==self.location_id):
                if move != self:
                    qty = qty - move.quantity
            self.location_quantity = qty
        else:
            self.location_quantity = 0    
        

    
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
            res = {}
            res['warning'] = {'title': _('Warning')}
            res['warning']['message'] = _(
                    "El product conternido en la ubicación de destino:"
                    "%s : %s no es compatible con el producto de la ubicación "
                    "seleccionada para esta operación."
                ) % (self.location_dest_id.name, self.location_dest_id.product_id.name)
            self.location_dest_id = False
            return res 


    
    def create_picking(self):
        if self.move_type == 'to_production':
            vals = {
                'location_id': self.location_id.id,
                'location_dest_id': self.env['ir.model.data'].xmlid_to_res_id("stock.location_production"),
                'picking_type_id': self.env['ir.model.data'].xmlid_to_res_id("custom_stock.send_to_production_type"),
                'date_done': self.date_done   
            }
            destination_q = self.destination_q_prod
        elif self.move_type == 'from_production':
            vals = {
                'location_id': self.env['ir.model.data'].xmlid_to_res_id("stock.location_production"),
                'location_dest_id': self.location_dest_id.id,
                'picking_type_id': self.env['ir.model.data'].xmlid_to_res_id("custom_stock.send_from_production_type"),
                'date_done': self.date_done   
            }
            destination_q = False
        elif self.move_type == 'move':
            vals = {
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'picking_type_id': self.env['ir.model.data'].xmlid_to_res_id("stock.picking_type_internal"),
                'date_done': self.date_done   
            }
            destination_q = False
        elif self.move_type == 'scrap':
            vals = {
                'location_id': self.location_id.id,
                'location_dest_id': self.env['ir.model.data'].xmlid_to_res_id("stock.stock_location_scrapped"),
                'picking_type_id': self.env['ir.model.data'].xmlid_to_res_id("stock.picking_type_internal"),
                'date_done': self.date_done   
            }
            destination_q = self.destination_q_scrap
        picking_id = self.env['stock.picking'].create(vals)

        vals = {
            'location_id': picking_id.location_id.id,
            'location_dest_id': picking_id.location_dest_id.id,
            'product_id': self.product_id.id,
            'product_uom_qty': self.quantity,
            'picking_id': picking_id.id,
            'destination_q': destination_q,

        }
        move = self.env['stock.move'].new(vals)

        move.onchange_product_id()
        vals = move._convert_to_write(move._cache)
        self.env['stock.move'].create(vals)
        picking_id.action_confirm()
        picking_id.action_assign()
        #picking_id.action_done()
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
