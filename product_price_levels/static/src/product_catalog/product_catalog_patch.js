/** @odoo-module */
import { useSubEnv } from "@odoo/owl";
import { ProductCatalogKanbanRecord } from "@product/product_catalog/kanban_record";
import { ProductCatalogSaleOrderLine } from "@sale_stock/product_catalog/sale_order_line/sale_order_line";
import { patch } from "@web/core/utils/patch";
import { formatFloat, formatMonetary } from "@web/views/fields/formatters";

patch(ProductCatalogKanbanRecord.prototype, {
    setup() {
        super.setup();
        useSubEnv({ selectPriceLevel: this.selectPriceLevel.bind(this) });
    },

    /**
     * Select a price level: applied right away when the product is already in the order,
     * otherwise used when the product gets added.
     */
    selectPriceLevel(level) {
        if (this.productCatalogData.readOnly) {
            return;
        }
        this.productCatalogData.priceLevel = level.key;
        this.productCatalogData.price = level.price;
        if (this.productCatalogData.quantity) {
            this.debouncedUpdateQuantity();
        }
    },

    _getUpdateQuantityAndGetPriceParams() {
        const params = super._getUpdateQuantityAndGetPriceParams();
        if (this.env.orderResModel === "sale.order" && this.productCatalogData.priceLevel) {
            params.price_level = this.productCatalogData.priceLevel;
        }
        return params;
    },
});

ProductCatalogSaleOrderLine.template = "product_price_levels.ProductCatalogSaleOrderLine";
Object.assign(ProductCatalogSaleOrderLine.props, {
    priceLevels: { type: Array, optional: true },
    priceLevel: { type: [String, Boolean], optional: true },
    locationQuantities: { type: Array, optional: true },
});

patch(ProductCatalogSaleOrderLine.prototype, {
    formatLevelPrice(price) {
        const { currencyId, digits } = this.env;
        return formatMonetary(price, { currencyId, digits });
    },

    formatLocationQuantity(quantity) {
        return formatFloat(quantity, { digits: [false, this.env.precision] });
    },
});
