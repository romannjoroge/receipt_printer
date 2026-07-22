/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { Chrome } from "@point_of_sale/app/pos_app";
import { _t } from "@web/core/l10n/translation";

patch(Chrome.prototype, {
    setup() {
        super.setup();
        this._thermalPrinterInterval = setInterval(() => {
            this._tryInjectThermalPrinterButton();
        }, 500);
    },

    _tryInjectThermalPrinterButton() {
        const receiptOptions = document.querySelector('.receipt-options');
        if (!receiptOptions || receiptOptions.querySelector('.thermal-printer-btn')) {
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

        const btn = document.createElement('button');
        btn.className = 'button print btn btn-lg btn-success w-100 py-3 thermal-printer-btn';
        btn.innerHTML = '<i class="fa fa-print me-1"></i>Send to Thermal Printer';
        btn.addEventListener('click', async () => {
            const order = pos.getOrder();
            if (!order) return;

            const orderData = {
                orderlines: order.getOrderlines().map((line) => ({
                    product_name: line.full_product_name || line.product_id?.display_name,
                    qty: line.qty,
                    price: line.prices?.total_included || 0,
                })),
                total: order.priceIncl || 0,
                partner: order.getPartner()?.name || "",
                date: order.date_order,
            };

            await pos.data.call(
                "pos.config",
                "action_print_receipt",
                [[pos.config.id], orderData]
            );

            this.env.services.notification.add(
                _t("Receipt sent to thermal printer"),
                { type: "success" }
            );
        });

        const printDiv = receiptOptions.querySelector('.d-flex.gap-1');
        if (printDiv) {
            printDiv.parentNode.insertBefore(btn, printDiv.nextSibling);
        } else {
            receiptOptions.prepend(btn);
        }
    },
});
