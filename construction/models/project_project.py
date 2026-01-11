from odoo import models, fields, api, _


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
    nilai_ppn_11 = fields.Float(
        string="Nilai PPN 11%",
        compute="_compute_construction_finance",
        store=True,
        readonly=True,
    )
    grand_total_kontrak = fields.Float(
        string="Grand Total Kontrak",
        compute="_compute_construction_finance",
        store=True,
        readonly=True,
    )
    nilai_potongan_pph = fields.Float(
        string="Nilai Potongan PPh",
        compute="_compute_construction_finance",
        store=True,
        readonly=True,
    )


    nilai_kontrak = fields.Float('Nilai Kontrak')
    currecy_id = fields.Many2one('res.currency', string='Mata Uang')
    target_rap = fields.Float('Target RAP')
    nilai_pekerjaan_rap = fields.Float(
        string="Nilai Pek. RAP",
        compute="_compute_construction_finance",
        store=True,
        readonly=True,
    )
    nilai_pekerjaan_kontrak = fields.Float(
        string="Nilai Pek. Kontrak",
        compute="_compute_construction_finance",
        store=True,
        readonly=True,
    )
    target_rap = fields.Float(
        string="Target RAP",
        compute="_compute_construction_finance",
        store=True,
        readonly=True,
        help="Target RAP = Nilai Pek. RAP / Nilai Dasar (DPP).",
    )

    nilai_pekerjaan_kontrak = fields.Float('Nilai Pek Kontrak')
    status_proyek_id = fields.Many2one('status.proyek', string='Status Proyek')
    nilai_jasa = fields.Float('Nilai Jasa')
    pengguna_jasa = fields.Char('Pengguna Jasa')
    alamat_pengguna_jasa = fields.Text('Alamat Pengguna Jasa')
    ppn_dipotong = fields.Boolean('Potongan PPN')
    potongan_pph = fields.Float('Potongan PPh (%)')

    @api.depends(
        "nilai_kontrak",
        "ppn_dipotong",
        "potongan_pph",
    )
    def _compute_construction_finance(self):
        """
        Perhitungan:
        - include PPN (ppn_dipotong = True):
            nilai_kontrak dianggap sudah termasuk PPN
            DPP = nilai_kontrak / 1.11
            PPN = nilai_kontrak - DPP
            Grand Total = nilai_kontrak
        - exclude PPN (ppn_dipotong = False):
            nilai_kontrak dianggap belum termasuk PPN
            PPN = nilai_kontrak * 0.11
            Grand Total = nilai_kontrak + PPN
            DPP = nilai_kontrak

        Target RAP:
            Nilai Pek. RAP / DPP

        Nilai Potongan PPh:
            DPP * (potongan_pph / 100)
        """
        ProjectRap = self.env["project.rap"]
        PurchaseOrder = self.env["purchase.order"]

        for project in self:
            nilai_kontrak = project.nilai_kontrak or 0.0

            # --- DPP / PPN / Grand Total ---
            if project.ppn_dipotong:
                # nilai_kontrak sudah termasuk PPN
                dpp = nilai_kontrak / 1.11 if nilai_kontrak else 0.0
                nilai_ppn = nilai_kontrak - dpp
                grand_total = nilai_kontrak
            else:
                # nilai_kontrak belum termasuk PPN
                nilai_ppn = nilai_kontrak * 0.11
                grand_total = nilai_kontrak + nilai_ppn
                dpp = nilai_kontrak

            # --- Nilai Pek. RAP (sum pekerjaan pada RAP type 'rap' untuk proyek ini) ---
            rap = ProjectRap.search(
                [("project_id", "=", project.id), ("type", "=", "rap")],
                order="id desc",
                limit=1,
            )
            nilai_pekerjaan_rap = 0.0
            if rap:
                # total_harga di project.pekerjaan sudah compute
                nilai_pekerjaan_rap = sum(rap.pekerjaan_ids.mapped("total_harga"))

            # --- Nilai Pek. Kontrak (sum pengeluaran dari PO) ---
            # Catatan: project_id pada PO harus sudah ada & store (related rap_id.project_id) dari implementasi sebelumnya
            po_domain = [
                ("project_id", "=", project.id),
                ("state", "in", ("purchase", "done")),
            ]
            # pakai amount_untaxed supaya sejajar dengan DPP; kalau mau amount_total tinggal ganti
            nilai_pekerjaan_kontrak = sum(PurchaseOrder.search(po_domain).mapped("amount_untaxed"))

            # --- Target RAP ---
            target_rap = (nilai_pekerjaan_rap / dpp) if dpp else 0.0

            # --- Potongan PPh (persen) ---
            pph_pct = project.potongan_pph or 0.0
            nilai_potongan_pph = dpp * (pph_pct / 100.0)

            # assign hasil
            project.nilai_ppn_11 = nilai_ppn
            project.grand_total_kontrak = grand_total
            project.nilai_pekerjaan_rap = nilai_pekerjaan_rap
            project.nilai_pekerjaan_kontrak = nilai_pekerjaan_kontrak
            project.target_rap = target_rap
            project.nilai_potongan_pph = nilai_potongan_pph