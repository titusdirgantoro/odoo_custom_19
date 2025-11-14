from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    type_master_data = fields.Selection(
        [
            ('bahan', 'Bahan'),
            ('upah', 'Upah'),
            ('overhead', 'Overhead'),
            ('jasa', 'Jasa'),
            ('sewa_alat', 'Sewa Alat'),
        ],
        string='Type Master Data',
        help='Menandai jenis master data produk untuk kebutuhan Construction.'
    )
