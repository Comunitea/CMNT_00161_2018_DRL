# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields


class ResCompany(models.Model):

    _inherit = "res.company"

    nrc = fields.Integer(string="NRC", help="Número de Referencia Completo")
    nr_letraq = fields.Integer(string="NR Letra Q")
