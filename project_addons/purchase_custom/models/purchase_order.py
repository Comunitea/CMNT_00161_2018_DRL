# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def _create_picking(self):
        super()._create_picking()
        StockPicking = self.env['stock.picking']
        for order in self:
            pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
            for pick in pickings:
                moves = pick.move_lines.filtered(lambda x: x.purchase_line_id.date_planned != pick.scheduled_date)
                while moves:
                    scheduled_date = moves[0].purchase_line_id.date_planned
                    res = order._prepare_picking()
                    res['scheduled_date'] = scheduled_date
                    new_picking = StockPicking.create(res)
                    moves_to_assign = moves.filtered(lambda x: x.purchase_line_id.date_planned == scheduled_date)
                    for move in moves_to_assign:
                        move.picking_id = new_picking
                        move.move_line_ids.picking_id = new_picking
                    moves -= moves_to_assign
                    new_picking.message_post_with_view('mail.message_origin_link',
                                                   values={'self': new_picking, 'origin': order},
                                                   subtype_id=self.env.ref('mail.mt_note').id)
        return True


