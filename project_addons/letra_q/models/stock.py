# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class StockLocation(models.Model):

    _inherit = 'stock.location'

    location_type_q = fields.Selection(
        [('1', 'tanque'),
         ('2', 'silo'),
         ('3', 'cisterna'),
         ('4', 'línea de Producción'),
         ('5', 'agente no nacional'),
         ('6', 'rechazo'),
         ('7', 'intermediario'),
         ('8', 'agente nacional')],
        'Type of Location', required=False)
    code_q = fields.Char(string='Código Letra Q')
    product_id = fields.Many2one(
        string='Product',
        comodel_name='product.product',
        ondelete='restrict',
        compute="_compute_information"
    )
    quantity = fields.Float(
        string='Quantity',
        compute="_compute_information"
    )
    lot_id = fields.Many2one(
        string='Internal lot',
        comodel_name='stock.production.lot',
        ondelete='restrict',
        compute="_compute_information"
    )
    
    def _compute_information(self):
        for location in self:
            if location.location_type_q not in ('1','2','3'):
                location.product_id = False
                location.quantity = 0
                location.lot_id = False
            else:
                quants = self.env['stock.quant'].read_group([('location_id', '=', location.id)], ['product_id', 'lot_id', 'quantity:sum'],  ['product_id', 'lot_id'], lazy=False)
                if quants:
                    location.product_id = quants[0]['product_id'][0]
                    location.quantity = quants[0]['quantity']
                    location.lot_id = quants[0]['lot_id'][0]

class StockMove(models.Model):

    _inherit = 'stock.move'

    @api.depends(
        'location_id.location_type_q',
        'location_dest_id.location_type_q',
        'product_id.subject_q')
    def _compute_is_letra_q(self):
        for move in self:
            if move.product_id.subject_q:
                if move.location_id.location_type_q and \
                        move.location_dest_id.location_type_q:
                    move.is_letra_q = True
            else:
                move.is_letra_q = False

    emptied = fields.Boolean('Emptied')
    is_letra_q = fields.Boolean("Letra Q Move", compute="_compute_is_letra_q",
                                store=True)
    location_type_q = fields.Selection(
        related='location_id.location_type_q', readonly=True)


class StockMoveLine(models.Model):

    _inherit = 'stock.move.line'

    @api.depends(
        'location_id.location_type_q',
        'location_dest_id.location_type_q',
        'product_id.subject_q')
    def _compute_is_letra_q(self):
        for move in self:
            if move.product_id.subject_q:
                if move.location_id.location_type_q and \
                        move.location_dest_id.location_type_q:
                    move.is_letra_q = True
            else:
                move.is_letra_q = False

    @api.depends(
        'location_id.location_type_q',
        'vehicle_id.letter_code_q',
        'location_id.code_q')
    def _compute_letra_q_group(self):
        for move in self:
            if move.location_id.location_type_q == '3':
                move.letra_q_group = '{} - {}'.format(
                    move.vehicle_id.letter_code_q or '',
                    move.picking_id.name or '')
            else:
                move.letra_q_group = move.location_id.code_q

    emptied = fields.Boolean('Emptied')
    is_letra_q = fields.Boolean("Letra Q Move", compute="_compute_is_letra_q",
                                store=True)
    vehicle_id = fields.Many2one(
        'vehicle',
        related='registry_line_id.registry_id.vehicle_id',
        readonly=True,
        store=True)
    deposit_id = fields.Many2one('deposit')
    dest_location_type_q = fields.Selection(
        related='location_id.location_type_q', readonly=True)
    letra_q_group = fields.Char(compute="_compute_letra_q_group", store=True)
    exportation_ids = fields.One2many('letra.q.exporter.move', 'move_id')
