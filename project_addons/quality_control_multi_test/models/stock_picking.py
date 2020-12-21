# Copyright 2020 Comunitea
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError



class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
 
    @api.multi
    def action_done(self):
        res = super().action_done()
        
        valid = all([x.valid_for_move for x in qc_inspections_ids])
        
        if not valid:
            raise ValidationError(_('Before validate th picking you need to fill at least on inspecion . You can need to geneate tests'))

        return res
