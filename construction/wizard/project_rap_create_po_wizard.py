# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProjectRapCreatePoWizard(models.TransientModel):
    _name = "project.rap.create.po.wizard"
    _description = "Create Purchase Order from RAP"

    rap_id = fields.Many2one(
        "project.rap",
        string="RAP",
        required=True,
        readonly=True,
    )

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

    partner_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
    )
    deliver_to_id = fields.Many2one(
        "res.partner",
        string="Deliver To",
    )
    expected_arrival = fields.Datetime(
        string="Expected Arrival",
    )

    use_wizard_lines = fields.Boolean(
        string="Use Wizard Lines (Edit Qty/Price Before Create)",
        default=True,
        help="Jika aktif, sistem akan membuat daftar item berdasarkan master sub-pekerjaan, "
             "dan Anda bisa mengubah qty/harga sebelum membuat PO.",
    )
    merge_same_product = fields.Boolean(
        string="Merge Same Product",
        default=True,
        help="Jika produk sama muncul beberapa kali, gabungkan qty dan pakai harga terakhir.",
    )

    line_ids = fields.One2many(
        "project.rap.create.po.wizard.line",
        "wizard_id",
        string="Lines",
        copy=False,
    )

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.partner_id = self.deliver_to_id

    def _get_sub_master_lines(self, sub):
        """Gabungkan master lines dari berbagai model (bahan/upah/jasa/alat/overhead)
        menjadi python list supaya aman (tidak union recordset lintas model).
        """
        sub.ensure_one()
        return (
            list(sub.master_bahan_ids)
            + list(sub.master_upah_ids)
            + list(sub.master_sewa_alat_ids)
            + list(sub.master_overhead_ids)
            + list(sub.master_jasa_ids)
        )

    def _build_wizard_lines_from_sub(self, sub):
        """Return list of O2M commands untuk field line_ids."""
        master_lines = self._get_sub_master_lines(sub)

        # tuples: (product_variant_id, uom_id, qty, price_unit)
        items = []
        for ml in master_lines:
            tmpl = ml.product_id  # product.template
            if not tmpl:
                continue

            # purchase.order.line pakai product.product
            variant = tmpl.product_variant_id
            if not variant:
                continue

            qty = ml.volume or 0.0
            price = ml.harga_satuan or 0.0
            uom = ml.uom_id

            items.append((variant.id, uom.id, qty, price))

        commands = [(5, 0, 0)]  # clear existing
        if not items:
            return commands

        if self.merge_same_product:
            merged = {}
            for product_id, uom_id, qty, price in items:
                key = (product_id, uom_id)
                if key not in merged:
                    merged[key] = {"qty": 0.0, "price": price}
                merged[key]["qty"] += qty
                merged[key]["price"] = price  # keep latest
            for (product_id, uom_id), vals in merged.items():
                commands.append((0, 0, {
                    "product_id": product_id,
                    "product_uom": uom_id,
                    "product_qty": vals["qty"],
                    "price_unit": vals["price"],
                }))
        else:
            for product_id, uom_id, qty, price in items:
                commands.append((0, 0, {
                    "product_id": product_id,
                    "product_uom": uom_id,
                    "product_qty": qty,
                    "price_unit": price,
                }))

        return commands

    # =========================
    # Onchange
    # =========================
    @api.onchange("pekerjaan_id")
    def _onchange_pekerjaan_id(self):
        """Saat pekerjaan berubah: reset sub & lines."""
        self.sub_pekerjaan_id = False
        self.line_ids = [(5, 0, 0)]

    @api.onchange("sub_pekerjaan_id", "use_wizard_lines", "merge_same_product")
    def _onchange_sub_pekerjaan_id(self):
        """Auto-generate wizard lines ketika sub-pekerjaan dipilih (opsional)."""
        if not self.use_wizard_lines:
            self.line_ids = [(5, 0, 0)]
            return

        if not self.sub_pekerjaan_id:
            self.line_ids = [(5, 0, 0)]
            return

        self.line_ids = self._build_wizard_lines_from_sub(self.sub_pekerjaan_id)

    # =========================
    # Action
    # =========================
    def action_confirm_create_po(self):
        """Klik OK -> buat purchase.order + purchase.order.line."""
        self.ensure_one()

        # Validasi integritas
        if not self.rap_id:
            raise UserError(_("RAP tidak ditemukan."))

        if not self.pekerjaan_id or self.pekerjaan_id.rap_id != self.rap_id:
            raise UserError(_("Pekerjaan tidak valid untuk RAP ini."))

        if not self.sub_pekerjaan_id or self.sub_pekerjaan_id.pekerjaan_id != self.pekerjaan_id:
            raise UserError(_("Sub-Pekerjaan tidak valid untuk Pekerjaan ini."))

        if not self.partner_id:
            raise UserError(_("Vendor wajib diisi."))

        po_vals = {
            "partner_id": self.partner_id.id,
            "rap_id": self.rap_id.id,
            "pekerjaan_id": self.pekerjaan_id.id,
            "sub_pekerjaan_id": self.sub_pekerjaan_id.id,
            "deliver_to_id": self.deliver_to_id.id if self.deliver_to_id else False,
            "expected_arrival": self.expected_arrival,
        }

        po = self.env["purchase.order"].create(po_vals)

        line_vals_list = []
        planned_date = self.expected_arrival or fields.Datetime.now()

        if self.use_wizard_lines:
            if not self.line_ids:
                raise UserError(_(
                    "Wizard Lines kosong. Pilih Sub-Pekerjaan untuk generate lines "
                    "atau matikan opsi Wizard Lines."
                ))

            for wl in self.line_ids:
                if not wl.product_id:
                    continue
                if wl.product_qty <= 0:
                    continue

                line_vals_list.append({
                    "order_id": po.id,
                    "product_id": wl.product_id.id,
                    "product_qty": wl.product_qty,
                    "product_uom_id": wl.product_uom.id,
                    "price_unit": wl.price_unit,
                    "date_planned": planned_date,
                    "name": wl.name or wl.product_id.display_name,
                })
        else:
            # langsung ambil dari master sub pekerjaan
            sub = self.sub_pekerjaan_id
            master_lines = self._get_sub_master_lines(sub)

            for ml in master_lines:
                tmpl = ml.product_id
                if not tmpl:
                    continue

                variant = tmpl.product_variant_id
                if not variant:
                    continue

                qty = ml.volume or 0.0
                if qty <= 0:
                    continue

                uom = ml.uom_id
                line_vals_list.append({
                    "order_id": po.id,
                    "product_id": variant.id,
                    "product_qty": qty,
                    "product_uom_id": uom.id,
                    "price_unit": ml.harga_satuan or 0.0,
                    "date_planned": planned_date,
                    "name": variant.display_name,
                })

        if line_vals_list:
            self.env["purchase.order.line"].create(line_vals_list)
        else:
            raise UserError(_("Tidak ada line yang dibuat. Cek qty/produk pada master atau wizard lines."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Purchase Order"),
            "res_model": "purchase.order",
            "view_mode": "form",
            "res_id": po.id,
            "target": "current",
        }


class ProjectRapCreatePoWizardLine(models.TransientModel):
    _name = "project.rap.create.po.wizard.line"
    _description = "Create PO Wizard Line"

    wizard_id = fields.Many2one(
        "project.rap.create.po.wizard",
        string="Wizard",
        required=True,
        ondelete="cascade",
    )

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
    )
    name = fields.Char(string="Description")

    product_qty = fields.Float(
        string="Quantity",
        default=1.0,
    )
    product_uom = fields.Many2one(
        "uom.uom",
        string="Unit of Measure",
        required=True,
    )
    price_unit = fields.Float(
        string="Unit Price",
        default=0.0,
    )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.name = rec.product_id.display_name
                rec.product_uom = rec.product_id.uom_id
