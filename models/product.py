from odoo import tools,fields, models, api, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _compute_trabajo(self):
        for rec in self:
            res = 0
            for activity in rec.product_activity_ids:
                uom_hour = self.env.ref('uom.product_uom_hour')
                res = res + activity.uom_id._compute_quantity(activity.amount,uom_hour)
            rec.trabajo = res


    trabajo = fields.Float('Trabajo',compute=_compute_trabajo)
    product_activity_ids = fields.One2many(comodel_name='product.activity',inverse_name='product_tmpl_id',string='Subactividades')
