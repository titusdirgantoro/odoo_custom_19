from odoo import models, fields


class SupplierCategory(models.Model):
    _name = 'supplier.category'
    _description = 'Kategori Pemasok'

    name = fields.Char(string='Nama Kategori', required=True)
    code = fields.Char(string='Kode Kategori', required=True)
    active = fields.Boolean(string='Aktif', default=True)

    def _compute_display_name(self):
        """Tampilkan 'code - name' jika code ada, kalau tidak hanya name."""
        for rec in self:
            if rec.code and rec.name:
                rec.display_name = f"{rec.code} - {rec.name}"
            else:
                rec.display_name = rec.name or rec.code or ''
