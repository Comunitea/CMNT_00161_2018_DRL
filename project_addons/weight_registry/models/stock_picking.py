# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from .weight_registry import REGISTRY_TYPE

PICK_WEIGHT_STATES=[('none', 'No weight'), ('waiting', 'Waiting control'), ('to_assign', 'Waiting assigment'), ('done', 'Done')]


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    weight_control_default_uom_id = fields.Many2one('uom.uom', string="Default weight control unit")
    flow_control_default_uom_id= fields.Many2one('uom.uom', string="Default flow control unit")

    @api.model
    def get_values(self):
        res = super().get_values()
        get_param = self.env["ir.config_parameter"].sudo().get_param
        res.update(
            weight_control_default_uom_id=int(
                get_param("weight_registry.weight_control_default_uom_id", default=False)
            ),
            flow_control_default_uom_id=int(
                get_param("weight_registry.flow_control_default_uom_id", default=False)
            ),
        )
        return res

    def set_values(self):
        super().set_values()
        set_param = self.env["ir.config_parameter"].sudo().set_param
        set_param("weight_registry.weight_control_default_uom_id", self.weight_control_default_uom_id.id)
        set_param("weight_registry.flow_control_default_uom_id", self.flow_control_default_uom_id.id)


class StockPicking(models.Model):

    _inherit = "stock.picking"

    #picking_ids = fields.Many2many('stock.picking', "pick_weight_rel", column1="picking_id", column2="weight_id",
    #                               string="Albaranes asociados")
    weight_registry_ids = fields.Many2many('weight.registry', "stock_picking_weight_rel", string="Linked weight registry")
    weight_control = fields.Selection(related='picking_type_id.weight_control', store=True)
    weight_state = fields.Selection (selection=PICK_WEIGHT_STATES, string="Weight state",
                                     compute="compute_weight_state",
                                     help="No weight: No need weight control.\nWaiting Control: Need control, watiting fot it.\nWaiting assigment: Control done, need moves.\Moves done. Weight done")

    @api.multi
    def compute_weight_state(self):
        for pick in self:
            if pick.weight_control == 'none':
                pick.weight_state = 'none'
                continue
            if pick.state == 'done':
                pick.weight_state = 'done'
                continue
            if not pick.weight_registry_ids:
                pick.weight_state = 'waiting'
            else:
                if any(not sml.registry_line_id for sml in pick.move_line_ids):
                    pick.weight_state = 'to_assign'
                else:
                    pick.weight_state = 'done'

    @api.multi
    def link_and_fill_from_weight_wzd(self):
        self.ensure_one()
        if self.weight_control in ('done', 'none'):
            return

        if self.weight_state == 'waiting':
            return self.link_weight_wzd()
        else:
            return self.fill_from_weight_wzd()

    @api.multi
    def fill_from_weight_wzd(self):
        self.ensure_one()
        wr_id = self.weight_registry_ids
        if not wr_id:
            raise ValidationError ('El albarán no tiene asignado una pesada')
        product_id = self.move_lines[0].product_id
        return wr_id._create_new_wzd(picking_id=self, product_id = product_id)


    @api.multi
    def link_weight_wzd(self):
        self.ensure_one()
        domain = [('picking_ids', '=', False)]
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