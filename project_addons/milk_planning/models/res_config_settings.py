# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from ast import literal_eval
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_raw_milk = fields.Many2one('product.product')
    product_raw_milk_do = fields.Many2one('product.product')
    product_raw_milk_100 = fields.Many2one('product.product')
    product_skimmed_milk = fields.Many2one('product.product')
    product_cream = fields.Many2one('product.product')

    @api.model
    def get_values(self):
        res = super().get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res.update(
            product_raw_milk=int(get_param(
                'milk_planning.product_raw_milk', default=False
            )),
            product_raw_milk_do=int(get_param(
                'product_milk_do.product_raw_milk', default=False
            )),
            product_raw_milk_100=int(get_param(
                'product_milk_100.product_raw_milk', default=False
            )),
            product_skimmed_milk=int(get_param(
                'milk_planning.product_skimmed_milk', default=False
            )),
            product_cream=int(get_param(
                'milk_planning.product_cream', default=False
            )),
        )

        return res

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param

        set_param('milk_planning.product_raw_milk', self.product_raw_milk.id)
        set_param('milk_planning.product_raw_milk_do',
                  self.product_raw_milk_do.id)
        set_param('milk_planning.product_raw_milk_100',
                  self.product_raw_milk_100.id)
        set_param('milk_planning.product_skimmed_milk', self.product_skimmed_milk.id)
        set_param('milk_planning.product_cream', self.product_cream.id)
