
from odoo import models, fields


class ConstructionUsageCategory(models.Model):
    _name = 'construction.usage.category'
    _description = 'Kategori Penggunaan Product'

    name = fields.Char(string='Kategori Penggunaan', required=True)
    active = fields.Boolean(default=True)

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name
