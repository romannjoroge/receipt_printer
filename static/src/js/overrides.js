/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { Chrome } from "@point_of_sale/app/pos_app";
import { _t } from "@web/core/l10n/translation";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";

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
            btn.disabled = true;
            btn.innerHTML = '<i class="fa fa-fw fa-spin fa-circle-o-notch me-1"></i>Sending...';

            try {
                const order = pos.getOrder();
                if (!order) return;

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
                    _t("Receipt sent to thermal printer"),
                    { type: "success" }
                );
            } catch (e) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fa fa-print me-1"></i>Send to Thermal Printer';
                this.env.services.notification.add(
                    _t("Failed to send receipt. Please try again."),
                    { type: "danger" }
                );
            }
        });

        const printDiv = receiptOptions.querySelector('.d-flex.gap-1');
        if (printDiv) {
            printDiv.parentNode.insertBefore(btn, printDiv.nextSibling);
        } else {
            receiptOptions.prepend(btn);
        }
    },
});
