{
    'name': 'Product Price Levels',
    'version': '18.0.1.0.0',
    'category': 'Sales/Sales',
    'summary': 'Public / wholesale / minimum prices from cost margins, on quotation lines and in the catalog',
    'description': """
Product Price Levels
====================
* Three price levels per product (public = standard sales price, wholesale, minimum),
  each computed from the product cost and its own margin percentage.
* Quotation line unit price offers the three levels as a dropdown (manual typing stays possible).
* The sale order product catalog shows the three selectable prices and the on-hand
  quantity of every internal location.
""",
    'author': 'TodoOps',
    'license': 'LGPL-3',
    'depends': ['sale_stock'],
    'data': [
        'data/ir_actions_server.xml',
        'views/product_template_views.xml',
        'views/product_catalog_views.xml',
        'views/sale_order_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'product_price_levels/static/src/**/*',
        ],
        'web.assets_tests': [
            'product_price_levels/static/tests/tours/**/*',
        ],
    },
    'installable': True,
    'application': False,
}
