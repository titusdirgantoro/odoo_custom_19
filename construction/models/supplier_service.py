from odoo import models, fields


class SupplierService(models.Model):
    _name = 'supplier.service'
    _description = 'Layanan Pemasok'

    name = fields.Char(string='Nama Layanan', required=True)
    active = fields.Boolean(string='Aktif', default=True)
