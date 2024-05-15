from odoo import tools,fields, models, api, _
from odoo.exceptions import ValidationError
from odoo import api, models

class BaseModelExtend(models.AbstractModel):
    _inherit = 'base'

    def unlink(self):
        raise ValidationError('No se permite esta operacion')
