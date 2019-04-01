# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields

class ResCompany(models.Model):

    _inherit = "res.company"

    NRC=fields.Integer(string="NRC", help="Número de Referencia Completo")
    NR_LetraQ=fields.Integer(string="NR Letra Q")
