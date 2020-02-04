# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class QcTriggerLine(models.AbstractModel):
    _inherit = "qc.trigger.line"

    before_move_done = fields.Boolean()


class QcTriggerProductTemplateLine(models.Model):
    _inherit = "qc.trigger.product_template_line"

    def get_trigger_line_for_product(self, trigger, product, partner=False):
        trigger_lines = super().get_trigger_line_for_product(
            trigger, product, partner=partner
        )
        final_lines = set()
        if self._context.get("before_move_done"):
            for line in trigger_lines:
                if line.before_move_done:
                    final_lines.add(line)
        else:
            for line in trigger_lines:
                if not line.before_move_done:
                    final_lines.add(line)
        return final_lines


class QcTriggerProductCategoryLine(models.Model):
    _inherit = "qc.trigger.product_category_line"

    def get_trigger_line_for_product(self, trigger, product, partner=False):
        trigger_lines = super().get_trigger_line_for_product(
            trigger, product, partner=partner
        )
        final_lines = set()
        if self._context.get("before_move_done"):
            for line in trigger_lines:
                if line.before_move_done:
                    final_lines.add(line)
        else:
            for line in trigger_lines:
                if not line.before_move_done:
                    final_lines.add(line)
        return final_lines


class QcTriggerProductLine(models.Model):
    _inherit = "qc.trigger.product_line"

    def get_trigger_line_for_product(self, trigger, product, partner=False):
        trigger_lines = super().get_trigger_line_for_product(
            trigger, product, partner=partner
        )
        final_lines = set()
        if self._context.get("before_move_done"):
            for line in trigger_lines:
                if line.before_move_done:
                    final_lines.add(line)
        else:
            for line in trigger_lines:
                if not line.before_move_done:
                    final_lines.add(line)
        return final_lines
