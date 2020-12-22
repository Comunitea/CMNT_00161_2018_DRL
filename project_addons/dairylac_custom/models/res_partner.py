# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, fields, api


class ResPartner(models.Model):

    _inherit = "res.partner"

    driver = fields.Boolean("Driver")
    legacy_account_code = fields.Char("Código contable (previo)")

    @api.multi
    def _get_name(self):
        res = super()._get_name()
        if self.type == 'contact':
            if self.parent_id:
                res = u'☺ %s'%res
            else:
                res = u'⚐ %s'%res

        if self.type == 'private':
            res = u'⚿ %s' % res

        if self.type == 'invoice':
            res =  u'$ %s' % res
        if self.type == 'delivery':
            res = u'⛟ %s' % res
        return res
