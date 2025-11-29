from odoo import models, fields

class ConstructionEquipmentCategory(models.Model):
    _name = 'construction.equipment.category'
    _description = 'Kategori Alat Konstruksi'

    name = fields.Char(string='Nama Kategori', required=True)
    code = fields.Char(string='Kode')
    active = fields.Boolean(default=True)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.code} - {rec.name}" if rec.code else rec.name
