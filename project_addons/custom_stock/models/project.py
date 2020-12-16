# Copyright 2012 - 2013 Daniel Reis
# Copyright 2015 - Antiun Ingeniería S.L. - Sergio Teruel
# Copyright 2016 - Tecnativa - Vicent Cubells
# Copyright 2018 - Brain-tec AG - Carlos Jesus Cebrian
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3.0).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Task(models.Model):
    """Added operations  in the Project Task."""

    _inherit = "project.task"

    operation_ids = fields.One2many(
        comodel_name='operations.log.move', inverse_name='task_id',
        string='Material Operations')


class Project(models.Model):
    _inherit = "project.project"
    
    op_count = fields.Integer(compute='_compute_op_count', string="Operations Count")
    
    def _compute_op_count(self):
        op_data = self.env['operations.log.move'].read_group([('project_id', 'in', self.ids)], ['project_id'], ['project_id'])
        result = dict((data['project_id'][0], data['project_id_count']) for data in op_data)
        for project in self:
            project.op_count = result.get(project.id, 0)


