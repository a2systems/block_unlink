from odoo import tools,fields, models, api, _
from odoo.exceptions import ValidationError

class ProductActivity(models.Model):
    _name = 'product.activity'
    _description = 'product.activity'

    def _default_uom_id(self):
        return self.env.ref('uom.product_uom_hour').id
    
    @api.model
    def create(self, vals):
        res = super(ProductActivity, self).create(vals)
        valor_hora = res.product_tmpl_id.categ_id.valor_hora
        amount = res.product_tmpl_id.trabajo
        product_tmpl_id = res.product_tmpl_id
        product_tmpl_id.list_price = amount * valor_hora
        return res

    def write(self,vals):
        res = super(ProductActivity, self).write(vals)
        for rec in self:
            valor_hora = rec.product_tmpl_id.categ_id.valor_hora
            amount = rec.product_tmpl_id.trabajo
            product_tmpl_id = rec.product_tmpl_id
            product_tmpl_id.list_price = amount * valor_hora
        return res

    def unlink(self):
        for rec in self:
            valor_hora = rec.product_tmpl_id.categ_id.valor_hora
            amount = 0
            uom_hour = self.env.ref('uom.product_uom_hour')
            for activity in rec.product_tmpl_id.product_activity_ids:
                if activity.id not in self.ids:
                    amount = amount + activity.uom_id._compute_quantity(activity.amount,uom_hour)
            product_tmpl_id = rec.product_tmpl_id
            product_tmpl_id.list_price = amount * valor_hora
        res = super(ProductActivity, self).unlink()
        return res


    product_tmpl_id = fields.Many2one('product.template',string='Producto')
    name = fields.Char('Nombre')
    amount = fields.Float('Cantidad')
    uom_id = fields.Many2one('uom.uom',string='Unidad de Medida',default=_default_uom_id)

