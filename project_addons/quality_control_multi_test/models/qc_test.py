# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class QcTest(models.Model):

    _inherit = "qc.test"

    no_cases = fields.\
        Selection([('1', 'One column'), ('2', 'Two columns'),
                   ('3', 'Three columns'), ('4', 'Four columns'),
                   ('5', 'Five columns'), ('6', 'Six columns')], "No of Cases",
                  required=True, default='1')

