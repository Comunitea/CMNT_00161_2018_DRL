# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    species_q = fields.Selection(
        [('1', 'vacuno'),
         ('2', 'ovino'),
         ('3', 'caprino')],
        'Milk Species', required=False)
    subject_q = fields. Boolean('Subject to Letra Q')
