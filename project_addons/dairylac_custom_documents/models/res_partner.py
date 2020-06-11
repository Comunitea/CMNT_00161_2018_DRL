# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, fields


class ResPartner(models.Model):

    _inherit = "res.partner"

    code_dac = fields.Char("Código DAC")
    rgseea = fields.Char("RGSEEA")
