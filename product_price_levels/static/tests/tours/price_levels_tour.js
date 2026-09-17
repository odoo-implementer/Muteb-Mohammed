import { registry } from "@web/core/registry";

const productCard = '.o_kanban_record:contains("PPL Tour Widget")';

registry.category("web_tour.tours").add("product_price_levels_line_dropdown", {
    steps: () => [
        {
            content: "Edit the unit price of the order line",
            trigger: ".o_field_widget[name=order_line] .o_data_row:first .o_data_cell[name=price_unit]",
            run: "click",
        },
        {
            content: "Open the price levels dropdown",
            trigger: ".o_data_row.o_selected_row .o_field_price_level_float .o_price_level_toggler",
            run: "click",
        },
        {
            content: "Pick the wholesale price",
            trigger: '.o_price_level_item:contains("Wholesale Price")',
            run: "click",
        },
        {
            content: "The unit price is filled with the wholesale price",
            trigger: ".o_data_row.o_selected_row .o_field_price_level_float input:value(120.00)",
        },
        {
            content: "Save the order",
            trigger: ".o_form_button_save",
            run: "click",
        },
        {
            content: "Wait for the save",
            trigger: ".o_form_saved",
        },
    ],
});

registry.category("web_tour.tours").add("product_price_levels_catalog", {
    steps: () => [
        {
            content: "Open the product catalog",
            trigger: 'button[name="action_add_from_catalog"]',
            run: "click",
        },
        {
            content: "Search the product",
            trigger: "input.o_searchview_input",
            run: "edit PPL Tour",
        },
        {
            content: "Validate the search",
            trigger: "input.o_searchview_input",
            run: "press Enter",
        },
        {
            content: "Quantities are shown per location",
            trigger: `${productCard} .o_location_quantities:contains("Shelf Tour"):contains("WH/Stock")`,
        },
        {
            content: "The unit price is shown next to the price levels",
            trigger: `${productCard} .o_product_catalog_price:contains("150.00")`,
        },
        {
            content: "The order line price (150) is recognised as the public price",
            trigger: `${productCard} .o_price_levels button[data-price-level="public"].btn-primary`,
        },
        {
            content: "Select the minimum price",
            trigger: `${productCard} .o_price_levels button[data-price-level="min"]`,
            run: "click",
        },
        {
            content: "The minimum price is selected",
            trigger: `${productCard} .o_price_levels button[data-price-level="min"].btn-primary`,
        },
        {
            content: "The unit price is still shown with the price levels, and follows the selection",
            trigger: `${productCard} .o_product_catalog_price:contains("101.50")`,
        },
        {
            content: "Increase the quantity",
            trigger: `${productCard} .fa-plus`,
            run: "click",
        },
        {
            content: "Wait for the quantity",
            trigger: `${productCard} .o_input:value(3)`,
        },
        {
            content: "Back to the quotation",
            trigger: ".o-kanban-button-back",
            run: "click",
        },
        {
            content: "The order line uses the minimum price",
            trigger: '.o_field_widget[name=order_line] .o_data_row:first .o_data_cell[name=price_unit]:contains("101.50")',
        },
    ],
});
