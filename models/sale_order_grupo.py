from odoo import tools,fields, models, api, _
from odoo.exceptions import ValidationError

class SaleOrderGrupo(models.Model):
    _name = 'sale.order.grupo'

    order_id = fields.Many2one('sale.order')
    grupo = fields.Char('Grupo')
    amount = fields.Float('Monto')
