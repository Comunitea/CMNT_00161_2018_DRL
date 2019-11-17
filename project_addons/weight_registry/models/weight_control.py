# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import datetime
from odoo import models, fields, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

REGISTRY_TYPE = [
    ('incoming', 'Incoming'),
    ('outgoing', 'Outgoing'),
    ('production', 'Production'),
    ('internal', 'Internal'),
    ('wash', 'Wash'),
    ('other', 'Other')]


class WeightRegistryType(models.Model):

    _name = "weight.registry.type"

    def _get_types(self):
        selection = []
        return selection

    code = fields.Char('Code')
    description = fields.Char('Description')
    move_type_id = fields.Selection(selection=_get_types, string="Move type")


class WeightRegistry(models.Model):

    _name = "weight.registry"

    vehicle_id = fields.Many2one('vehicle', string="Vehicle", required=True)
    scale_weight = fields.Integer('weight')
    fill = fields.Boolean(
        'Fill', compute='_compute_worked_hours', store=True, readonly=True)
    check_in = fields.Datetime(
        string="Check In", default=fields.Datetime.now, required=True)
    check_out = fields.Datetime(string="Check Out")
    worked_hours = fields.Float(
        string='Worked Hours', compute='_compute_worked_hours',
        store=True, readonly=True)
    check_in_weight = fields.Integer('Check out weight')
    check_out_weight = fields.Integer('Check in weight')
    net = fields.Integer(
        'Net weight', compute='_compute_worked_hours',
        store=True, readonly=True)
    partner_id = fields.Many2one(
        'res.partner', 'Measured by', domain=[('driver', '=', True)])
    note = fields.Text('Notes')
    worked_hours = fields.Float(
        string='Worked Hours', compute='_compute_worked_hours',
        store=True, readonly=True)
    move_line_ids = fields.One2many(
        'stock.move', 'weight_registry_id', string="Weight register")
    picking_id = fields.Many2one('stock.picking')
    registry_type = fields.Selection(
        REGISTRY_TYPE, string="Registy type", required=False)
    product_id = fields.Many2one('product.product', 'Product')

    def apply_net_to_qty_done(self):
        for w_r in self.filtered(lambda x: x.check_out):
            qty_done = w_r.net
            if any(x.state == 'done' for x in w_r.mapped('move_line_ids')):
                raise exceptions.ValidationError(
                    _('Move {} is done.'.format(
                        w_r.mapped('move_line_ids').mapped('display_name'))))

            for mv in w_r.move_line_ids:
                for ml in mv.move_line_ids:
                    mv.qty_done = min(ml.product_uom_qty, qty_done)
                    qty_done -= mv.qty_done
                if qty_done:
                    mv.qty_done += qty_done

    def unlink(self):
        self.action_unlink_weight()
        return super().unlink()

    def action_unlink_weight(self):
        for w_r in self:
            w_r.mapped('picking_id').do_unreserve()
            w_r.picking_id = False

    def name_get(self):
        result = []
        for registry in self:
            if not registry.check_out:
                result.append((registry.id, _("%(empl_name)s from %(check_in)s: %(weight)s Kgrs") % {
                    'empl_name': registry.vehicle_id.register,
                    'weight': registry.check_in_weight,
                    'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(registry,
                                                                                            fields.Datetime.from_string(
                                                                                                registry.check_in))),
                }))
            else:
                result.append((registry.id, _("%(empl_name)s from %(check_in)s: %(weight_in)s Kgrs to %(check_out)s: %(weight_out)s Kgrs") % {
                    'empl_name': registry.vehicle_id.register,
                    'weight_in': registry.check_in_weight,
                    'weight_out': registry.check_out_weight,
                    'check_in': fields.Datetime.to_string(fields.Datetime.context_timestamp(registry,
                                                                                            fields.Datetime.from_string(
                                                                                                registry.check_in))),
                    'check_out': fields.Datetime.to_string(fields.Datetime.context_timestamp(registry,
                                                                                             fields.Datetime.from_string(
                                                                                                 registry.check_out))),
                }))
        return result

    @api.depends(
        'check_in', 'check_out', 'check_in_weight', 'check_out_weight')
    def _compute_worked_hours(self):
        for registry in self:
            if registry.check_out:
                # delta = datetime.strptime(
                #     registry.check_out,
                #     DEFAULT_SERVER_DATETIME_FORMAT) - datetime.strptime(
                #     registry.check_in, DEFAULT_SERVER_DATETIME_FORMAT)
                delta =  registry.check_out - registry.check_in
                registry.worked_hours = delta.total_seconds() / 3600.0

                registry.net = abs(
                    registry.check_in_weight - registry.check_out_weight)
                registry.fill = registry.check_out_weight > registry.check_in_weight

    def get_checkout_vals(self, date, weight=0.00, measured_by=False):
        if self.check_in_weight > weight:
            gross = self.check_in_weight
            tara = weight
        else:
            tara = self.check_in_weight
            gross = weight
        net = gross-tara
        vals = {'check_out': date,
                'weight_check_out': weight,
                'net': net
                }
        return vals

    @api.constrains('check_in', 'check_out', 'vehicle_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared
            to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for registry in self:
            # we take the latest attendance before our check_in
            # time and check it doesn't overlap with ours
            last_reg_before_check_in = self.env['weight.registry'].search([
                ('vehicle_id', '=', registry.vehicle_id.id),
                ('check_in', '<=', registry.check_in),
                ('id', '!=', registry.id),
            ], order='check_in desc', limit=1)
            if last_reg_before_check_in and \
                    last_reg_before_check_in.check_out and \
                    last_reg_before_check_in.check_out > registry.check_in:
                raise exceptions.ValidationError(_(
                    "Cannot create new registry record for %(empl_name)s, the vehicle was already checked in on %(datetime)s") %
                    {'empl_name': registry.vehicle_id.register,
                     'datetime': fields.Datetime.to_string(
                        fields.Datetime.context_timestamp(
                            self, fields.Datetime.from_string(registry.check_in))),
                     })

            if not registry.check_out:
                # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
                no_check_out_registry = self.env['weight.registry'].search([
                    ('vehicle_id', '=', registry.vehicle_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', registry.id),
                ], order='check_in desc', limit=1)
                if no_check_out_registry:
                    raise exceptions.ValidationError(_(
                        "Cannot create new registry record for %(empl_name)s, the vehicle hasn't checked out since %(datetime)s") % {
                                                         'empl_name': registry.vehicle_id.register,
                                                         'datetime': fields.Datetime.to_string(
                                                             fields.Datetime.context_timestamp(self,
                                                                                               fields.Datetime.from_string(
                                                                                                   no_check_out_registry.check_in))),
                                                     })
            else:
                # we verify that the latest attendance with check_in time before our check_out time
                # is the same as the one before our check_in time computed before, otherwise it overlaps
                last_reg_before_check_out = self.env['weight.registry'].search([
                    ('vehicle_id', '=', registry.vehicle_id.id),
                    ('check_in', '<', registry.check_out),
                    ('id', '!=', registry.id),
                ], order='check_in desc', limit=1)
                if last_reg_before_check_out and last_reg_before_check_in != last_reg_before_check_out:
                    raise exceptions.ValidationError(_(
                        "Cannot create new registry record for %(empl_name)s, the vehicle was already checked in on %(datetime)s") % {
                                                         'empl_name': registry.vehicle_id.register,
                                                         'datetime': fields.Datetime.to_string(
                                                             fields.Datetime.context_timestamp(self,
                                                                                               fields.Datetime.from_string(
                                                                                                   last_reg_before_check_out.check_in))),
                                                     })

    @api.model
    def set_weight_registry(self, vehicle_id, weight):
        res = True
        vehicle = self.env['vehicle'].browse(vehicle_id)
        vehicle.vehicle_action_change()
        # if not vehicle.check_in_weight:
        #     vehicle.check_in_weight = weight
        # else:
        #     vehicle.check_out_weight = weight
        return res





