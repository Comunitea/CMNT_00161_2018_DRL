# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class QcTestQuestion(models.Model):

    _inherit = "qc.test.question"

    result_type = fields.\
        Selection([('all', 'All valid'), ('one', 'One valid'),
                   ('sum', 'Sum valid'), ('avg', 'Average valid')],
                  "Result type", required=True, default='one')
