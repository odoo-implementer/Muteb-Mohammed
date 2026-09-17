from odoo import _, fields, models

# price level key -> product price field
PRICE_LEVEL_FIELDS = {
    'public': 'list_price',
    'wholesale': 'wholesale_price',
    'min': 'min_price',
}


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_price_level_labels(self):
        return {
            'public': _("Public Price"),
            'wholesale': _("Wholesale Price"),
            'min': _("Minimum Price"),
        }

    def _get_sale_price_levels(self, uom=None, currency=None, company=None, date=False,
                               fiscal_position=None):
        """ The three price levels of the product, prepared the same way sale order lines prepare
        the pricelist price: converted to `uom` and `currency`, and adapted to the taxes mapped by
        `fiscal_position` when the product taxes are price-included.

        :return: {level_key: price}
        """
        self.ensure_one()
        company = company or self.env.company
        product = self.with_company(company)
        date = date or fields.Date.context_today(self)
        product_taxes = product.taxes_id._filter_taxes_by_company(company)
        levels = {}
        for level, price_field in PRICE_LEVEL_FIELDS.items():
            price = product._price_compute(
                price_field, uom=uom, currency=currency, company=company, date=date,
            )[product.id]
            levels[level] = product._get_tax_included_unit_price_from_price(
                price, product_taxes=product_taxes, fiscal_position=fiscal_position,
            )
        return levels
