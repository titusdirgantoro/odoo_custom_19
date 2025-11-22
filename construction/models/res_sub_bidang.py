from odoo import models, fields


class ResSubBidang(models.Model):
    _name = 'res.sub.bidang'
    _description = 'Sub Bidang Proyek'

    name = fields.Char(required=True)
    code = fields.Char()
    bidang_id = fields.Many2one('res.bidang', string='Bidang', ondelete='restrict')
    active = fields.Boolean(default=True)

    def _compute_display_name(self):
        if self.code:
            self.display_name = f"{self.code} - {self.name}"
        else:
            self.display_name = self.name
