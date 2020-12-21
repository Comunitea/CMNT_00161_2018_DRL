# © 2019 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _
from .weight_registry import REGISTRY_TYPE
from odoo.exceptions import ValidationError

class ProductUom(models.Model):

    _inherit = 'uom.uom'    

    template_id = fields.Many2one ('product.template')


    # @api.model
    # def get_weight_factor(self, template_id):
    #     return self.env['product.uom.factor'].get_weight_factor(template_id, self.id)

class ProductTemplate(models.Model):

    _inherit = "product.template"

    uom_po_id_category_id = fields.Many2one(related='uom_po_id.category_id')
    weight_control = fields.Boolean('Requires weight control', help="For filter in weight control links", default=False)
   

    # @api.model
    # def get_weight_factor(self, uom_id):
    #     return self.env['product.uom.factor'].get_weight_factor(self, uom_id)
