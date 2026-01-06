/** @odoo-module **/

import { registry } from "@web/core/registry";
import { append, createElement, setAttributes } from "@web/core/utils/xml";
import { session } from "@web/session";

function compileChatter(node, params) {
    if (!session.is_system) {
        return createElement("t");
    }

    const chatterContainerXml = createElement("t");
    setAttributes(chatterContainerXml, {
        "t-component": "__comp__.mailComponents.Chatter",
        has_activities: "__comp__.props.archInfo.has_activities",
        hasAttachmentPreview: Boolean(
            this.templates.FormRenderer.querySelector(".o_attachment_preview")
        ),
        hasParentReloadOnActivityChanged: Boolean(node.getAttribute("reload_on_activity")),
        hasParentReloadOnAttachmentsChanged: Boolean(node.getAttribute("reload_on_attachment")),
        hasParentReloadOnFollowersUpdate: Boolean(node.getAttribute("reload_on_follower")),
        hasParentReloadOnMessagePosted: Boolean(node.getAttribute("reload_on_post")),
        isAttachmentBoxVisibleInitially: Boolean(node.getAttribute("open_attachments")),
        threadId: "__comp__.props.record.resId or undefined",
        threadModel: "__comp__.props.record.resModel",
        record: "__comp__.props.record",
        saveRecord: "() => __comp__.save and __comp__.save()",
        highlightMessageId: "__comp__.highlightMessageId",
    });

    const chatterContainerHookXml = createElement("div");
    chatterContainerHookXml.classList.add("o-mail-ChatterContainer", "o-mail-Form-chatter");
    setAttributes(chatterContainerHookXml, { "t-if": "!__comp__.env.inDialog" });

    append(chatterContainerHookXml, chatterContainerXml);
    return chatterContainerHookXml;
}

registry.category("form_compilers").add(
    "chatter_compiler",
    {
        selector: "chatter",
        fn: compileChatter,
    },
    { force: true }
);
