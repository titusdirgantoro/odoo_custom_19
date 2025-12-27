# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProjectRapImportTemplateWizard(models.TransientModel):
    _name = "project.rap.import.template"
    _description = "Wizard: Add Pekerjaan from Template to RAP/PFC"

    rap_id = fields.Many2one("project.rap", required=True, readonly=True)

    template_ids = fields.Many2many(
        "construction.pekerjaan.template",
        string="Pekerjaan Templates",
        required=True,
    )

    mode = fields.Selection(
        [("append", "Append"), ("replace", "Replace")],
        default="append",
        required=True,
    )

    duplicate_policy = fields.Selection(
        [("error", "Error"), ("skip", "Skip"), ("rename", "Rename")],
        default="error",
        required=True,
        help="Saat code pekerjaan dari template bentrok dengan pekerjaan yang sudah ada di RAP, pilih aksi yang dilakukan.",
    )

    price_rule = fields.Selection(
        [
            ("template_price", "Use Template Price"),
            ("product_construction_price", "Use Product Construction Price"),
            ("template_else_product", "Template Price else Product Price"),
        ],
        default="template_else_product",
        required=True,
    )

    def _get_target_line_model(self, type_master_data):
        mapping = {
            "bahan": "project.master.bahan",
            "upah": "project.master.upah",
            "sewa_alat": "project.master.sewa.alat",
            "overhead": "project.master.overhead",
            "jasa": "project.master.jasa",
        }
        return mapping.get(type_master_data)

    def _compute_tx_price(self, line):
        product = line.product_id
        template_price = line.harga_satuan_default or 0.0
        product_price = getattr(product, "construction_price", 0.0) or 0.0

        if self.price_rule == "template_price":
            return template_price
        if self.price_rule == "product_construction_price":
            return product_price
        # template_else_product
        return template_price if template_price else product_price

    def _generate_unique_pekerjaan_code(self, rap, base_code):
        base_code = (base_code or "").strip() or "TEMPLATE"
        code = base_code
        i = 1
        existing = set(rap.pekerjaan_ids.mapped("code"))
        while code in existing:
            i += 1
            code = f"{base_code}-{i}"
        return code

    def action_import(self):
        self.ensure_one()
        rap = self.rap_id

        if rap.state == "approved":
            raise UserError(_("Dokumen RAP/PFC sudah Approved, tidak bisa diubah."))

        if self.mode == "replace":
            rap.pekerjaan_ids.unlink()

        for tmpl_pekerjaan in self.template_ids:
            # handle code conflict with RAP constraint unique(rap_id, code)
            code = (tmpl_pekerjaan.code or "").strip()
            if code and code in rap.pekerjaan_ids.mapped("code"):
                if self.duplicate_policy == "error":
                    raise UserError(_("Code pekerjaan '%s' sudah ada di dokumen ini.") % code)
                if self.duplicate_policy == "skip":
                    continue
                if self.duplicate_policy == "rename":
                    code = self._generate_unique_pekerjaan_code(rap, code)

            pekerjaan_tx = self.env["project.pekerjaan"].create(
                {
                    "rap_id": rap.id,
                    "template_id": tmpl_pekerjaan.id,
                    "code": code or self._generate_unique_pekerjaan_code(rap, tmpl_pekerjaan.code),
                    "name": tmpl_pekerjaan.name,
                }
            )

            for sub_tmpl in tmpl_pekerjaan.sub_template_ids.sorted(lambda r: (r.sequence, r.id)):
                sub_tx = self.env["project.sub.pekerjaan"].create(
                    {
                        "pekerjaan_id": pekerjaan_tx.id,
                        "template_id": sub_tmpl.id,
                        "name": sub_tmpl.name,
                        "uom_id": sub_tmpl.uom_id.id if sub_tmpl.uom_id else False,
                        "volume": sub_tmpl.default_volume or 1.0,
                    }
                )

                for line in sub_tmpl.line_ids:
                    target_model = self._get_target_line_model(line.type_master_data)
                    if not target_model:
                        # skip unknown type
                        continue

                    self.env[target_model].create(
                        {
                            "sub_pekerjaan_id": sub_tx.id,
                            "product_id": line.product_id.id,
                            "volume": line.volume or 1.0,
                            "harga_satuan": self._compute_tx_price(line),
                            "template_line_id": line.id,
                        }
                    )

        return {"type": "ir.actions.act_window_close"}
