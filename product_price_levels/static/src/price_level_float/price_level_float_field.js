/** @odoo-module */
import { _t } from "@web/core/l10n/translation";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { FloatField, floatField } from "@web/views/fields/float/float_field";
import { formatFloat } from "@web/views/fields/formatters";

/**
 * Unit price input with a dropdown offering the product price levels
 * (public / wholesale / minimum). Typing a manual price stays possible.
 * The line must expose price_level_public, price_level_wholesale and price_level_min.
 */
export class PriceLevelFloatField extends FloatField {
    static template = "product_price_levels.PriceLevelFloatField";
    static components = { ...FloatField.components, Dropdown, DropdownItem };

    get priceLevels() {
        const data = this.props.record.data;
        if (!data.product_id) {
            return [];
        }
        return [
            { key: "public", label: _t("Public Price"), price: data.price_level_public },
            { key: "wholesale", label: _t("Wholesale Price"), price: data.price_level_wholesale },
            { key: "min", label: _t("Minimum Price"), price: data.price_level_min },
        ];
    }

    formatLevelPrice(price) {
        return formatFloat(price, {
            digits: this.props.digits,
            field: this.props.record.fields[this.props.name],
        });
    }

    async selectPriceLevel(level) {
        await this.props.record.update({ [this.props.name]: level.price });
    }
}

export const priceLevelFloatField = {
    ...floatField,
    component: PriceLevelFloatField,
    displayName: _t("Price with levels"),
};

registry.category("fields").add("price_level_float", priceLevelFloatField);
