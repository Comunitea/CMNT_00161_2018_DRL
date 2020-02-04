# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ContractContract(models.Model):

    _inherit = "contract.contract"

    position = fields.Selection([('muelle', 'En destino sobre muelle fábrica')])
    analytic = fields.Char()
    quality_demand = fields.Char()
    billing = fields.Selection([("end_of_month", "End of month")])

    def get_product_report_line(self):
        self.ensure_one()
        if self.price_agreement_ids:
            line = self.price_agreement_ids[0]
            deliveries = len(self.delivery_agreement_ids)
            quantity = (
                sum([x.quantity for x in self.delivery_agreement_ids]) * 1000
            )
            product_name = line.product_id.name
            return "{}  cisternas de {} +/- {} litros".format(
                deliveries, product_name, int(quantity)
            )
