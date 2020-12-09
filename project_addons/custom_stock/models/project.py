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

