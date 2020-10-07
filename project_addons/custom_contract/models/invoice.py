# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
import math


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.model
    def create(self, vals):
        res = super().create(vals)
        sale_order = self.env['sale.order'].search([('contract_id', '!=', False)]).filtered(lambda x: res.invoice_id in x.invoice_ids)

        def compute_new_data(price_unit, demand, line):
            difference = False
            increment = False
            if demand.comparative_sign == 'greaterThan' and line.quantitative_value > demand.standard_value:
                difference = line.quantitative_value - demand.standard_value
                if demand.tolerance == 0.0:
                    increment = 1
                else:
                    increment = math.floor(difference/demand.tolerance) if math.floor(difference/demand.tolerance) > 0 else 1
                    
            elif demand.comparative_sign == 'lowerThan' and line.quantitative_value < demand.standard_value:
                difference = demand.standard_value - line.quantitative_value
                if demand.tolerance == 0.0:
                    increment = 1
                else:
                    increment = math.floor(difference/demand.tolerance) if math.floor(difference/demand.tolerance) > 0 else 1
            else:
                return False
            
            if increment and demand.price_change == 'bonus':
                return res.price_unit + (demand.value*increment)
            elif increment and demand.price_change == 'discount':
                return res.price_unit - (demand.value*increment)
            else:
                return False

        if len(sale_order) > 1:
            sale_order = sale_order[-1]
        
        if sale_order and sale_order.contract_id and sale_order.contract_id.quality_demand_ids:
            for demand in sale_order.contract_id.quality_demand_ids.filtered(lambda x: x.product_id == res.product_id):
                inspection = sale_order.picking_ids.mapped('qc_inspections_ids').filtered(lambda x: x.test == demand.qc_test_id)
                for line in inspection.inspection_lines.filtered(lambda x: x.test_line == demand.qc_test_question_id):
                    new_price_unit = compute_new_data(res.price_unit, demand, line)
                    if new_price_unit:
                        res.update({
                            "price_unit": new_price_unit
                        })
        return res