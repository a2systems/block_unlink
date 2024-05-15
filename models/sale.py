from odoo import tools,fields, models, api, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    grupo_ids = fields.One2many(comodel_name='sale.order.grupo',inverse_name='order_id')
    porc_pm = fields.Float('% PM',tracking=True)
    porc_riesgo = fields.Float('% Riesgo',tracking=True)
    discount = fields.Float('% Descuento')
    parent_id = fields.Many2one('sale.order',string='Cotización Original')
    child_ids = fields.One2many(comodel_name='sale.order',inverse_name='parent_id',string='Versiones')
    version = fields.Integer('Versión',compute="_compute_version")
    subactivity_ids = fields.One2many(comodel_name='sale.order.activity',inverse_name='order_id',string='Subactividades')
    sale_invoice_ids = fields.One2many(comodel_name='sale.order.invoice',inverse_name='order_id',string='Cronograma Facturas')
    sale_invoices_amount = fields.Float('Monto cronograma de facturas',compute="_compute_sale_invoices")
    sale_invoices_percent = fields.Float('% cronograma de facturas',compute="_compute_sale_invoices")

    def _compute_sale_invoices(self):
        for rec in self:
            rec.sale_invoices_percent = sum(rec.sale_invoice_ids.mapped('percent'))
            rec.sale_invoices_amount = sum(rec.sale_invoice_ids.mapped('amount'))

    def _compute_version(self):
        for rec in self:
            if rec.child_ids:
                orders = self.env['sale.order'].search([('create_date','>',rec.create_date),('parent_id','=',rec.id)])
                res = len(orders) + 1
            else:
                orders = self.env['sale.order'].search([('create_date','<',rec.create_date),('parent_id','=',rec.parent_id.id)])
                res = len(orders) + 1
            rec.version = res

    def btn_create_version(self):
        self.ensure_one()
        new_order_id = self.copy({'parent_id': self.id})
        new_order_id.action_cancel()

    def _prepare_scat_invoice(self, date=None):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()

        values = {
            'ref': self.client_order_ref or '',
            'move_type': 'out_invoice',
            'narration': self.note,
            'currency_id': self.currency_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'team_id': self.team_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id._get_fiscal_position(self.partner_invoice_id)).id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_user_id': self.user_id.id,
            'payment_reference': self.reference,
            'company_id': self.company_id.id,
            'invoice_line_ids': [],
            'user_id': self.user_id.id,
        }
        if self.journal_id:
            values['journal_id'] = self.journal_id.id
        if date:
            values['invoice_date'] = date
        return values

    def btn_scat_invoices(self):
        self.ensure_one()
        if self.invoice_ids:
            raise ValidationError('Facturas ya creadas')
        if self.state in ['draft','cancel']:
            raise ValidationError('Estado no permitido')
        if not self.sale_invoice_ids:
            raise ValidationError('No ingreso cronograma de facturación')
        for inv_line in self.sale_invoice_ids:
            if not inv_line.percent and inv_line.amount:
                inv_line.percent = (inv_line.amount / inv_line.order_id.amount_total) * 100
        if self.sale_invoices_percent > 99:
            raise ValidationError('Cronograma incorrecto')
        for inv_line in self.sale_invoice_ids:
            vals = self._prepare_scat_invoice(inv_line.date)
            if inv_line.amount:
                percent = (inv_line.amount / self.amount_total) * 100
            else:
                percent = inv_line.percent
            invoice_line_ids = self._prepare_scat_invoice_lines(self.order_line,percent=percent)
            #for order_line in self.order_line:
            #    invoice_line_ids.append((order_line._prepare_scat_invoice_line(percent=inv_line.percent)))
            vals['invoice_line_ids'] = invoice_line_ids
            #raise ValidationError(str(invoice_line_ids))
            move_id = self.env['account.move'].create(vals)
            inv_line.move_id = move_id.id

    def _prepare_scat_invoice_lines(self, order_line, percent):
        invoice_lines = []
        for o_line in order_line:
            invoice_lines.append((0,None,o_line._prepare_scat_invoice_line(percent)))
        return invoice_lines

    def btn_add_discount(self):
        self.ensure_one()
        vals = {
            'order_id': self.id,
            }
        wizard_id = self.env['sale.order.discount.wizard'].create(vals)
        res = {
            'name': _('Agregar descuento global'),
            'res_model': 'sale.order.discount.wizard',
            'view_mode': 'form',
            'res_id': wizard_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
        return res

    def action_confirm(self):
        for rec in self:
            if not rec.sale_invoice_ids:
                raise ValidationError('Debe ingresar un cronograma de facturación')
            res = super(SaleOrder, self).action_confirm()
            for grupo_id in rec.grupo_ids:
                grupo_id.unlink()
            grupos = {}
            for order_line in rec.order_line:
                if not order_line.display_type and order_line.grupo:
                    if order_line.grupo not in grupos:
                        grupos[order_line.grupo] = order_line.price_subtotal
                    else:
                        grupos[order_line.grupo] = grupos[order_line.grupo] + order_line.price_subtotal
            if grupos:
                for key,val in grupos.items():
                    vals = {
                            'order_id': rec.id,
                            'grupo': key,
                            'amount': val,
                            }
                    grupo_id = self.env['sale.order.grupo'].create(vals)
        return res

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _compute_grupo(self):
        for rec in self:
            res = ''
            domain = [('sequence','<',rec.sequence),('order_id','=',rec.order_id.id),('display_type','=','line_section')]
            prev_line = self.env['sale.order.line'].search(domain,order='sequence desc',limit=1)
            if prev_line and prev_line.name:
                res = prev_line.name
            rec.grupo = res

    @api.model
    def create(self, vals):
        res = super(SaleOrderLine, self).create(vals)
        if res.product_id.product_activity_ids:
            for prod_activity in res.product_id.product_activity_ids:
                vals_act = {
                        'order_id': res.order_id.id,
                        'order_line_id': res.id,
                        'name': prod_activity.name,
                        'amount': prod_activity.amount * res.product_uom_qty,
                        'uom_id': prod_activity.uom_id.id,
                        }
                act_id = self.env['sale.order.activity'].create(vals_act)
        return res

    def write(self, vals):
        res = super(SaleOrderLine, self).write(vals)
        if 'product_id' in vals or 'product_uom_qty' in vals:
            for rec in self:
                subactivities = self.env['sale.order.activity'].search([('order_line_id','=',rec.id)])
                if subactivities:
                    subactivities.unlink()
                if rec.product_id.product_activity_ids:
                    for prod_activity in rec.product_id.product_activity_ids:
                        vals_act = {
                            'order_id': rec.order_id.id,
                            'order_line_id': rec.id,
                            'name': prod_activity.name,
                            'amount': prod_activity.amount * rec.product_uom_qty,
                            'uom_id': prod_activity.uom_id.id,
                            }
                        act_id = self.env['sale.order.activity'].create(vals_act)
        return res

    def unlink(self):
        for rec in self:
            subactivities = self.env['sale.order.activity'].search([('order_line_id','=',rec.id)])
            if subactivities:
                subactivities.unlink()
        return super(SaleOrderLine, self).unlink()

    def _prepare_scat_invoice_line(self, percent = 0):
        """Prepare the values to create the new invoice line for a sales order line.

        :param optional_values: any parameter that should be added to the returned invoice line
        :rtype: dict
        """
        self.ensure_one()
        res = {
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit * percent / 100,
            #'tax_ids': [(6,0,self.tax_id.ids)],
            #'account_id': self.product_id.property_account_income_id.id,
        }
        return res

    grupo = fields.Char('Grupo',compute=_compute_grupo)
    amount_pm = fields.Float('Monto PM')
    amount_riesgo = fields.Float('Monto Riesgo')
    old_price_unit = fields.Float('Precio Unitario Original')

