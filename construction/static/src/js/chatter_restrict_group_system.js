/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { user } from "@web/core/user";

// hanya ini yang ada di instans kamu
import { Chatter } from "@mail/chatter/web_portal/chatter";

async function _setIsSystem(comp) {
    comp.state.isSystem = await user.hasGroup("base.group_system");
}

// simpan reference method asli
const _setup = Chatter.prototype.setup;

patch(Chatter.prototype, {
    name: "construction.restrict_chatter_group_system",
    setup() {
        // panggil setup asli
        _setup.call(this, ...arguments);

        // lalu set flag
        _setIsSystem(this);
    },
});
