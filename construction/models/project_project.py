from odoo import models, fields


class ProjectProject(models.Model):
    _inherit = 'project.project'
    
    # Data Umum Proyek
    kantor_id = fields.Many2one('res.kantor', string='Kantor')
    status_mitra = fields.Selection([
        ('mitra', 'Mitra'),
        ('no_mitra', 'Tanpa Mitra'),
    ], string='Status Mitra')
    department_id = fields.Many2one('hr.department', string='Departemen')
    kode_project = fields.Char('Kode Project')
    kelompok_proyek_id = fields.Many2one('kelompok.proyek', string='Klp Proyek')
    bidang_id = fields.Many2one('res.bidang', string='Bidang')
    sub_bidang_id = fields.Many2one('res.sub.bidang', string='Sub Bidang')
    uraian_proyek = fields.Text('Uraian Proyek')

    # Data Kontrak
    no_sppbj = fields.Char('No SPPBJ')
    tgl_pra_kontrak = fields.Date('Tanggal Pra Kontrak')
    tgl_mulai_kontrak = fields.Date('Tanggal Mulai Kontrak')
    pho = fields.Date('PHO')
    tgl_selesai_kontrak = fields.Date('Tanggal Selesai Kontrak')
    waktu_kontrak_hari = fields.Integer('Waktu Kontrak (Hari)')
    tgl_selesai_pemeliharaan = fields.Date('Tanggal Selesai Pemeliharaan')
    waktu_pemeliharaan_hari = fields.Integer('Waktu Pemeliharaan (Hari)')
    tgl_fho = fields.Date('Tanggal FHO')
    tgl_sppbj = fields.Date('Tanggal SPPBJ')

    # Data Schedule
    tgl_mulai_schedule = fields.Date('Tanggal Mulai Schedule')
    tgl_selesai_schedule = fields.Date('Tanggal Selesai Schedule')
    waktu_pemeliharaan_hari = fields.Integer('Waktu Schedule (Hari)')
    waktu_pemeliharaan_minggu = fields.Integer('Waktu Schedule (Minggu)')

    # Data Lokasi & Kontrak
    nomor_kontrak = fields.Char('Nomor Kontrak')
    tgl_kontrak = fields.Date('Tanggal Kontrak')
    lokasi_proyek = fields.Char('Lokasi Proyek')
    kota_proyek = fields.Many2one('res.city', string='Kota Proyek')
    propinsi_proyek = fields.Many2one('res.country.state', string='Provinsi Proyek')
    

    # Data Keuangan
    nilai_kontrak = fields.Float('Nilai Kontrak')
    currecy_id = fields.Many2one('res.currency', string='Mata Uang')
    target_rap = fields.Float('Target RAP')
    nilai_pekerjaan_rap = fields.Float('Nilai Pek RAP')
    nilai_pekerjaan_kontrak = fields.Float('Nilai Pek Kontrak')
    status_proyek_id = fields.Many2one('status.proyek', string='Status Proyek')
    nilai_jasa = fields.Float('Nilai Jasa')
    pengguna_jasa = fields.Char('Pengguna Jasa')
    alamat_pengguna_jasa = fields.Text('Alamat Pengguna Jasa')
    ppn_dipotong = fields.Boolean('Potongan PPN')
    potongan_pph = fields.Float('Potongan PPh (%)')
