from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_round

# price field -> margin field. The public price is the standard sales price (list_price).
PRICE_MARGIN_FIELDS = {
    'list_price': 'list_price_margin',
    'wholesale_price': 'wholesale_price_margin',
    'min_price': 'min_price_margin',
}


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    list_price_margin = fields.Float(
        string="Public Price Margin (%)", digits=(16, 4),
        help="Public price = cost + cost x margin / 100.")
    wholesale_price = fields.Float(
        string="Wholesale Price", digits='Product Price', tracking=True)
    wholesale_price_margin = fields.Float(
        string="Wholesale Price Margin (%)", digits=(16, 4),
        help="Wholesale price = cost + cost x margin / 100.")
    min_price = fields.Float(
        string="Minimum Price", digits='Product Price', tracking=True)
    min_price_margin = fields.Float(
        string="Minimum Price Margin (%)", digits=(16, 4),
        help="Minimum price = cost + cost x margin / 100.")

    # Prices are only derived when their own margin changes (or on explicit recompute), so a
    # manual price is never overwritten by cost updates (AVCO/FIFO valuation) nor at install.

    def _get_price_from_margin(self, margin):
        """ cost + cost * margin / 100, in the template currency, rounded to 'Product Price'. """
        self.ensure_one()
        cost = self.standard_price
        if self.cost_currency_id != self.currency_id:
            cost = self.cost_currency_id._convert(
                cost, self.currency_id, self.env.company, fields.Date.context_today(self))
        digits = self.env['decimal.precision'].precision_get('Product Price')
        return float_round(cost * (1.0 + margin / 100.0), precision_digits=digits)

    def _check_single_variant_cost(self):
        multi = self.filtered(lambda t: t.product_variant_count > 1)
        if multi:
            raise UserError(_(
                "Prices cannot be computed from the cost of a product with several variants, "
                "each variant has its own cost:\n%s",
                "\n".join(multi.mapped('display_name')),
            ))

    @api.onchange('list_price_margin')
    def _onchange_list_price_margin(self):
        return self._apply_margin_onchange('list_price')

    @api.onchange('wholesale_price_margin')
    def _onchange_wholesale_price_margin(self):
        return self._apply_margin_onchange('wholesale_price')

    @api.onchange('min_price_margin')
    def _onchange_min_price_margin(self):
        return self._apply_margin_onchange('min_price')

    def _apply_margin_onchange(self, price_field):
        for template in self:
            if template.product_variant_count > 1:
                return {'warning': {
                    'title': _("Several variants"),
                    'message': _("The price was not computed: each variant has its own cost."),
                }}
            template[price_field] = template._get_price_from_margin(
                template[PRICE_MARGIN_FIELDS[price_field]])

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)
        for template, vals in zip(templates, vals_list):
            template._apply_margins_from_vals(vals)
        return templates

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('skip_price_margin') and any(
            margin in vals for margin in PRICE_MARGIN_FIELDS.values()
        ):
            for template in self:
                template._apply_margins_from_vals(vals)
        return res

    def _apply_margins_from_vals(self, vals):
        """ A margin written without its price (import, RPC) derives the price. A price written
        together with its margin (form save, manual edit) is kept as given. """
        self.ensure_one()
        to_compute = [
            price for price, margin in PRICE_MARGIN_FIELDS.items()
            if margin in vals and price not in vals
        ]
        if not to_compute:
            return
        self._check_single_variant_cost()
        self.with_context(skip_price_margin=True).write({
            price: self._get_price_from_margin(self[PRICE_MARGIN_FIELDS[price]])
            for price in to_compute
        })

    def action_recompute_prices_from_margin(self):
        """ Re-derive the three prices from the current cost and margins (overwrites manual prices). """
        self._check_single_variant_cost()
        for template in self:
            template.with_context(skip_price_margin=True).write({
                price: template._get_price_from_margin(template[margin])
                for price, margin in PRICE_MARGIN_FIELDS.items()
            })
        return True
