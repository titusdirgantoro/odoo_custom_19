# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class ProjectRapCreatePoWizard(models.TransientModel):
    _name = "project.rap.create.po.wizard"
    _description = "Create Purchase Order from RAP (Based on FPD)"

    rap_id = fields.Many2one(
        "project.rap",
        string="RAP",
        required=True,
        readonly=True,
    )

    # Source data sekarang dari FPD
    fpd_id = fields.Many2one(
        "project.fpd",
        string="FPD",
        required=True,
        domain="[('rap_id', '=', rap_id), ('state', 'in', ('approve'))]",
        help="FPD yang akan digunakan sebagai sumber lines untuk PO.",
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Vendor",
        required=True,
        domain="[('supplier_rank', '>', 0)]"
    )
    deliver_to_id = fields.Many2one(
        "stock.warehouse",
        string="Deliver To",
    )
    expected_arrival = fields.Datetime(
        string="Expected Arrival",
    )

    use_wizard_lines = fields.Boolean(
        string="Use Wizard Lines (Edit Qty/Price Before Create)",
        default=True,
        help="Jika aktif, sistem akan menyalin item dari FPD ke wizard lines, "
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
    picking_type_id = fields.Many2one(
        "stock.picking.type",
        string="Receipt Operation Type",
        compute="_compute_picking_type_id",
        readonly=True,
        help="Akan otomatis mengikuti Warehouse (Incoming Type).",
    )

    allowed_product_ids = fields.Many2many(
        "product.product",
        string="Allowed Products",
        compute="_compute_allowed_product_ids",
        help="Produk yang diizinkan berdasarkan FPD Lines terpilih.",
    )

    # =========================================================
    # Allowed Products: dari FPD Lines
    # =========================================================
    @api.depends("fpd_id")
    def _compute_allowed_product_ids(self):
        for wiz in self:
            products = self.env["product.product"]
            if wiz.fpd_id:
                tmpls = wiz.fpd_id.line_ids.mapped("product_tmpl_id")
                products = tmpls.mapped("product_variant_ids")
            wiz.allowed_product_ids = products

    # =========================================================
    # Picking type: dari warehouse
    # =========================================================
    @api.depends("deliver_to_id")
    def _compute_picking_type_id(self):
        for wiz in self:
            picking_type = self.env["stock.picking.type"].search(
                [("code", "=", "incoming"), ("warehouse_id", "in", wiz.deliver_to_id.ids)],
                limit=1
            )
            wiz.picking_type_id = picking_type or False

    # =========================================================
    # Builder Lines: dari FPD
    # =========================================================
    def _build_wizard_lines_from_fpd(self, fpd):
        """Return list of O2M commands untuk field line_ids dari FPD."""
        fpd.ensure_one()

        # tuples: (product_variant_id, uom_id, qty, price_unit)
        items = []
        for fl in fpd.line_ids:
            tmpl = fl.product_tmpl_id
            if not tmpl:
                continue

            variant = tmpl.product_variant_id  # asumsi 1 template = 1 variant
            if not variant:
                continue

            qty = fl.qty or 0.0
            price = fl.price_unit or 0.0
            uom = fl.uom_id or tmpl.uom_id

            items.append((variant.id, uom.id, qty, price))

        commands = [(5, 0, 0)]
        if not items:
            return commands

        if self.merge_same_product:
            merged = {}
            for product_id, uom_id, qty, price in items:
                key = (product_id, uom_id)
                if key not in merged:
                    merged[key] = {"qty": 0.0, "price": price}
                merged[key]["qty"] += qty
                merged[key]["price"] = price
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

    # =========================================================
    # Onchange: FPD -> generate lines
    # =========================================================
    @api.onchange("fpd_id", "use_wizard_lines", "merge_same_product")
    def _onchange_fpd_id(self):
        if not self.use_wizard_lines:
            self.line_ids = [(5, 0, 0)]
            return

        if not self.fpd_id:
            self.line_ids = [(5, 0, 0)]
            return

        self.line_ids = self._build_wizard_lines_from_fpd(self.fpd_id)

    # =========================================================
    # Action Create PO
    # =========================================================
    def action_confirm_create_po(self):
        self.ensure_one()
        _logger.info("==== self.picking_type_id %s" % (str(self.picking_type_id)))
        # Validasi integritas
        if not self.picking_type_id:
            raise UserError(_("Warehouse belum memiliki Incoming Operation Type (Receipt)."))

        if not self.rap_id:
            raise UserError(_("RAP tidak ditemukan."))

        if not self.fpd_id or self.fpd_id.rap_id != self.rap_id:
            raise UserError(_("FPD tidak valid untuk RAP ini."))

        if not self.partner_id:
            raise UserError(_("Vendor wajib diisi."))

        if not self.fpd_id.line_ids:
            raise UserError(_("FPD Lines kosong."))

        picking_type = self.picking_type_id

        # Header PO: ambil pekerjaan/sub dari FPD
        po_vals = {
            "partner_id": self.partner_id.id,
            "rap_id": self.rap_id.id,
            "fpd_id": self.fpd_id.id if "fpd_id" in self.env["purchase.order"]._fields else False,
            "pekerjaan_id": self.fpd_id.pekerjaan_id.id if "pekerjaan_id" in self.env["purchase.order"]._fields else False,
            "sub_pekerjaan_id": self.fpd_id.sub_pekerjaan_id.id if "sub_pekerjaan_id" in self.env["purchase.order"]._fields else False,
            "picking_type_id": picking_type.id,
            "expected_arrival": self.expected_arrival,
        }

        # bersihkan key False agar tidak error create bila field tidak ada
        po_vals = {k: v for k, v in po_vals.items() if v is not False}

        po = self.env["purchase.order"].create(po_vals)

        planned_date = self.expected_arrival or fields.Datetime.now()
        line_vals_list = []

        if self.use_wizard_lines:
            if not self.line_ids:
                raise UserError(_(
                    "Wizard Lines kosong. Pilih FPD untuk generate lines "
                    "atau matikan opsi Wizard Lines."
                ))

            for wl in self.line_ids:
                if not wl.product_id or wl.product_qty <= 0:
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
            # langsung ambil dari FPD lines
            for fl in self.fpd_id.line_ids:
                tmpl = fl.product_tmpl_id
                if not tmpl:
                    continue
                variant = tmpl.product_variant_id
                if not variant:
                    continue
                qty = fl.qty or 0.0
                if qty <= 0:
                    continue
                uom = fl.uom_id or tmpl.uom_id
                line_vals_list.append({
                    "order_id": po.id,
                    "product_id": variant.id,
                    "product_qty": qty,
                    "product_uom_id": uom.id,
                    "price_unit": fl.price_unit or 0.0,
                    "date_planned": planned_date,
                    "name": variant.display_name,
                })

        if line_vals_list:
            self.env["purchase.order.line"].create(line_vals_list)
        else:
            raise UserError(_("Tidak ada line yang dibuat. Cek qty/produk pada FPD."))

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

    allowed_product_ids = fields.Many2many(
        "product.product",
        related="wizard_id.allowed_product_ids",
        readonly=True,
    )

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
        domain="[('id', 'in', allowed_product_ids)]",
    )

    name = fields.Char(string="Description")

    product_qty = fields.Float(string="Quantity", default=1.0)

    product_uom = fields.Many2one(
        "uom.uom",
        string="Unit of Measure",
        required=True,
    )

    price_unit = fields.Float(string="Unit Price", default=0.0)

    type_master_data = fields.Selection(
        related="product_id.type_master_data",
        string="Type Master Data",
        readonly=True,
    )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.name = rec.product_id.display_name
                rec.product_uom = rec.product_id.uom_id
