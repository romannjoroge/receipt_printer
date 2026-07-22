/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { useTrackedAsync } from "@point_of_sale/app/hooks/hooks";
import { _t } from "@web/core/l10n/translation";

patch(ReceiptScreen.prototype, {
    setup() {
        super.setup();
        this.sendToPrinter = useTrackedAsync(
            this._sendToThermalPrinter.bind(this)
        );
    },

    get hasThermalPrinter() {
        return !!this.pos.config.receipt_printer_printer_id;
    },

    async _sendToThermalPrinter() {
        const order = this.currentOrder;
        const printerId = this.pos.config.receipt_printer_printer_id?.id;
        if (!printerId) {
            return;
        }

        const orderData = {
            orderlines: order.get_orderlines().map((line) => ({
                product_name: line.get_full_product_name(),
                qty: line.get_quantity(),
                price: line.get_price_with_tax(),
            })),
            total: order.get_total_with_tax(),
            partner: order.getPartner()?.name || "",
            date: order.date_order,
        };

        await this.pos.data.call(
            "pos.config",
            "action_print_receipt",
            [[this.pos.config.id], orderData]
        );

        this.env.services.notification.add(
            _t("Receipt sent to thermal printer"),
            { type: "success" }
        );
    },
});
