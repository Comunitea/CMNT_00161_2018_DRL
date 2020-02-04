# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models
from odoo.addons.quality_control.models.qc_trigger_line import (
    _filter_trigger_lines,
)


class StockPicking(models.Model):

    _inherit = "stock.picking"
    created_tests = fields.Boolean()

    def launch_tests_before_move(self):
        self.ensure_one()
        inspection_model = self.env["qc.inspection"]
        qc_trigger = self.env["qc.trigger"].search(
            [("picking_type_id", "=", self.picking_type_id.id)]
        )
        for operation in self.move_lines:
            trigger_lines = set()
            for model in [
                "qc.trigger.product_category_line",
                "qc.trigger.product_template_line",
                "qc.trigger.product_line",
            ]:
                partner = (
                    self.partner_id if qc_trigger.partner_selectable else False
                )
                trigger_lines = trigger_lines.union(
                    self.env[model]
                    .with_context(before_move_done=True)
                    .get_trigger_line_for_product(
                        qc_trigger, operation.product_id, partner=partner
                    )
                )
            for trigger_line in _filter_trigger_lines(trigger_lines):
                inspection_model._make_inspection(operation, trigger_line)
        self.created_tests = True
