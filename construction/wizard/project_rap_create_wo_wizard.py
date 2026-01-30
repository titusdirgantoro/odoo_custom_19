# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProjectRapCreateWoWizard(models.TransientModel):
    _name = "project.rap.create.wo.wizard"
    _description = "Create Work Order (WO) from RAP"

    def _default_warehouse_id(self):
        return self.env['stock.warehouse'].search(self.env['stock.warehouse']._check_company_domain(self.env.company), limit=1).id

    rap_id = fields.Many2one(
        "project.rap",
        string="RAP",
        required=True,
        readonly=True,
    )  
    fpd_id = fields.Many2one(
        "project.fpd",
        string="FPD",
        required=True,
        domain="[('rap_id', '=', rap_id), ('state', '=', 'approve'), ('is_used', '=', False)]",
        help="FPD yang akan digunakan sebagai sumber lines untuk PO.",
    )

    pekerjaan_id = fields.Many2one(
        "project.pekerjaan",
        string="Pekerjaan",
        domain="[('rap_id', '=', rap_id)]",
        related='fpd_id.pekerjaan_id',
        store=True
    )
    sub_pekerjaan_id = fields.Many2one(
        "project.sub.pekerjaan",
        string="Sub-Pekerjaan",
        domain="[('pekerjaan_id', '=', pekerjaan_id)]",
        help="Jika diisi, hanya service yang sesuai sub-pekerjaan yang boleh dipilih. "
             "Jika kosong, semua service boleh dipilih.",
        related='fpd_id.sub_pekerjaan_id',
        store=True
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
        default=_default_warehouse_id,
    )
    expected_arrival = fields.Datetime(string="Expected Arrival")

    picking_type_id = fields.Many2one(
        "stock.picking.type",
        string="Receipt Operation Type",
        compute="_compute_picking_type_id",
        readonly=True,
        help="Akan otomatis mengikuti Warehouse (Incoming Type).",
    )

    allowed_product_ids = fields.Many2many(
        "product.product",
        string="Allowed Service Products",
        compute="_compute_allowed_product_ids",
        help="Jika Sub-Pekerjaan diisi: service dari master lines sub-pekerjaan. "
             "Jika kosong: semua service.",
    )

    line_ids = fields.One2many(
        "project.rap.create.wo.wizard.line",
        "wizard_id",
        string="Lines",
        copy=False,
    )

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
    # Allowed Products: service only
    # - jika ada sub_pekerjaan: dari master lines sub (service saja)
    # - jika tidak: semua service (purchase_ok=True)
    # =========================================================
    @api.depends("fpd_id", "fpd_id.line_ids", "fpd_id.line_ids.product_tmpl_id")
    def _compute_allowed_product_ids(self):
        Product = self.env["product.product"]
        for wiz in self:
            products = Product

            if wiz.fpd_id:
                tmpls = wiz.fpd_id.line_ids.mapped("product_tmpl_id").filtered(lambda t: t and t.type == "service")
                products = tmpls.mapped("product_variant_ids")

            wiz.allowed_product_ids = products

    def _build_wizard_lines_from_fpd(self, fpd):
        """Return O2M commands untuk line_ids dari FPD (service only)."""
        fpd.ensure_one()

        items = []
        for fl in fpd.line_ids:
            tmpl = fl.product_tmpl_id
            if not tmpl or tmpl.type != "service":
                continue

            variant = tmpl.product_variant_id  # asumsi 1 template = 1 variant
            if not variant:
                continue

            qty = fl.qty or 0.0
            price = fl.price_unit or 0.0
            uom = fl.uom_id or tmpl.uom_id

            if qty <= 0:
                continue

            items.append((variant.id, uom.id, qty, price))

        commands = [(5, 0, 0)]
        if not items:
            return commands

        for product_id, uom_id, qty, price in items:
            commands.append((0, 0, {
                "product_id": product_id,
                "product_uom": uom_id,
                "product_qty": qty,
                "price_unit": price,
            }))

        return commands
    
    @api.onchange("fpd_id")
    def _onchange_fpd_id(self):
        for wiz in self:
            if not wiz.fpd_id:
                wiz.line_ids = [(5, 0, 0)]
                return

            # pastikan RAP konsisten
            if wiz.rap_id and wiz.fpd_id.rap_id and wiz.fpd_id.rap_id != wiz.rap_id:
                raise UserError(_("FPD yang dipilih tidak sesuai dengan RAP pada wizard."))

            wiz.line_ids = wiz._build_wizard_lines_from_fpd(wiz.fpd_id)

    def action_confirm_create_wo(self):
        self.ensure_one()

        if not self.picking_type_id:
            raise UserError(_("Warehouse belum memiliki Incoming Operation Type (Receipt)."))

        if not self.rap_id:
            raise UserError(_("RAP tidak ditemukan."))

        if self.rap_id.state != "approved":
            raise UserError(_("WO hanya boleh dibuat saat RAP sudah Approved."))

        if not self.partner_id:
            raise UserError(_("Vendor wajib diisi."))

        if not self.line_ids:
            raise UserError(_("Lines kosong. Tambahkan minimal 1 line."))
        if self.fpd_id.state != "approve":
            raise UserError(_("FPD harus berstatus Approved."))

        if self.fpd_id.rap_id != self.rap_id:
            raise UserError(_("FPD tidak sesuai dengan RAP."))
        # validasi service-only (double guard)
        for wl in self.line_ids:
            if wl.product_id and wl.product_id.type != "service":
                raise UserError(_("WO hanya boleh berisi product type Service."))

        po_vals = {
            "partner_id": self.partner_id.id,
            "fpd_id": self.fpd_id.id,
            "rap_id": self.rap_id.id,
            "pekerjaan_id": self.pekerjaan_id.id if self.pekerjaan_id else False,
            "sub_pekerjaan_id": self.sub_pekerjaan_id.id if self.sub_pekerjaan_id else False,
            "picking_type_id": self.picking_type_id.id,
            "expected_arrival": self.expected_arrival,
            "is_work_order": True,
        }
        po_vals = {k: v for k, v in po_vals.items() if v is not False}

        wo = self.env["purchase.order"].create(po_vals)

        planned_date = self.expected_arrival or fields.Datetime.now()
        line_vals_list = []
        for wl in self.line_ids:
            if not wl.product_id or wl.product_qty <= 0:
                continue
            line_vals_list.append({
                "order_id": wo.id,
                "product_id": wl.product_id.id,
                "product_qty": wl.product_qty,
                "product_uom_id": wl.product_uom.id,
                "price_unit": wl.price_unit,
                "date_planned": planned_date,
                "name": wl.name or wl.product_id.display_name,
            })

        if not line_vals_list:
            raise UserError(_("Tidak ada line yang dibuat. Cek qty/produk pada wizard."))

        self.env["purchase.order.line"].create(line_vals_list)

        return {
            "type": "ir.actions.act_window",
            "name": _("Work Order"),
            "res_model": "purchase.order",
            "view_mode": "form",
            "res_id": wo.id,
            "target": "current",
        }


class ProjectRapCreateWoWizardLine(models.TransientModel):
    _name = "project.rap.create.wo.wizard.line"
    _description = "Create WO Wizard Line"

    wizard_id = fields.Many2one(
        "project.rap.create.wo.wizard",
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
        string="Product (Service)",
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

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.name = rec.product_id.display_name
                rec.product_uom = rec.product_id.uom_id
