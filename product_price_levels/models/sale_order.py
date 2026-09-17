from odoo import _, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

from .product_product import PRICE_LEVEL_FIELDS


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _get_product_catalog_order_line_info(self, product_ids, child_field=False, **kwargs):
        """ Add the three price levels and the per-location on-hand quantities to the catalog. """
        # super() consumes `product_ids` (it removes the products already in the order)
        info = super()._get_product_catalog_order_line_info(
            list(product_ids), child_field=child_field, **kwargs)
        products = self.env['product.product'].browse(list(info))
        location_quantities = self._get_product_catalog_location_quantities(products)
        for product in products:
            lines = self.order_line.filtered(
                lambda line: line.product_id == product and not line.display_type)
            info[product.id].update(self._get_product_catalog_price_level_data(product, lines))
            if product.id in location_quantities:
                info[product.id]['locationQuantities'] = location_quantities[product.id]
        return info

    def _get_product_catalog_price_level_data(self, product, lines):
        labels = product._get_price_level_labels()
        if len(lines) == 1:
            levels = lines._get_price_levels()
            selected = next(
                (level for level, price in levels.items()
                 if not self.currency_id.compare_amounts(price, lines.price_unit)),
                False,
            )
        else:
            levels = product._get_sale_price_levels(
                currency=self.currency_id,
                company=self.company_id,
                date=self.date_order,
                fiscal_position=self.fiscal_position_id,
            )
            selected = False
        return {
            'priceLevels': [
                {'key': level, 'label': labels[level], 'price': levels[level]}
                for level in PRICE_LEVEL_FIELDS
            ],
            'priceLevel': selected,
        }

    def _get_product_catalog_location_quantities(self, products):
        """ On-hand quantity per internal location of the order company, one query for all
        storable products shown on the catalog page. Locations without stock are omitted.

        :return: {product_id: [{'id', 'name', 'quantity', 'uom'}]}
        """
        storable = products.filtered('is_storable')
        result = {product.id: [] for product in storable}
        if not storable:
            return result
        groups = self.env['stock.quant']._read_group(
            [
                ('product_id', 'in', storable.ids),
                ('location_id.usage', '=', 'internal'),
                ('company_id', '=', self.company_id.id),
            ],
            ['product_id', 'location_id'],
            ['quantity:sum'],
        )
        for product, location, quantity in groups:
            if float_is_zero(quantity, precision_rounding=product.uom_id.rounding):
                continue
            result[product.id].append({
                'id': location.id,
                'name': location.display_name,
                'quantity': quantity,
                'uom': product.uom_id.name,
            })
        for locations in result.values():
            locations.sort(key=lambda location: location['name'])
        return result

    def _update_order_line_info(self, product_id, quantity, price_level=False, **kwargs):
        price = super()._update_order_line_info(product_id, quantity, **kwargs)
        if not price_level or quantity <= 0:
            return price
        if price_level not in PRICE_LEVEL_FIELDS:
            raise UserError(_("Unknown price level: %s", price_level))
        line = self.order_line.filtered(lambda sol: sol.product_id.id == product_id)
        line.ensure_one()
        if line.qty_invoiced > 0:
            raise UserError(_("The price of an invoiced line cannot be changed."))
        line.price_unit = line._get_price_levels()[price_level]
        return line.price_unit * (1 - (line.discount or 0.0) / 100.0)
