# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
import odoo.addons.decimal_precision as dp


class QcInspection(models.Model):
    _inherit = 'qc.inspection'

    @api.depends('test.no_cases')
    def _get_no_cases(self):
        for inspection in self:
            inspection.no_cases = int(inspection.test.no_cases)

    no_cases = fields.\
        Integer("No of Cases", compute="_get_no_cases", store=True)
    
    valid_for_move = fields.Boolean(
        compute="_compute_valid_for_move", string='Success',
        help='This field will be marked if all tests requiered for move are covered.',
        store=True,
        readonly=True)
        
    @api.multi
    def _prepare_inspection_line(self, test, line, fill=None):
        data = super()._prepare_inspection_line(test, line, fill)
        data['result_required'] = line.result_required
        return data 

    @api.depends('inspection_lines', 'inspection_lines.success')
    def _compute_valid_for_move(self):
        for i in self:
            i.valid_for_move = False
            required_lines = i.inspection_lines.filtered(lambda a: a.result_required == True)
            if not required_lines:
                i.valid_for_move = True
            else: 
                i.valid_for_move = all([x.success for x in required_lines])


class QcInspectionLine(models.Model):
    _inherit = 'qc.inspection.line'

    @api.depends('question_type', 'uom_id', 'test_uom_id', 'max_value',
                 'min_value', 'quantitative_value', 'qualitative_value',
                 'possible_ql_values', 'quantitative_value2',
                 'quantitative_value3', 'quantitative_value4',
                 'quantitative_value5', 'quantitative_value6')
    def _compute_quality_test_check(self):
        super(QcInspectionLine, self.
              filtered(lambda x: x.inspection_id.no_cases == 1 or
                       x.question_type == 'qualitative')).\
            _compute_quality_test_check()
        for l in self.filtered(lambda x: x.inspection_id.no_cases != 1 and
                               x.question_type != 'qualitative'):
            if l.uom_id.id == l.test_uom_id.id:
                amount = l.quantitative_value
            else:
                amount = self.env['product.uom']._compute_quantity(
                    l.quantitative_value,
                    l.test_uom_id.id)

            if l.test_line.result_type == 'one' and \
                    l.max_value >= amount >= l.min_value:
                l.success = True
            elif l.test_line.result_type == 'all' and not \
                    l.max_value >= amount >= l.min_value:
                l.success = False
            else:
                total_amount = amount
                result = False
                for case in range(2, l.inspection_id.no_cases + 1):
                    if l.uom_id.id == l.test_uom_id.id:
                        amount = l['quantitative_value' + str(case)]
                    else:
                        amount = self.env['product.uom']._compute_quantity(
                            l['quantitative_value' + str(case)],
                            l.test_uom_id.id)
                    total_amount += amount

                    if l.test_line.result_type == 'all' and not \
                            l.max_value >= amount >= l.min_value:
                        l.success = False
                        result = True
                        break
                    elif l.test_line.result_type == 'one' and \
                            l.max_value >= amount >= l.min_value:
                        l.success = True
                        result = True
                        break
                if not result:
                    if l.test_line.result_type == 'all':
                        l.success = True
                    elif l.test_line.result_type == 'sum':
                        l.success = l.max_value >= total_amount >= l.min_value
                    elif l.test_line.result_type == 'avg':
                        l.success = l.max_value >= \
                            (total_amount / l.inspection_id.no_cases) >= \
                            l.min_value

    quantitative_value2 = fields.Float(
        'Quantitative value 2', digits=dp.get_precision('Quality Control'),
        help="Value 2 of the result for a quantitative question.",
        default=0.0)
    quantitative_value3 = fields.Float(
        'Quantitative value 3', digits=dp.get_precision('Quality Control'),
        help="Value 3 of the result for a quantitative question.",
        default=0.0)
    quantitative_value4 = fields.Float(
        'Quantitative value 4', digits=dp.get_precision('Quality Control'),
        help="Value 4 of the result for a quantitative question.",
        default=0.0)
    quantitative_value5 = fields.Float(
        'Quantitative value 5', digits=dp.get_precision('Quality Control'),
        help="Value 5 of the result for a quantitative question.",
        default=0.0)
    quantitative_value6 = fields.Float(
        'Quantitative value 6', digits=dp.get_precision('Quality Control'),
        help="Value 6 of the result for a quantitative question.",
        default=0.0)
    result_required= fields.Boolean("Required for validate move")
