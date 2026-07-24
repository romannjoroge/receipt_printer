/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { Chrome } from "@point_of_sale/app/pos_app";
import { _t } from "@web/core/l10n/translation";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";

patch(Chrome.prototype, {
    setup() {
        super.setup();
        this._thermalPrinterSentOrders = new Set();
        this._thermalPrinterInterval = setInterval(() => {
            this._tryAutoPrintReceipt();
        }, 500);
    },

    async _tryAutoPrintReceipt() {
        const receiptOptions = document.querySelector('.receipt-options');
        if (!receiptOptions) {
            return;
        }

        const pos = this.pos;
        if (!pos?.config) {
            return;
        }

        const printerId = pos.config.receipt_printer_printer_id
            || pos.config.raw?.receipt_printer_printer_id;
        if (!printerId) {
            return;
        }

        const order = pos.getOrder();
        if (!order) {
            return;
        }

        // Prevent duplicate jobs for the same order
        if (this._thermalPrinterSentOrders.has(order.uuid)) {
            return;
        }
        this._thermalPrinterSentOrders.add(order.uuid);

        try {
            const renderer = this.env.services.renderer;
            const receiptImage = await renderer.toJpeg(
                OrderReceipt,
                { order: order, basic_receipt: false },
                { addClass: "pos-receipt-print p-3" }
            );

            await pos.data.call(
                "pos.config",
                "action_print_receipt",
                [[pos.config.id], receiptImage]
            );

            this.env.services.notification.add(
                _t("Receipt automatically sent to thermal printer"),
                { type: "success" }
            );
        } catch (e) {
            // Remove from sent set so it can retry on next poll
            this._thermalPrinterSentOrders.delete(order.uuid);
            this.env.services.notification.add(
                _t("Failed to send receipt to thermal printer. Retrying..."),
                { type: "warning" }
            );
        }
    },
});
