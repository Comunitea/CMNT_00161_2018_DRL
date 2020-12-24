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

    @api.multi
    def compute_first_product_id(self):
        for pick in self:
            move = pick.move_lines.filtered(lambda x: x.product_id.weight_control)
            if move:
                pick.first_product_id = move[0].product_id

    @api.multi
    def _compute_last_weight_state(self):
        for pick in self:
            v_ids = pick.vehicle_ids.filtered(lambda x: x.master)
            if v_ids:
                pick.weight_registry_state = v_ids[0].weight_registry_state

    weight_registry_id = fields.Many2one('weight.registry', string="Linked weight registry", copy=False)
    weight_control = fields.Selection(related='picking_type_id.weight_control', store=True)
    net_weight_registry = fields.Integer(related="weight_registry_id.net", string='Net weight registry')#, compute="compute_weight_state")
    weight_state = fields.Selection (selection=PICK_WEIGHT_STATES, string="Weight state",
                                     compute="compute_weight_state",
                                     help="No weight: No need weight control.\nWaiting Control: Need control, watiting fot it.\nWaiting assigment: Control done, need moves.\Moves done. Weight done")
    available_vehicle_ids = fields.Many2many(related="carrier_id.vehicle_ids")
    vehicle_ids = fields.Many2many('vehicle', string="Listado de matrículas", required=False, copy=False, domain="[('id', 'in', available_vehicle_ids)]")
    weight_registry_state = fields.Selection(
        string="Vehicle state", compute='_compute_last_weight_state',
        selection=[('checked_out', "Check out"), ('checked_in', "Check in")], copy=False)

    @api.multi
    def do_unreserve(self):
        super().do_unreserve()
        for picking in self:
            #picking.weight_registry_ids = False
            picking.weight_registry_id = False


    @api.multi
    def compute_weight_state(self):
        for pick in self:
            if not pick.first_product_id:
                pick.weight_state = 'none'
                continue

            #pick.net_weight_registry = sum(x.net for x in pick.weight_registry_ids)
            if pick.state in ['draft', 'cancel', 'confirmed', 'waiting'] or pick.weight_control == 'none':
                pick.weight_state = 'none'
                continue
            if pick.state == 'done':
                pick.weight_state = 'done'
                continue
            if not pick.weight_registry_id or (pick.weight_registry_id and not pick.weight_registry_id.check_out):
                # not pick.weight_registry_ids or not pick.weight_registry_ids.check_out:
                pick.weight_state = 'waiting'
            else:
                if any(not sml.registry_line_id for sml in pick.move_line_ids):
                    pick.weight_state = 'to_assign'
                else:
                    pick.weight_state = 'done'


    @api.multi
    def link_and_fill_from_weight_wzd(self):
        self.ensure_one()
        if self.weight_state in ('done', 'none'):
            return
        vehicle_id = self.vehicle_ids and self.vehicle_ids[0] or False

        if vehicle_id:
            if vehicle_id.weight_registry_state == 'checked_in':
                ## Tengo que asigna
                return self.fill_from_weight_wzd()


        if self.weight_state == 'waiting':
            return self.link_weight_wzd()
        else:
            return self.fill_from_weight_wzd()

    @api.multi
    def fill_from_weight_wzd(self):
        self.ensure_one()
        #wr_id = self.weight_registry_ids
        wr_id = self.weight_registry_id
        if not wr_id:
            raise ValidationError ('El albarán no tiene asignado una pesada')
        product_id = self.move_lines[0].product_id
        return wr_id._create_new_wzd(picking_id=self, product_id = product_id)


    @api.multi
    def link_weight_wzd(self):
        self.ensure_one()
        domain = [('picking_id', '=', False)]
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

    @api.multi
    def fill_weight_from_pick(self):
        self.ensure_one()
        if not self.vehicle_ids:
            raise ValidationError (_('You need vehicles'))

        weight = self.env['weight.online'].get_last()
        vehicle_ids = []
        deposit_ids = []
        vehicle_id = self.vehicle_ids[0]

        if not self.vehicle_ids[0].vehicle_type_id.master:
            raise ValidationError(_('First register must be master'))

        for v_id in self.vehicle_ids:
            vals = {'id': v_id.id, 'register': v_id.register}
            vehicle_ids.append(vals)
            for dep in v_id.deposit_ids:
                v_dep = {'id': dep.id, 'check': False}
                deposit_ids.append((v_dep))

        ## Creo el asistente
        if self.weight_registry_id:
            show_details = True
        else:
            show_details = False
        wzd_vals = {'vehicle_id': v_id.id, 'picking_id': self.id, 'weight': weight, 'show_details': show_details}
        wzd_id = self.env['weight.pick.direct.wzd'].create(wzd_vals)
        for v_id in self.vehicle_ids:
            for dep in v_id.deposit_ids:
                line_val = {'wzd_id': wzd_id.id,
                            'vehicle_id': v_id.id,
                            'deposit_id': dep.id,
                            'checked': True,
                            'capacity': dep.capacity}
                wzd_id.line_ids.create(line_val)
        action = wzd_id.get_formview_action()
        action['target'] = 'new'
        # return action
        action['res_id'] = wzd_id.id
        return action








