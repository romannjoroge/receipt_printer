/** @odoo-module */

console.log("[Receipt Printer] overrides.js loaded");

import { patch } from "@web/core/utils/patch";
import { Chrome } from "@point_of_sale/app/pos_app";
import { _t } from "@web/core/l10n/translation";
import { onMounted, onWillUnmount } from "@odoo/owl";

patch(Chrome.prototype, {
    setup() {
        super.setup();
        this._thermalPrinterObserver = null;
        onMounted(() => {
            this._startThermalPrinterObserver();
        });
        onWillUnmount(() => {
            if (this._thermalPrinterObserver) {
                this._thermalPrinterObserver.disconnect();
            }
        });
    },

    _startThermalPrinterObserver() {
        const target = document.querySelector('.pos') || document.body;
        this._thermalPrinterObserver = new MutationObserver(() => {
            this._tryInjectThermalPrinterButton();
        });
        this._thermalPrinterObserver.observe(target, {
            childList: true,
            subtree: true,
        });
    },

    _tryInjectThermalPrinterButton() {
        // Check if receipt screen is visible
        const receiptOptions = document.querySelector('.receipt-options');
        if (!receiptOptions) {
            return;
        }

        // Already injected
        if (receiptOptions.querySelector('.thermal-printer-btn')) {
            return;
        }

        // POS might not be ready yet
        const pos = this.env?.pos;
        if (!pos) {
            return;
        }

        // Check printer - try multiple paths since the data structure varies
        const printerId = pos.config?.receipt_printer_printer_id
            || pos.config?.raw?.receipt_printer_printer_id;
        if (!printerId) {
            return;
        }

        const btn = document.createElement('button');
        btn.className = 'button print btn btn-lg btn-success w-100 py-3 thermal-printer-btn';
        btn.innerHTML = '<i class="fa fa-print me-1"></i>Send to Thermal Printer';
        btn.addEventListener('click', async () => {
            const order = pos.get_order();
            if (!order) return;

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
