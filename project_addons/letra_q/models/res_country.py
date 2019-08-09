# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCountry(models.Model):

    _inherit = 'res.country'

    letra_q_code = fields.Char()
