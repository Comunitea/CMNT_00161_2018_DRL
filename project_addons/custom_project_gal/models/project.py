# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, fields, _


class Task(models.Model):
    _inherit = "project.task"

    def action_subtask(self):
        ctx = self.env.context.copy()
        ctx.update({
            'search_default_parent_only': False,
        })
        self.env.context = ctx
        return super().action_subtask()
    