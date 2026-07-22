/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { rpc } from "@web/network/rpc";

patch(PosStore.prototype, {
    async printReceipt(order) {
        const printerId = this.config.receipt_printer_printer_id;
        if (!printerId) {
            return super.printReceipt(order);
        }

        const orderData = {
            orderlines: order.get_orderlines().map((line) => ({
                product_name: line.get_full_product_name(),
                qty: line.get_quantity(),
                price: line.get_price_with_tax(),
            })),
            total: order.get_total_with_tax(),
        };

        await rpc("/receipt_printer/pending_jobs", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        });

        await this.env.services.rpc("/receipt_printer/create_job", {
            printer_id: printerId,
            payload: JSON.stringify(orderData),
        });
    },
});
