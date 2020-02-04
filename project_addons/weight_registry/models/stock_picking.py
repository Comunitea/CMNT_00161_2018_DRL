# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from .weight_registry import REGISTRY_TYPE


class StockPicking(models.Model):

    _inherit = "stock.picking"

    picking_ids = fields.Many2many('stock.picking', "pick_weight_rel", column1="picking_id", column2="weight_id",
                                   string="Albaranes asociados")
    weight_registry_ids = fields.Many2many('weight.registry',  "pick_weight_rel", column2="picking_id", column1="weight_id",string="Linked weight registry")
    weight_control = fields.Selection(related='picking_type_id.weight_control', store=True)


    @api.multi
    def fill_from_weight_wzd(self):
        self.ensure_one()
        wr_id = self.weight_registry_ids
        if not wr_id:
            raise ValidationError ('El albarán no tiene asignado una pesada')
        product_id = self.move_lines[0].product_id
        return wr_id.create_new_wzd(picking_id=self, product_id = product_id)


    @api.multi
    def link_weight_wzd(self):
        self.ensure_one()
        domain = [('linked', '=', False)]
        wc_ids = self.env['weight.registry'].search(domain)
        val = {'picking_id': self.id}
        new_wzd = self.env['weight.pick.link.wzd'].create(val)
        for wc in wc_ids:
            vals = {'wzd_id': new_wzd.id,
                    'weight_registry_id': wc.id}
            self.env['weight.pick.link.line.wzd'].create(vals)

        action = new_wzd.get_formview_action()
        action['target'] = 'new'
        # return action
        action['res_id'] = new_wzd.id
        return action