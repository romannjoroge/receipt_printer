/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { Navbar } from "@point_of_sale/app/components/navbar/navbar";

patch(Navbar.prototype, {
    setup() {
        super.setup();
        this._printJobsInterval = setInterval(() => {
            this._injectPrintJobsMenu();
        }, 500);
    },

    _injectPrintJobsMenu() {
        const menuItems = document.querySelector('.pos-burger-menu-items');
        if (!menuItems) {
            return;
        }

        // Avoid duplicates
        if (menuItems.querySelector('[data-action="print-jobs"]')) {
            return;
        }

        // Find the "Close Register" item to insert before it
        const items = menuItems.querySelectorAll('.dropdown-item');
        let insertBefore = null;
        for (const item of items) {
            if (item.textContent.trim() === 'Close Register') {
                insertBefore = item;
                break;
            }
        }

        if (!insertBefore) {
            return;
        }

        const menuItem = document.createElement('span');
        menuItem.className = 'o-dropdown-item dropdown-item o-navigable';
        menuItem.setAttribute('role', 'menuitem');
        menuItem.setAttribute('data-action', 'print-jobs');
        menuItem.textContent = 'Print Jobs';
        menuItem.style.cursor = 'pointer';
        menuItem.addEventListener('click', () => {
            const actionId = "receipt_printer.job_action_pos";
            const url = `/web#action=${actionId}&view_type=list`;
            window.open(url, '_blank');
        });

        menuItems.insertBefore(menuItem, insertBefore);
    },
});
