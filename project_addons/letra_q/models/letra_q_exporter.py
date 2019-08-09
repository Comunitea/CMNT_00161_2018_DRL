# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class LetraQExporter(models.Model):

    _name = 'letra.q.exporter'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(default=lambda r: fields.Date.today())
    user_id = fields.Many2one('res.users', default=lambda r: r.env.user.id)
    letra_q_groups = fields.One2many('letra.q.exporter.group', 'exporter_id')

    def get_group_sequence(self):
        return self.letra_q_groups and max(self.mapped('letra_q_groups.sequence')) + 1 or 1


class LetraQExporterGroup(models.Model):
    _name = 'letra.q.exporter.group'

    exporter_id = fields.Many2one('letra.q.exporter')
    name = fields.Char()
    sequence = fields.Integer(default=1)
    move_ids = fields.One2many('letra.q.exporter.move', 'group_id', 'Moves')


class LetraQExporterMove(models.Model):
    _name = 'letra.q.exporter.move'
    _order = 'move_date'

    group_id = fields.Many2one('letra.q.exporter.group')
    move_id = fields.Many2one('stock.move.line', 'Generated from move')
    product_id = fields.Many2one('product.product', required=True)
    move_date = fields.Datetime(required=True)
    liters = fields.Float(required=True)
    origin_location = fields.Selection(
        [('1', 'tanque'),
         ('2', 'silo'),
         ('3', 'cisterna'),
         ('4', 'línea de Producción'),
         ('5', 'agente no nacional'),
         ('6', 'rechazo'),
         ('7', 'intermediario'),
         ('8', 'agente nacional')], required=True)
    origin_q_code = fields.Char(required=True)
    origin_deposit = fields.Char()
    origin_center = fields.Char()
    origin_country = fields.Many2one('res.country', required=True)
    origin_empty = fields.Boolean()
    dest_location = fields.Selection(
        [('1', 'tanque'),
         ('2', 'silo'),
         ('3', 'cisterna'),
         ('4', 'línea de Producción'),
         ('5', 'agente no nacional'),
         ('6', 'rechazo'),
         ('7', 'intermediario'),
         ('8', 'agente nacional')], required=True)
    dest_q_code = fields.Char(required=True)
    dest_center = fields.Char()
    dest_country = fields.Many2one('res.country', required=True)
    picking = fields.Char(size=100)
    notes = fields.Text(size=300)
