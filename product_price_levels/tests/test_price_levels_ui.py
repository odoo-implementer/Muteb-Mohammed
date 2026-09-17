from odoo import Command
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestPriceLevelsUi(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref('product.decimal_price').digits = 2
        warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.env.company.id)], limit=1)
        shelf = cls.env['stock.location'].create({
            'name': "Shelf Tour", 'location_id': warehouse.lot_stock_id.id,
        })
        template = cls.env['product.template'].create({
            'name': "PPL Tour Widget",
            'is_storable': True,
            'standard_price': 100.0,
            'list_price': 150.0,
            'taxes_id': [Command.clear()],
        })
        template.write({
            'list_price_margin': 50, 'wholesale_price_margin': 20, 'min_price_margin': 1.5,
        })
        product = template.product_variant_id
        cls.env['stock.quant']._update_available_quantity(product, warehouse.lot_stock_id, 7)
        cls.env['stock.quant']._update_available_quantity(product, shelf, 3)
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.env['res.partner'].create({'name': "PPL Tour Customer"}).id,
            'order_line': [Command.create({'product_id': product.id, 'product_uom_qty': 2})],
        })

    def test_order_line_price_dropdown(self):
        self.start_tour(
            f"/odoo/action-sale.action_quotations/{self.order.id}", 'product_price_levels_line_dropdown', login='admin')
        self.assertEqual(self.order.order_line.price_unit, 120.0)

    def test_catalog_price_levels_and_locations(self):
        self.start_tour(
            f"/odoo/action-sale.action_quotations/{self.order.id}", 'product_price_levels_catalog', login='admin')
        self.assertEqual(self.order.order_line.product_uom_qty, 3)
        self.assertEqual(self.order.order_line.price_unit, 101.5)
