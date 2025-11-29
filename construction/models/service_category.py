from odoo import models, fields

class ConstructionServiceCategory(models.Model):
    _name = 'construction.service.category'
    _description = 'Kategori Jasa Konstruksi'

    name = fields.Char(string='Nama Kategori', required=True)
    code = fields.Char(string='Kode')
    active = fields.Boolean(default=True)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.code} - {rec.name}" if rec.code else rec.name
