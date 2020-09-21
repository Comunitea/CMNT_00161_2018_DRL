# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, fields, _


class StockPicking(models.Model):

    _inherit = "stock.picking"

    conform = fields.Boolean('Se ajusta', help='Se ajusta a las especificaciones')
    specifications = fields.Char('Especificaciones', help='Ficha de especificaciones')
    not_conform_note = fields.Text('Motivo', help='En caso de que la partida NO se ajuste a las especificaciones, indicar el motivo del incumplimiento')

    def get_letter_values(self):
        self.ensure_one()
        res = {
            'lq_center': '',

            'operator': '*',
            'transport': '*',
            'driver': '*',
            'truck': '',
            'trailer': '*',
            'nif_transport': '*',
            'nif_driver': '*',
            'lq_truck': '*',
            'lq_trailer': '',

            'product': '',
            'orig_silo':'',
            'kg': '',
            'inspection_lines': '*',

            'registration': '',
            'in': '',
            'out': '',
            'net': '',
            'date': '',

            'precint': '',
            'lots': '',
            'production': '*',
        }

        if self.move_lines and self.move_lines[0].move_line_ids and \
                self.move_lines[0].move_line_ids[0].registry_line_id:
            ml = self.move_lines[0]
            wrl = ml.move_line_ids[0].registry_line_id
            wr = wrl.registry_id
            if wr.vehicle_id:
                res['truck'] = wr.vehicle_id.register
                res['registration'] = wr.vehicle_id.register
                res['lq_truck'] = wr.vehicle_id.letter_code_q
            
            if ml.product_id:
                res['product'] = ml.product_id.name
            
            locs = ml.move_line_ids.mapped('location_id').\
                filtered(lambda x: x.location_type_q == '2')
            if locs:
                res['orig_silo'] = ','.join(locs.mapped('name'))
            
            if ml.registry_line_id_qty:
                res['kg'] = ml.registry_line_id_qty
            
            if wr.check_in_weight:
                res['in'] = wr.check_in_weight
            if wr.check_out_weight:
                res['out'] = wr.check_out_weight
            if wr.net:
                res['net'] = wr.net
            if wr.check_out:
                res['date'] = wr.check_out.strftime('%d-%m-%Y %HH:%MM')
            
            lots = ml.move_line_ids.mapped('lot_id')
            if lots:
                res['lots'] = ','.join(lots.mapped('name'))
                

        return res