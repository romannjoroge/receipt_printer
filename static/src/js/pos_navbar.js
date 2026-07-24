/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { Navbar } from "@point_of_sale/app/components/navbar/navbar";

patch(Navbar.prototype, {
    setup() {
        super.setup();
        this._printJobsInjected = false;
        this._printJobsInterval = setInterval(() => {
            this._injectPrintJobsMenu();
        }, 500);
    },

    _injectPrintJobsMenu() {
        if (this._printJobsInjected) {
            return;
        }

        const menuItems = document.querySelector('.pos-burger-menu-items');
        if (!menuItems) {
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

        const menuItem = document.createElement('div');
        menuItem.className = 'dropdown-item';
        menuItem.setAttribute('role', 'menuitem');
        menuItem.textContent = 'Print Jobs';
        menuItem.addEventListener('click', () => {
            const actionId = "receipt_printer.job_action_pos";
            const url = `/web#action=${actionId}&view_type=list`;
            window.open(url, '_blank');
        });

        if (insertBefore) {
            menuItems.insertBefore(menuItem, insertBefore);
        } else {
            menuItems.appendChild(menuItem);
        }

        this._printJobsInjected = true;
    },
});
