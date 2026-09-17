from unittest.mock import MagicMock, patch

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.sale.tests.common import SaleCommon


@tagged('post_install', '-at_install')
class TestPriceLevels(SaleCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref('product.decimal_price').digits = 2
        cls.template = cls.env['product.template'].create({
            'name': "Price Level Product",
            'is_storable': True,
            'standard_price': 100.0,
            'list_price': 150.0,
            'taxes_id': [Command.clear()],
        })
        cls.variant = cls.template.product_variant_id

    def _set_margins(self, public, wholesale, minimum):
        self.template.write({
            'list_price_margin': public,
            'wholesale_price_margin': wholesale,
            'min_price_margin': minimum,
        })

    # --- product ------------------------------------------------------------------------------

    def test_form_each_margin_computes_its_own_price(self):
        with Form(self.template) as form:
            form.list_price_margin = 1.5
            self.assertEqual(form.list_price, 101.5)
            self.assertEqual(form.wholesale_price, 0.0)
            form.wholesale_price_margin = 10
            self.assertEqual(form.wholesale_price, 110.0)
            self.assertEqual(form.list_price, 101.5)
            form.min_price_margin = 5
        self.assertEqual(self.template.list_price, 101.5)
        self.assertEqual(self.template.wholesale_price, 110.0)
        self.assertEqual(self.template.min_price, 105.0)

    def test_zero_margin_means_price_equals_cost(self):
        self.template.wholesale_price_margin = 10
        self.template.wholesale_price_margin = 0
        self.assertEqual(self.template.wholesale_price, 100.0)

    def test_manual_price_is_kept(self):
        with Form(self.template) as form:
            form.wholesale_price_margin = 10
            form.wholesale_price = 123.45
        self.assertEqual(self.template.wholesale_price, 123.45)
        # a cost change never overwrites prices
        self.template.standard_price = 200.0
        self.assertEqual(self.template.wholesale_price, 123.45)
        self.assertEqual(self.template.list_price, 150.0)

    def test_write_margin_without_price_derives_only_that_price(self):
        self.template.write({'min_price_margin': 2.25})
        self.assertEqual(self.template.min_price, 102.25)
        self.assertEqual(self.template.list_price, 150.0)
        self.assertEqual(self.template.wholesale_price, 0.0)

    def test_price_follows_product_price_precision(self):
        self.template.wholesale_price_margin = 0.333
        self.assertEqual(self.template.wholesale_price, 100.33)

    def test_recompute_from_cost(self):
        self._set_margins(50, 20, 5)
        self.template.write({'list_price': 999.0, 'standard_price': 200.0})
        self.template.action_recompute_prices_from_margin()
        self.assertEqual(self.template.list_price, 300.0)
        self.assertEqual(self.template.wholesale_price, 240.0)
        self.assertEqual(self.template.min_price, 210.0)

    def test_multi_variant_template_refuses_cost_based_prices(self):
        attribute = self.env['product.attribute'].create({
            'name': "Size",
            'value_ids': [Command.create({'name': "S"}), Command.create({'name': "L"})],
        })
        template = self.env['product.template'].create({
            'name': "Two Variants",
            'attribute_line_ids': [Command.create({
                'attribute_id': attribute.id,
                'value_ids': [Command.set(attribute.value_ids.ids)],
            })],
        })
        with self.assertRaises(UserError):
            template.write({'wholesale_price_margin': 10})
        with self.assertRaises(UserError):
            template.action_recompute_prices_from_margin()

    # --- sale order line ----------------------------------------------------------------------

    def test_sale_line_price_levels_and_selection_survives_quantity_change(self):
        self._set_margins(50, 20, 5)
        order = self.empty_order
        order.order_line = [Command.create({'product_id': self.variant.id, 'product_uom_qty': 1})]
        line = order.order_line
        self.assertEqual(line.price_unit, 150.0)
        self.assertEqual(
            (line.price_level_public, line.price_level_wholesale, line.price_level_min),
            (150.0, 120.0, 105.0),
        )
        line.price_unit = line.price_level_wholesale
        line.product_uom_qty = 5
        self.assertEqual(line.price_unit, 120.0)
        self.assertEqual(line.price_subtotal, 600.0)

    def test_sale_line_price_levels_follow_line_uom(self):
        self._set_margins(50, 20, 5)
        order = self.empty_order
        order.order_line = [Command.create({
            'product_id': self.variant.id,
            'product_uom': self.env.ref('uom.product_uom_dozen').id,
        })]
        self.assertEqual(order.order_line.price_level_wholesale, 1440.0)

    def test_price_included_tax_is_adapted_by_fiscal_position(self):
        self._set_margins(10, 10, 10)
        tax_included = self.env['account.tax'].create({
            'name': "15% incl", 'amount': 15, 'price_include_override': 'tax_included',
        })
        tax_excluded = self.env['account.tax'].create({'name': "0%", 'amount': 0})
        self.template.taxes_id = tax_included
        fiscal_position = self.env['account.fiscal.position'].create({
            'name': "Export",
            'tax_ids': [Command.create({
                'tax_src_id': tax_included.id, 'tax_dest_id': tax_excluded.id,
            })],
        })
        order = self.empty_order
        order.fiscal_position_id = fiscal_position
        order.order_line = [Command.create({'product_id': self.variant.id})]
        # 110 tax included at 15% -> 95.65 once mapped to a 0% tax, exactly like price_unit
        self.assertEqual(order.order_line.price_level_wholesale, order.order_line.price_unit)
        self.assertAlmostEqual(order.order_line.price_level_wholesale, 95.65, places=2)

    # --- catalog ------------------------------------------------------------------------------

    def _catalog_update(self, order, product, quantity, **kwargs):
        with patch('odoo.addons.sale.models.sale_order.request', MagicMock()):
            return order._update_order_line_info(product.id, quantity, **kwargs)

    def test_catalog_info_prices_and_location_quantities(self):
        self._set_margins(50, 20, 5)
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1)
        shelf = self.env['stock.location'].create({
            'name': "Shelf A", 'location_id': warehouse.lot_stock_id.id,
        })
        self.env['stock.location'].create({
            'name': "Shelf Empty", 'location_id': warehouse.lot_stock_id.id,
        })
        Quant = self.env['stock.quant']
        Quant._update_available_quantity(self.variant, warehouse.lot_stock_id, 7)
        Quant._update_available_quantity(self.variant, shelf, 3)

        info = self.empty_order._get_product_catalog_order_line_info(
            [self.variant.id, self.service_product.id])

        data = info[self.variant.id]
        self.assertEqual(
            [(level['key'], level['price']) for level in data['priceLevels']],
            [('public', 150.0), ('wholesale', 120.0), ('min', 105.0)],
        )
        self.assertFalse(data['priceLevel'])
        self.assertEqual(
            [(loc['name'], loc['quantity']) for loc in data['locationQuantities']],
            [(warehouse.lot_stock_id.display_name, 7.0), (shelf.display_name, 3.0)],
        )
        self.assertEqual(
            sum(loc['quantity'] for loc in data['locationQuantities']),
            self.variant.with_context(warehouse_id=warehouse.id).qty_available,
        )
        self.assertNotIn('locationQuantities', info[self.service_product.id])

    def test_catalog_update_with_price_level(self):
        self._set_margins(50, 20, 5)
        order = self.empty_order
        price = self._catalog_update(order, self.variant, 2, price_level='min')
        self.assertEqual(price, 105.0)
        self.assertEqual(order.order_line.price_unit, 105.0)

        self._catalog_update(order, self.variant, 4, price_level='min')
        self.assertEqual(order.order_line.product_uom_qty, 4)
        self.assertEqual(order.order_line.price_unit, 105.0)

        info = order._get_product_catalog_order_line_info([self.variant.id])
        self.assertEqual(info[self.variant.id]['priceLevel'], 'min')

        # without a level the catalog keeps the standard behaviour
        self._catalog_update(order, self.variant, 0)
        self.assertFalse(order.order_line)
        self._catalog_update(order, self.variant, 1)
        self.assertEqual(order.order_line.price_unit, 150.0)

    def test_catalog_rejects_unknown_price_level(self):
        with self.assertRaises(UserError):
            self._catalog_update(self.empty_order, self.variant, 1, price_level='vip')
