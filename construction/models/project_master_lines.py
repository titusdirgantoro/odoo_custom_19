# -*- coding: utf-8 -*-
from odoo import models, fields


class ProjectMasterBahan(models.Model):
    _name = "project.master.bahan"
    _description = "Master Bahan (RAP/PFC)"
    _inherit = "project.master.line.mixin"

    product_id = fields.Many2one(
        "product.template",
        required=True,
        domain=[("type_master_data", "=", "bahan")],
    )


class ProjectMasterUpah(models.Model):
    _name = "project.master.upah"
    _description = "Master Upah (RAP/PFC)"
    _inherit = "project.master.line.mixin"

    product_id = fields.Many2one(
        "product.template",
        required=True,
        domain=[("type_master_data", "=", "upah")],
    )


class ProjectMasterSewaAlat(models.Model):
    _name = "project.master.sewa.alat"
    _description = "Master Sewa Alat (RAP/PFC)"
    _inherit = "project.master.line.mixin"

    product_id = fields.Many2one(
        "product.template",
        required=True,
        domain=[("type_master_data", "=", "sewa_alat")],
    )


class ProjectMasterOverhead(models.Model):
    _name = "project.master.overhead"
    _description = "Master Overhead (RAP/PFC)"
    _inherit = "project.master.line.mixin"

    product_id = fields.Many2one(
        "product.template",
        required=True,
        domain=[("type_master_data", "=", "overhead")],
    )


class ProjectMasterJasa(models.Model):
    _name = "project.master.jasa"
    _description = "Master Jasa (RAP/PFC)"
    _inherit = "project.master.line.mixin"

    product_id = fields.Many2one(
        "product.template",
        required=True,
        domain=[("type_master_data", "=", "jasa")],
    )
