# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ExportMovesLetraQ(models.TransientModel):
    _name = 'export.moves.letra.q'

    exportation_id = fields.Many2one('letra.q.exporter')

    def create_exportation(self):
        exportation = self.exportation_id
        if not exportation:
            exportation = self.env['letra.q.exporter'].create({})
        for move_line in self.env['stock.move.line'].browse(
                self._context.get('active_ids')):
            group_name = move_line.letra_q_group
            use_group = self.env['letra.q.exporter.group'].search([
                ('exporter_id', '=', exportation.id),
                ('name', '=', group_name)
            ])
            if not use_group:
                use_group = self.env['letra.q.exporter.group'].create({
                    'exporter_id': exportation.id,
                    'name': group_name,
                    'sequence': exportation.get_group_sequence()
                })
            if move_line.location_id.location_type_q == '3':   #ORIGEN ES CISTERNA
                origin_letra_q = move_line.vehicle_id.letter_code_q
                origin_center = move_line.picking_id.partner_id or move_line.picking_id.company_id.partner_id
            elif move_line.location_id.location_type_q in ('1','2'):   # ORIGEN ES TANQUE O SILO
                origin_letra_q = move_line.location_id.code_q
                origin_center = move_line.picking_id.company_id.partner_id
            else:
                raise ValidationError(_("Origen no implementado en Letra Q {}".format(move_line.location_id.name)))
        
                
            if move_line.location_dest_id.location_type_q == '3': # DESTINO ES CISTERNA
                dest_letra_q = move_line.vehicle_id.letter_code_q
                dest_center = move_line.picking_id.partner_id or move_line.picking_id.company_id.partner_id
                destination = ''
            elif move_line.location_dest_id.location_type_q in ('1','2'): # DESTINO ES TANQUE O SILO
                dest_letra_q = move_line.location_dest_id.code_q
                dest_center = move_line.picking_id.partner_id or move_line.picking_id.company_id.partner_id
                destination = ''
            elif move_line.location_dest_id.location_type_q == '4': # DESTINO ES LINEA DE PRODUCCIÓN
                dest_letra_q = move_line.location_dest_id.code_q
                dest_center = move_line.picking_id.partner_id or move_line.picking_id.company_id.partner_id
                destination = move_line.move_id.destination_q
            elif move_line.location_dest_id.location_type_q == '6': # DESTINO ES RECHAZO
                dest_letra_q = move_line.location_dest_id.code_q
                dest_center = move_line.picking_id.partner_id or move_line.picking_id.company_id.partner_id
                destination = move_line.move_id.destination_q
            
            else:
                raise ValidationError(_("Destino no implementado en Letra Q {}".format(move_line.location_dest_id.name)))
            vals = {
                'group_id': use_group.id,
                'move_id': move_line.id,
                'product_id': move_line.product_id.id,
                'move_date': move_line.date,
                'liters': int(move_line.qty_done),
                'origin_location': move_line.location_id.location_type_q,
                'origin_q_code': origin_letra_q,
                'origin_deposit': move_line.deposit_id and move_line.deposit_id.number or '',
                'origin_center': origin_center.vat,
                'origin_country': origin_center.country_id.id,
                'origin_empty': move_line.emptied,
                'dest_q_code': dest_letra_q,
                'dest_location': move_line.location_dest_id.location_type_q,
                'dest_center': dest_center.vat,
                'dest_country': dest_center.country_id.id,
                'picking': move_line.picking_id.name,
                'destination': destination
            }
            self.env['letra.q.exporter.move'].create(vals)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'letra.q.exporter',
            'res_id': exportation.id,
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('letra_q.letra_q_exporter_view_form').id,
            'target': 'current',
        }
