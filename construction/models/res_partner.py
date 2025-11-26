from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # =========================
    # A. Identitas Pemasok
    # =========================
    kode_pemasok = fields.Char(string='Kode Pemasok')
    status_pemasok = fields.Selection([
        ('aktif', 'Aktif'),
        ('non_aktif', 'Non Aktif'),
    ], string='Status Pemasok')
    blacklist_status = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Blacklist (BL)')
    kategori_pemasok_ids = fields.Many2many(
        'supplier.category',
        string='Kategori Pemasok',
        help="Kategori internal pemasok: Bahan, Upah, Sewa Alat, Subkon, Overhead, Jasa."
    )
    layanan_id = fields.Many2one(
        'supplier.service',
        string='Layanan',
        help="Jenis barang/jasa yang disediakan pemasok."
    )

    # =========================
    # B. Data Keuangan
    # =========================
    no_pkp = fields.Char(string='No PKP')
    no_fp = fields.Char(string='No FP')
    # harus_ppn = fields.Boolean(
    #     string='Harus PPN',
    #     help='Centang jika transaksi dengan pemasok ini wajib dikenai PPN.'
    # )
    # npwp = fields.Char(string='NPWP')
    npwp16 = fields.Char(string='NPWP 16 Digit')
    ktp = fields.Char(string='KTP')

    # =========================
    # E. Data Personalia
    # =========================
    nama_pimpinan = fields.Char(string='Nama Pimpinan')
    hp_pimpinan = fields.Char(string='HP Pimpinan')
    kontak_person_1 = fields.Char(string='Kontak Person 1')
    hp_kontak_1 = fields.Char(string='HP Kontak 1')
    kontak_person_2 = fields.Char(string='Kontak Person 2')
    hp_kontak_2 = fields.Char(string='HP Kontak 2')

    # =========================
    # C, D, F menggunakan field standar res.partner
    # =========================
    # C. Data Alamat & Lokasi:
    #    - street      : Alamat 1
    #    - street2     : Alamat 2 (jika perlu)
    #    - zip         : Kode Pos
    #    - city        : Kabupaten / Kota
    #    - state_id    : Provinsi
    #    - country_id  : Negara
    #
    # D. Data Kontak:
    #    - phone   : Telepon kantor
    #    - mobile  : HP umum
    #    - fax     : Fax
    #    - email   : Email
    #    - website : Website
    nomor_fax = fields.Char('Nomor FAX')
    #
    # F. Data Rekening Bank:
    #    - bank_ids (res.partner.bank): data rekening bank pemasok
