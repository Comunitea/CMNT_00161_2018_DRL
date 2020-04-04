# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api


class PurchaseOrderLine(models.Model):

    _inherit = "purchase.order.line"

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(PurchaseOrderLine, self).onchange_product_id()


        if self:
            category_id = self.product_id.uom_id.category_id.id
            tmpl_id = self.product_id.product_tmpl_id.id
            if not res.get('domain', False):
                res.update(domain = {})
            if not res['domain'].get('product_uom', False):
                res.update(product_uom = '')
            res['domain']['product_uom'] = [('category_id', '=', category_id), '|', ('template_id', '=', False), ('template_id','=', tmpl_id)]

        return res
