from odoo import tools,fields, models, api, _
from odoo.exceptions import ValidationError

class SaleOrderInvoice(models.Model):
    _name = 'sale.order.invoice'

    order_id = fields.Many2one('sale.order','Pedido')
    move_id = fields.Many2one('account.move','Factura')
    date = fields.Date('Fecha Factura')
    amount = fields.Float('Monto')
    percent = fields.Float('%')
