# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, fields, api, _
from random import choice
from string import digits
from odoo.exceptions import ValidationError


class Vehicle(models.Model):

    _inherit = "vehicle"

    def name_get(self):
        return [
            (vehicle.id, "{}: {}".format(
                vehicle.register or vehicle.barcode,
                vehicle.vehicle_type_id.code or vehicle.vehicle_type_id.name)
                if vehicle.vehicle_type_id else
                vehicle.register or vehicle.barcode) for vehicle in self]

    def _default_random_barcode(self):
        barcode = None
        while not barcode or self.env['vehicle'].search(
                [('barcode', '=', barcode)]):
            barcode = "".join(choice(digits) for i in range(8))
        return barcode

    def _get_weight_registry_count(self):
        for vehicle in self:
            vehicle.weight_registry_count = len(vehicle.weight_registry_ids)

    weight_registry_ids = fields.One2many(
        'weight.registry', 'vehicle_id', string="Weight registry")
    weight_registry_count = fields.Integer(
        'Weight Registry Count', compute="_get_weight_registry_count")

    barcode = fields.Char(
        string="Badge ID", help="ID used for vehicle identification.",
        default=_default_random_barcode, copy=False)
    weight_control_ids = fields.One2many(
        'weight.registry', 'vehicle_id',
        help='list of weight.registry for this vehicle')
    last_weight_control_id = fields.Many2one(
        'weight.registry', compute='_compute_last_weight_control_id')
    weight_registry_state = fields.Selection(
        string="Vehicle state", compute='_compute_last_weight_state',
        selection=[('checked_out', "Check out"), ('checked_in', "Check in")])
    last_driver_id = fields.Many2one(
        'res.partner', compute="_compute_last_weight_control_id")

    def action_view_weight_registry(self):
        w_reg = self.mapped('weight_registry_ids')
        action = self.env.ref(
            'weight_registry.weight_registry_action_vehicle').read()[0]
        action['context'] = {'default_vehicle_id': self.id}
        if len(w_reg) > 1:
            action['domain'] = [('id', 'in', w_reg.ids)]
        elif len(w_reg) == 1:
            action['views'] = [
                (self.env.ref('weight_registry.weight_registry_view_form').id,
                 'form')]
            action['res_id'] = w_reg.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.depends(
        'last_weight_control_id.check_in',
        'last_weight_control_id.check_out',
        'last_weight_control_id')
    def _compute_last_weight_state(self):
        for vehicle in self:
            vehicle.weight_registry_state = vehicle.last_weight_control_id and \
                not vehicle.last_weight_control_id.check_out and \
                'checked_in' or 'checked_out'

    @api.depends('weight_control_ids')
    def _compute_last_weight_control_id(self):
        for vehicle in self:
            last = self.env['weight.registry'].search([
                ('vehicle_id', '=', vehicle.id),
            ], order="id desc", limit=1)
            vehicle.last_weight_control_id = last
            last = self.env['weight.registry'].search([
                ('vehicle_id', '=', vehicle.id), ('partner_id', '!=', False)
            ], limit=1)
            vehicle.last_driver_id = last.partner_id

    @api.model
    def vehicle_scan(self, barcode):
        """ Receive a barcode scanned from the Kiosk Mode and change the
            attendances of corresponding vehicle.
            Returns either an action or a warning.
        """
        vehicle = self.search([('barcode', '=', barcode)], limit=1)
        return vehicle and vehicle.attendance_action(
            'hr_attendance.hr_attendance_action_kiosk_mode') or \
            {'warning': _('No vehicle corresponding to barcode %(barcode)s') %
             {'barcode': barcode}}

    def vehicle_action_change(self, weight=0.00, meaasured_by=False):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """

        if len(self) > 1:
            raise ValidationError(
                _('Cannot perform check in or check out on multiple vehicles.')
            )
        action_date = fields.Datetime.now()

        if self.weight_registry_state != 'checked_in':
            vals = {
                'vehicle_id': self.id,
                'check_in': action_date,
                'check_in_weight': weight,
                'measured_by': meaasured_by
            }
            return self.env['weight.registry'].create(vals)
        else:
            w_registry = self.env['weight.registry'].search(
                [('vehicle_id', '=', self.id), ('check_out', '=', False)],
                limit=1)
            if w_registry:
                w_registry.write(
                    w_registry.get_checkout_vals(action_date, weight))
            else:
                raise ValidationError(
                    _('Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
                      'Your attendances have probably been modified manually by human resources.') % {
                        'empl_name': self.name, })
            return w_registry

    @api.multi
    def vehicle_action(self, next_action, weight=0.0):
        return
    
    @api.model
    def get_vehicle_data(self, vehicle_number):
        res = {}
        domain = [('register', '=', vehicle_number)]
        vehicle = self.search(domain, limit=1)
        if vehicle:
            deposits = []
            for dep in vehicle.deposit_ids:
                dep_val = {
                    'id': dep.id,
                    'code': dep.code,
                    'number': dep.number,
                    'capacity': dep.capacity
                }
                deposits.append(dep_val)

            res = {
                'id': vehicle.id,
                'weight_registry_state': vehicle.weight_registry_state,
                'register': vehicle.register,
                'barcode': vehicle.barcode,
                'deposit_ids': deposits
            }
        return res
