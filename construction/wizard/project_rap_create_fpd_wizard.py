# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProjectRapCreateFpdWizard(models.TransientModel):
    _name = "project.rap.create.fpd.wizard"
    _description = "Create FPD from RAP"

    rap_id = fields.Many2one("project.rap", string="RAP", required=True, readonly=True)
    project_id = fields.Many2one("project.project", string="Project", required=True, readonly=True)

    pekerjaan_id = fields.Many2one(
        "project.pekerjaan",
        string="Pekerjaan",
        required=True,
        domain="[('rap_id', '=', rap_id)]",
    )
    sub_pekerjaan_id = fields.Many2one(
        "project.sub.pekerjaan",
        string="Sub-Pekerjaan",
        required=True,
        domain="[('pekerjaan_id', '=', pekerjaan_id)]",
    )

    merge_same_product = fields.Boolean(
        string="Merge Same Product",
        default=True,
        help="Jika produk sama muncul beberapa kali, gabungkan qty dan pakai harga terakhir.",
    )

    line_ids = fields.One2many("project.rap.create.fpd.wizard.line", "wizard_id", string="Lines", copy=False)

    def _get_sub_master_lines(self, sub):
        sub.ensure_one()
        return (
            list(sub.master_bahan_ids)
            + list(sub.master_upah_ids)
            + list(sub.master_sewa_alat_ids)
            + list(sub.master_overhead_ids)
            + list(sub.master_jasa_ids)
        )

    def _build_lines_from_sub(self, sub):
        master_lines = self._get_sub_master_lines(sub)

        # tuples: (product_template_id, uom_id, qty, price_unit)
        items = []
        for ml in master_lines:
            tmpl = ml.product_id  # product.template
            if not tmpl:
                continue

            qty = ml.volume or 0.0
            price = ml.harga_satuan or 0.0
            uom = ml.uom_id or tmpl.uom_id

            items.append((tmpl.id, uom.id, qty, price))

        commands = [(5, 0, 0)]
        if not items:
            return commands

        if self.merge_same_product:
            merged = {}
            for tmpl_id, uom_id, qty, price in items:
                key = (tmpl_id, uom_id)
                if key not in merged:
                    merged[key] = {"qty": 0.0, "price": price}
                merged[key]["qty"] += qty
                merged[key]["price"] = price
            for (tmpl_id, uom_id), vals in merged.items():
                commands.append((0, 0, {
                    "product_tmpl_id": tmpl_id,
                    "uom_id": uom_id,
                    "qty": vals["qty"],
                    "price_unit": vals["price"],
                }))
        else:
            for tmpl_id, uom_id, qty, price in items:
                commands.append((0, 0, {
                    "product_tmpl_id": tmpl_id,
                    "uom_id": uom_id,
                    "qty": qty,
                    "price_unit": price,
                }))

        return commands

    @api.onchange("pekerjaan_id")
    def _onchange_pekerjaan_id(self):
        self.sub_pekerjaan_id = False
        self.line_ids = [(5, 0, 0)]

    @api.onchange("sub_pekerjaan_id", "merge_same_product")
    def _onchange_sub_pekerjaan_id(self):
        if not self.sub_pekerjaan_id:
            self.line_ids = [(5, 0, 0)]
            return
        self.line_ids = self._build_lines_from_sub(self.sub_pekerjaan_id)

    def action_create_fpd(self):
        self.ensure_one()

        if not self.rap_id:
            raise UserError(_("RAP tidak ditemukan."))
        if not self.project_id:
            raise UserError(_("Project tidak ditemukan."))

        if not self.pekerjaan_id or self.pekerjaan_id.rap_id != self.rap_id:
            raise UserError(_("Pekerjaan tidak valid untuk RAP ini."))
        if not self.sub_pekerjaan_id or self.sub_pekerjaan_id.pekerjaan_id != self.pekerjaan_id:
            raise UserError(_("Sub-Pekerjaan tidak valid untuk Pekerjaan ini."))
        if not self.line_ids:
            raise UserError(_("Lines kosong. Pilih Sub-Pekerjaan untuk generate lines."))

        fpd = self.env["project.fpd"].create({
            "rap_id": self.rap_id.id,
            "project_id": self.project_id.id,
            "pekerjaan_id": self.pekerjaan_id.id,
            "sub_pekerjaan_id": self.sub_pekerjaan_id.id,
            "line_ids": [(0, 0, {
                "product_tmpl_id": l.product_tmpl_id.id,
                "qty": l.qty,
                "uom_id": l.uom_id.id,
                "price_unit": l.price_unit,
            }) for l in self.line_ids if l.product_tmpl_id and l.qty > 0],
        })

        return {
            "type": "ir.actions.act_window",
            "name": _("FPD"),
            "res_model": "project.fpd",
            "view_mode": "form",
            "res_id": fpd.id,
            "target": "current",
        }


class ProjectRapCreateFpdWizardLine(models.TransientModel):
    _name = "project.rap.create.fpd.wizard.line"
    _description = "Create FPD Wizard Line"

    wizard_id = fields.Many2one("project.rap.create.fpd.wizard", required=True, ondelete="cascade")

    product_tmpl_id = fields.Many2one("product.template", string="Product", required=True)
    qty = fields.Float(string="Qty", default=1.0)
    uom_id = fields.Many2one("uom.uom", string="UoM", required=True)
    price_unit = fields.Float(string="Price Unit", default=0.0)
    total_price = fields.Float(string="Total Price", compute="_compute_total_price", store=True)

    @api.depends("qty", "price_unit")
    def _compute_total_price(self):
        for rec in self:
            rec.total_price = (rec.qty or 0.0) * (rec.price_unit or 0.0)

    @api.onchange("product_tmpl_id")
    def _onchange_product_tmpl_id(self):
        for rec in self:
            if rec.product_tmpl_id:
                rec.uom_id = rec.product_tmpl_id.uom_id
                if "construction_price" in rec.product_tmpl_id._fields and not rec.price_unit:
                    rec.price_unit = rec.product_tmpl_id.construction_price or 0.0
