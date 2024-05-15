from odoo import tools,fields, models, api, _
from odoo.exceptions import ValidationError

class SaleOrderActivity(models.Model):
    _name = 'sale.order.activity'

    order_id = fields.Many2one('sale.order')
    order_line_id = fields.Many2one('sale.order.line')
    name = fields.Char('Subactividad')
    amount = fields.Float('Monto')
    uom_id = fields.Many2one('uom.uom','Unidad de medida')
