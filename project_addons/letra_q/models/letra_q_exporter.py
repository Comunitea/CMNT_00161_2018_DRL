# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from datetime import datetime, timedelta, time
from odoo.exceptions import ValidationError
import base64


class LetraQExporter(models.Model):

    _name = 'letra.q.exporter'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(default=lambda r: fields.Date.today())
    user_id = fields.Many2one('res.users', default=lambda r: r.env.user.id)
    letra_q_groups = fields.One2many('letra.q.exporter.group', 'exporter_id')

    def get_group_sequence(self):
        return self.letra_q_groups and max(self.mapped('letra_q_groups.sequence')) + 1 or 1

    def get_letra_q_file_name(self):
        user_vat = "{}".format(self.user_id.partner_id.vat.replace('-','').replace('_','') or "NOVAT").zfill(9)
        lqcode = "{}".format("000000").zfill(7) # letra q code 5 digits + 2 control digits
        date_file = "{}".format(datetime.now().strftime('%Y%m%d'))
        seq = "{}".format("001").zfill(3) # Position in files generated on the same day
        return "MOV{}{}.TXT".format(user_vat,lqcode,date_file,seq)

    @api.multi
    def create_letra_q_file(self):
        filename = self.get_letra_q_file_name()
        f = open(filename,"w")
        if f:
            for group in self.letra_q_groups:
                group_line = group.create_group_line()
                for move in group.move_ids:
                    line = group_line + move.create_move_line()
                    f.write(line+ '\n')
            f.close()
        else:
            raise ValidationError(_("There was a problem creating the file {}".format(filename)))
        
        try:
            file_ = open(filename,"r", encoding="utf8")
            data = file_.read()
            file_.close()
            attatchment = self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas':base64.b64encode(str.encode(data)),
                'datas_fname': filename + '.txt',
                'store_fname': filename,
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'text/plain'
            })
        except Exception as e:
            raise ValidationError(_('We could not create the file because:\n%s.' % e))

class LetraQExporterGroup(models.Model):
    _name = 'letra.q.exporter.group'

    exporter_id = fields.Many2one('letra.q.exporter')
    name = fields.Char()
    sequence = fields.Integer(default=1)
    move_ids = fields.One2many('letra.q.exporter.move', 'group_id', 'Moves')

    def create_group_line(self):
        line = ''

        try:
            dates = self.move_ids.mapped('move_date')
            dates.sort()
            group_date = dates[0].strftime('%d/%m/%Y')
            moves_num = len(self.move_ids)
            line += "{}#".format(group_date)
            line += "{}#".format(self.name[:30])
            line += "{}#".format(moves_num)
        except Exception as e:
            raise ValidationError(_('We could not create the line for the group %s because:\n%s.' % (self.name, e)))

        return line

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


    def create_move_line(self):
        line = ''

        try:
            line += "{}#".format(self.product_id.species_q if self.product_id.species_q else "")
            line += "{}#".format(self.move_date.strftime('%d/%m/%Y') if self.move_date else "")
            line += "{}#".format(self.move_date.strftime('%H:%M') if self.move_date else "")
            line += "{}#".format(int(round(self.liters, 0)) if self.liters else "")
            line += "{}#".format(self.origin_location if self.origin_location else "")
            line += "{}#".format(self.origin_q_code if self.origin_q_code else "")
            line += "{}#".format(self.origin_deposit if self.origin_deposit else "")
            line += "{}#".format(self.origin_center if self.origin_center else "")
            line += "{}#".format("") # VAT of the operator who rented the deposit
            line += "{}#".format(self.origin_country.letra_q_code if self.origin_country.letra_q_code else "")
            line += "{}#".format("") # Plates of the tanker lorry in origin
            line += "{}#".format("S" if self.origin_empty else "N")
            line += "{}#".format("") # Sample taker or technician
            line += "{}#".format("") # Lab code
            line += "{}#".format("") # Sample code
            line += "{}#".format(self.dest_location if self.dest_location else "")
            line += "{}#".format(self.dest_q_code if self.dest_q_code else "")
            line += "{}#".format("") # Destination deposit
            line += "{}#".format(self.dest_center if self.dest_center else "")
            line += "{}#".format("") # VAT of the operator who rented the deposit in destination
            line += "{}#".format(self.dest_country.letra_q_code if self.dest_country.letra_q_code else "")
            line += "{}#".format("") # Plates of the tanker lorry in destination
            line += "{}#".format("") # Destination. Production line or dejected
            line += "{}#".format("") # Needed if refected: Place code.
            line += "{}#".format("") # Needed if refected: Reason.
            line += "{}#".format(self.picking[:100] if self.picking else "")
            line += "{}#".format("") # β-Lactamic test order 1
            line += "{}#".format("") # β-Lactamic test order 1 results
            line += "{}#".format("") # Tetracycline test order 1
            line += "{}#".format("") # Tetracycline test order 1 results
            line += "{}#".format("") # β-Lactamic test order 2
            line += "{}#".format("") # β-Lactamic test order 2 results
            line += "{}#".format("") # Tetracycline test order 2
            line += "{}#".format("") # Tetracycline test order 2 results
            line += "{}".format(self.notes[:300] if self.notes else "")

        except Exception as e:
            raise ValidationError(_('We could not create the line for one move in %s because:\n%s.' % (self.group_id.name, e)))

        return line