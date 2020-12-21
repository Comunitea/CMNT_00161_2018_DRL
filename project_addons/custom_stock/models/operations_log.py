# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class OperationsLog(models.Model):

    _name = 'operations.log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed")],
        readonly=True,
        default="draft",
    )
    name = fields.Char(default=lambda r: fields.Date.today())
    #user_id = fields.Many2one('res.users', default=lambda r: r.env.user.id)
    move_ids = fields.One2many('operations.log.move', 'operations_log_id')

    def create_picking(self):
        for move in self.move_ids:
            if not move.registered:
                move.create_picking()
        self.write({'state': 'confirmed'})


class OperationsLogMove(models.Model):
    _name = 'operations.log.move'
    _order = 'date_done'

    task_id = fields.Many2one(
        comodel_name='project.task', string='Task',
        required=False)
    user_id = fields.Many2one('res.users', default=lambda r: r.env.user.id)
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
            ('services', 'Servicios'),
            ('consume', 'Consumos material'),
            ('to_production', 'Salida a Producción'), 
            ('from_production', 'Entrada desde Producción'), 
            ('move', 'Movs. entre silos o tanques'),
            ('scrap', 'Rechazo',)
            ],
        default='to_production',
        required=True
    )
    location_dest_id = fields.Many2one(
        string='Location destination',
        comodel_name='stock.location',
        ondelete='restrict',
        #domain="[('location_type_q', 'in',[1,2])]"
        domain="[('usage', '=', 'internal')]"
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
    lot_id = fields.Many2one(
        string='Lot',
        comodel_name='stock.production.lot',
        domain="[('product_id', '=', product_id)]",
        context="{'default_product_id': product_id}"
    )
    project_id = fields.Many2one(
        string='Proyecto',
        comodel_name='project.project',
        ondelete='restrict',
    )
    
    message = fields.Char(
        string='Message'
    )
    registered = fields.Boolean('Registered', default=False)
    
    uom_id = fields.Many2one(related='product_id.uom_id', readonly=True)
    picking_id = fields.Many2one('stock.picking', 'Picking')
    qc_inspections_ids = fields.One2many(related='picking_id.qc_inspections_ids')
    nbr_inspections = fields.Integer("Number inspections", compute="_compute_inspections")
    price = fields.Float(
        string='Price',
    )

    def _compute_inspections(self):
        for log in self:
            log.nbr_inspections = len(log.qc_inspections_ids)
        

    @api.multi
    @api.constrains('quantity')
    def _check_quantity(self):
        for operation in self:
            if not operation.quantity > 0.0:
                raise ValidationError(
                    _('Quantity of operation must be greater than 0.')
                )


    @api.onchange('move_type')
    def onchange_move_type(self):
        if self.move_type:
            if self.move_type == 'consume':
                return {'domain':{'location_id': [('location_type_q', '=', False) ,('usage', 'in',['internal'])], 'product_id':  [('type', '!=', 'service')]}}
            elif self.move_type == 'services':
                return {'domain':{'product_id': [('type', '=', 'service')]}}
            else:
                return {'domain':{'location_id': [('location_type_q', 'in',[1,2])], 'product_id': [('type', '=', 'product')]}}

    @api.onchange('location_id')
    def onchange_location_id(self):
        if self.location_id:
            if not self.product_id:
                self.product_id = self.location_id.product_id.id
            qty =  self.location_id.quantity
            for move in self.operations_log_id.move_ids.filtered(lambda m: m.product_id==self.product_id and m.location_id==self.location_id):
                if move != self:
                    qty = qty - move.quantity
            self.location_quantity = qty
        else:
            self.location_quantity = 0    
        
    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return False
        if self.move_type and self.move_type == 'consume' and self.product_id.type=='product':
            location_stock = self.env.ref('stock.stock_location_stock')
            quants = self.env['stock.quant']._gather(self.product_id, location_stock)
            if quants:
                self.location_id = quants[0].location_id.id
                self.lot_id = quants[0].lot_id and quants[0].lot_id.id or False
                self.location_quantity = quants[0].quantity
            else:
                res = {}
                res['warning'] = {'title': _('Warning')}
                res['warning']['message'] = _(
                        "No hay stock registrado para cosnsumir el producto:"
                        " %s seleccionado para esta operaction de consumo"
                    ) % (self.product_id.name)
                return res
        if self.move_type == 'services':
            self.price = self.product_id.standard_price
            

    
    @api.onchange('emptied', 'quantity')
    def onchange_emptied(self):
        if self.emptied:
            adjust = self.location_quantity - self.quantity
            self.message = "Se ha marcado como vaciado el tanque de origen.\r\n Se generará un movimiento de ajuste por %f litros" % adjust
        else:
             self.message = ""

    @api.onchange('location_dest_id')
    def onchange_location_dest_id(self):
    
        if self.location_dest_id and \
            self.location_dest_id.location_type_q in [1,2] and \
            self.location_dest_id.product_id and \
            self.location_dest_id.product_id != self.product_id: 
            res = {}
            res['warning'] = {'title': _('Warning')}
            res['warning']['message'] = _(
                    "El product contenido en la ubicación de destino:"
                    "%s : %s no es compatible con el producto de la ubicación "
                    "seleccionada para esta operación."
                ) % (self.location_dest_id.name, self.location_dest_id.product_id.name)
            self.location_dest_id = False
            return res 

    def unlink(self):
        for op in self:
            if op.registered:
                raise ValidationError(
                    _('You can not delete a registered move.')
                )            
    
    
    @api.multi
    def create_picking(self):
        if self.registered:
            return False
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
        elif self.move_type == 'consume':
            vals = {
                'location_id': self.location_id.id,
                'location_dest_id': self.env['ir.model.data'].xmlid_to_res_id("stock.location_production"),
                'picking_type_id': self.env['ir.model.data'].xmlid_to_res_id("custom_stock.consumes_type"),
                'date_done': self.date_done   
            }
            destination_q = False
        elif self.move_type == 'services':
            vals = {
                'location_id': False,
                'location_dest_id': False,
                'picking_type_id': False,
                'date_done': self.date_done   
            }
            destination_q = False
            
        ctx = self.env.context.copy()
        if ctx.get('default_parent_id'):
            del ctx['default_parent_id']
        if self.move_type != 'services':
            
            picking_id = self.env['stock.picking'].with_context(ctx).create(vals)
            

            vals = {
                'location_id': picking_id.location_id.id,
                'location_dest_id': picking_id.location_dest_id.id,
                'product_id': self.product_id.id,
                'product_uom_qty': self.quantity,
                'picking_id': picking_id.id,
                'destination_q': destination_q,
                'operation_log_id': self.id

            }
            move = self.env['stock.move'].new(vals)

            move.onchange_product_id()
            vals = move._convert_to_write(move._cache)
            self.env['stock.move'].with_context(ctx).create(vals)
            picking_id.action_confirm()
            picking_id.action_assign()
            if self.emptied:
                picking_id.move_line_ids.write({'emptied': True})
                
                
            
            pick_to_backorder = self.env['stock.picking']
            pick_to_do = self.env['stock.picking']
            
                # If still in draft => confirm and assign
                
            if picking_id.state != 'assigned':
                raise UserError(_("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            for move in picking_id.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty
                    if self.new_lot_id:
                        move_line.lot_id = self.new_lot_id.id
            picking_id.action_done()
            self.picking_id = picking_id.id
        self.registered = True
        
        if (self.move_type == 'services'):
            price = self.price
            name = "Operacion %s - %s" % (self.move_type, self.product_id.name),
        else:
            price = self.product_id.standard_price
            name = "Operacion %s - %s" % (picking_id.name, self.product_id.name),
            
        if self.project_id:
            self.env['account.analytic.line'].create({
                'project_id': False,
                'name': name,
                'account_id': self.project_id.analytic_account_id.id,
                'product_id': self.product_id.id,
                'unit_amount': -1 *self.quantity,
                'date': self.date_done,
                'product_uom_id': self.product_id.uom_id.id,
                'amount': -1 * price * self.quantity,
                
            })
    
    @api.multi
    def launch_tests_before_move (self):
        picking_id.launch_tests_before_move()
    
    

    @api.multi
    def action_view_qc_inspecions(self):
        
        action = self.env.ref('quality_control.action_qc_inspection').read()[0]

        inspections= self.qc_inspections_ids
        if len(inspections) > 1:
            action['domain'] = [('id', 'in', inspections.ids)]
        elif inspections:
            form_view = [(self.env.ref('quality_control.qc_inspection_form_view').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = inspections.id
        return action

class StockMove(models.Model):
    _inherit = 'stock.move'

    operation_log_id = fields.Many2one('operations.log.move', 'Operation')

    def _update_reserved_quantity(self, need, available_quantity,
                                  location_id, lot_id=None,
                                  package_id=None, owner_id=None,
                                  strict=True):
        if self.operation_log_id.lot_id:
            lot_id = self.operation_log_id.lot_id
        return super()._update_reserved_quantity(
            need, available_quantity, location_id, lot_id=lot_id,
            package_id=package_id, owner_id=owner_id, strict=strict)

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super()._prepare_move_line_vals(
            quantity=quantity, reserved_quant=reserved_quant)
        lot = False
        if self.operation_log_id.lot_id:
            lot = self.operation_log_id.lot_id
        if reserved_quant and lot:
            vals['lot_id'] = lot.id
        return vals