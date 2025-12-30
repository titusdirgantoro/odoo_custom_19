# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProjectRapSaveAsTemplateWizard(models.TransientModel):
    _name = "project.rap.save.as.template"
    _description = "Wizard: Save RAP/PFC as Template"

    source_rap_id = fields.Many2one("project.rap", required=True, readonly=True)

    template_name = fields.Char(string="Template Name (Prefix)", required=False)
    template_code_prefix = fields.Char(string="Template Code Prefix", required=True)

    scope = fields.Selection(
        [("all", "All Pekerjaan"), ("selected", "Selected Pekerjaan")],
        default="all",
        required=True,
    )

    pekerjaan_ids = fields.Many2many("project.pekerjaan", string="Pekerjaan", domain="[('rap_id','=',source_rap_id)]")

    price_policy = fields.Selection(
        [
            ("keep_prices", "Keep RAP Prices"),
            ("zero_prices", "Set Prices to 0"),
            ("use_product_price", "Use Product Construction Price"),
            ("rap_else_product", "RAP Price else Product Price"),
        ],
        default="keep_prices",
        required=True,
    )

    @api.onchange("scope", "source_rap_id")
    def _onchange_scope(self):
        for wiz in self:
            if not wiz.source_rap_id:
                continue
            if wiz.scope == "all":
                wiz.pekerjaan_ids = [(6, 0, wiz.source_rap_id.pekerjaan_ids.ids)]
            else:
                wiz.pekerjaan_ids = [(5, 0, 0)]

    def _compute_template_price(self, tx_line):
        product = tx_line.product_id
        rap_price = tx_line.harga_satuan or 0.0
        product_price = getattr(product, "construction_price", 0.0) or 0.0

        if self.price_policy == "keep_prices":
            return rap_price
        if self.price_policy == "zero_prices":
            return 0.0
        if self.price_policy == "use_product_price":
            return product_price
        # rap_else_product
        return rap_price if rap_price else product_price

    def _unique_template_code(self, base_code, company_id):
        base_code = (base_code or "").strip() or "TEMPLATE"
        code = base_code
        i = 1
        Template = self.env["construction.pekerjaan.template"]
        while Template.search_count([("code", "=", code), ("company_id", "=", company_id)]) > 0:
            i += 1
            code = f"{base_code}-{i}"
        return code

    def action_save(self):
        self.ensure_one()
        rap = self.source_rap_id
        if not rap.pekerjaan_ids:
            raise UserError(_("Dokumen ini belum memiliki pekerjaan."))

        pekerjaan_tx = self.pekerjaan_ids
        if self.scope == "all":
            pekerjaan_tx = rap.pekerjaan_ids
        if not pekerjaan_tx:
            raise UserError(_("Pilih minimal 1 pekerjaan untuk dijadikan template."))

        created_template_ids = []

        for p in pekerjaan_tx:
            # name & code
            multiple = len(pekerjaan_tx) > 1
            tmpl_name = self.template_code_prefix if not multiple else f"{self.template_code_prefix} - {p.name or p.code}"
            base_code = self.template_code_prefix or p.code or "TEMPLATE"
            if multiple:
                base_code = f"{base_code}-{p.name or p.code}"

            tmpl_code = self._unique_template_code(base_code, rap.project_id.company_id.id if rap.project_id.company_id else self.env.company.id)

            tmpl_pekerjaan = self.env["construction.pekerjaan.template"].create(
                {
                    "name": tmpl_name,
                    "code": tmpl_code,
                    "company_id": rap.project_id.company_id.id if rap.project_id.company_id else self.env.company.id,
                    "active": True,
                    "notes": _("Generated from %s") % rap.name,
                }
            )
            created_template_ids.append(tmpl_pekerjaan.id)

            for sub in p.sub_pekerjaan_ids:
                sub_tmpl = self.env["construction.sub.pekerjaan.template"].create(
                    {
                        "pekerjaan_template_id": tmpl_pekerjaan.id,
                        "sequence": 10,
                        "name": sub.name,
                        "uom_id": sub.uom_id.id if sub.uom_id else False,
                        "default_volume": sub.volume or 1.0,
                    }
                )

                # gather all tx lines from 5 categories
                tx_line_sets = [
                    sub.master_bahan_ids,
                    sub.master_upah_ids,
                    sub.master_sewa_alat_ids,
                    sub.master_overhead_ids,
                    sub.master_jasa_ids,
                ]

                for lineset in tx_line_sets:
                    for l in lineset:
                        self.env["construction.sub.template.line"].create(
                            {
                                "sub_template_id": sub_tmpl.id,
                                "product_id": l.product_id.id,
                                "volume": l.volume or 1.0,
                                "harga_satuan_default": self._compute_template_price(l),
                            }
                        )

        # open created templates
        return {
            "type": "ir.actions.act_window",
            "name": _("Pekerjaan Templates"),
            "res_model": "construction.pekerjaan.template",
            "view_mode": "list,form",
            "domain": [("id", "in", created_template_ids)],
        }
