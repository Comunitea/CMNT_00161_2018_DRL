# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class ProductProduct(models.Model):

    _inherit = "product.product"

    @api.model
    def get_milk_product_by_name(self, name):
        if name == "*":
            # Retornamos todos los productos
            ids = [
                int(
                    self.env["ir.config_parameter"].get_param(
                        "milk_planning.product_raw_milk"
                    )
                ),
                int(
                    self.env["ir.config_parameter"].get_param(
                        "milk_planning.product_raw_milk_do"
                    )
                ),
                int(
                    self.env["ir.config_parameter"].get_param(
                        "milk_planning.product_raw_milk_100"
                    )
                ),
                int(
                    self.env["ir.config_parameter"].get_param(
                        "milk_planning.product_skimmed_milk"
                    )
                ),
                int(
                    self.env["ir.config_parameter"].get_param(
                        "milk_planning.product_cream"
                    )
                ),
            ]
            return self.env["product.product"].browse(ids)
        elif name == "milk":
            # Retornamos los productos leche cruda y leche desnatada
            ids = [
                int(
                    self.env["ir.config_parameter"].get_param(
                        "milk_planning.product_raw_milk"
                    )
                ),
                int(
                    self.env["ir.config_parameter"].get_param(
                        "milk_planning.product_raw_milk_do"
                    )
                ),
                int(
                    self.env["ir.config_parameter"].get_param(
                        "milk_planning.product_raw_milk_100"
                    )
                ),
                int(
                    self.env["ir.config_parameter"].get_param(
                        "milk_planning.product_skimmed_milk"
                    )
                ),
            ]
            return self.env["product.product"].browse(ids)
        else:
            # Buscamos por valor de parametro
            id = int(
                self.env["ir.config_parameter"].get_param(
                    "milk_planning.product_%s" % name
                )
            )
            return self.env["product.product"].browse(id)
