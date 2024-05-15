from odoo import tools,fields, models, api, _
from odoo.exceptions import ValidationError

class UomUom(models.Model):
    _inherit = 'uom.uom'

    scat_code = fields.Char('Codigo SCAT')
