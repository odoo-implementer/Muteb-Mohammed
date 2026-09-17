from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    price_level_public = fields.Float(
        string="Public Price Level", compute='_compute_price_levels', digits='Product Price')
    price_level_wholesale = fields.Float(
        string="Wholesale Price Level", compute='_compute_price_levels', digits='Product Price')
    price_level_min = fields.Float(
        string="Minimum Price Level", compute='_compute_price_levels', digits='Product Price')

    @api.depends('product_id', 'product_uom', 'currency_id', 'company_id',
                 'order_id.date_order', 'order_id.fiscal_position_id')
    def _compute_price_levels(self):
        for line in self:
            if not line.product_id or line.display_type:
                line.price_level_public = line.price_level_wholesale = line.price_level_min = 0.0
                continue
            levels = line.product_id._get_sale_price_levels(
                uom=line.product_uom,
                currency=line.currency_id or line.company_id.currency_id,
                company=line.company_id or self.env.company,
                date=line.order_id.date_order,
                fiscal_position=line.order_id.fiscal_position_id,
            )
            line.price_level_public = levels['public']
            line.price_level_wholesale = levels['wholesale']
            line.price_level_min = levels['min']

    def _get_price_levels(self):
        self.ensure_one()
        return {
            'public': self.price_level_public,
            'wholesale': self.price_level_wholesale,
            'min': self.price_level_min,
        }
