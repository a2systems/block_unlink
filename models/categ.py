from odoo import tools,fields, models, api, _
from odoo.exceptions import ValidationError

class ProductCategory(models.Model):
    _inherit = 'product.category'

    valor_hora = fields.Float('Valor Hora')
