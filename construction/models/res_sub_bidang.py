from odoo import models, fields


class ResSubBidang(models.Model):
    _name = 'res.sub.bidang'
    _description = 'Sub Bidang Proyek'

    name = fields.Char(required=True)
    code = fields.Char()
    bidang_id = fields.Many2one('res.bidang', string='Bidang', ondelete='restrict')
    active = fields.Boolean(default=True)

    def _compute_display_name(self):
        for rec in self:
            if rec.code:
                rec.display_name = f"{rec.code} - {rec.name}"
            else:
                rec.display_name = rec.name
