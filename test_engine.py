import unittest
from datetime import date
import pandas as pd
from engine import META, compare, display_result, initialize, prepare, prepare_auto, read_csv, restore_dataset


def rows(values):
    return prepare(pd.DataFrame(values, columns=["id_rencana_kontrol", "no_surat_kontrol", "inserted_date", "updated_date", "respon_bpjs"]), "id_rencana_kontrol", "no_surat_kontrol")


class ComparisonTests(unittest.TestCase):
    def test_restore_source_only_sheet_creates_missing_result_columns(self):
        source = rows([['1', 'HDUL', '2026-11-09', '2026-11-09', 'gagal']])
        source = source.rename(columns={'id_rencana_kontrol': ' ID_RENCANA_KONTROL '})
        restored = restore_dataset(source)
        self.assertEqual(restored.loc[0, 'id_rencana_kontrol'], '1')
        self.assertEqual(restored.loc[0, 'respon_bpjs'], 'gagal')
        self.assertEqual(restored.loc[0, 'kategori_awal'], 'HDUL')
        self.assertTrue(all(col in restored for col in META))
        restored.loc[0, 'no_surat_kontrol_baru'] = '123'
        self.assertEqual(restore_dataset(restored).loc[0, 'no_surat_kontrol_baru'], '123')
        with self.assertRaisesRegex(ValueError, 'inserted_date'):
            restore_dataset(source.drop(columns=['inserted_date']))

    def test_identical_hdul_does_not_fill_join_columns(self):
        base = rows([['1', 'RAWAT-JALAN-BPJSHDUL-1850282-1794225453632',
                      '2026-11-09', '2026-11-09 18:57:37.827',
                      'Surat Rujukan ini Masa Berlaku Habis']])
        saved = initialize(base, day=date(2026, 11, 9))
        # Reproduce the previously saved result with redundant comparison values.
        for source, target in [('no_surat_kontrol', 'no_surat_kontrol_baru'),
                               ('respon_bpjs', 'respon_bpjs_baru'),
                               ('updated_date', 'updated_date_baru')]:
            saved[target] = base[source]
        saved['ketersediaan_data'] = 'Belum ada data terbaru'
        for day in [date(2026, 11, 13), date(2026, 11, 14)]:
            saved, _ = compare(saved, base, day=day)
            self.assertEqual(saved.loc[0, 'ketersediaan_data'], 'Belum ada data terbaru')
            self.assertEqual(saved.loc[0, 'kategori'], 'Belum diubah, melewati target')
            self.assertEqual(saved.loc[0, 'tanggal_pengambilan_data'], day.isoformat())
            for col in ['no_surat_kontrol_baru', 'respon_bpjs_baru', 'updated_date_baru']:
                self.assertEqual(saved.loc[0, col], '', col)
            self.assertEqual(saved.loc[0, 'no_surat_kontrol'], base.loc[0, 'no_surat_kontrol'])

    def test_unchanged_import_is_not_reported_as_new_data(self):
        base = rows([['1', 'HDUL', '2026-01-10', '2026-01-10 00:00:00', 'gagal']])
        same = rows([['1', 'HDUL', '2026-01-10', '2026-01-10T00:00:00', 'gagal']])
        result, _ = compare(initialize(base, day=date(2026, 1, 10)), same, day=date(2026, 1, 13))
        self.assertEqual(result.loc[0, 'ketersediaan_data'], 'Belum ada data terbaru')
        self.assertEqual(result.loc[0, 'kategori'], 'Belum diubah, melewati target')
        changed = same.copy()
        changed.loc[0, 'respon_bpjs'] = 'berbeda'
        result, _ = compare(result, changed, day=date(2026, 1, 13))
        self.assertEqual(result.loc[0, 'ketersediaan_data'], 'Ditemukan')
        result, _ = compare(result, changed, day=date(2026, 1, 14))
        self.assertEqual(result.loc[0, 'ketersediaan_data'], 'Belum ada data terbaru')

    def test_new_ids_are_appended_with_all_columns(self):
        base = prepare_auto(pd.DataFrame([{
            'id_rencana_kontrol': '1', 'no_surat_kontrol': 'HDUL',
            'inserted_date': '2026-01-10', 'updated_date': '2026-01-10',
            'respon_bpjs': 'gagal', 'nama_pasien': 'Lama',
        }]))
        latest = prepare_auto(pd.DataFrame([
            {'id_rencana_kontrol': '1', 'no_surat_kontrol': '123', 'inserted_date': '2026-01-10', 'updated_date': '2026-01-12', 'respon_bpjs': 'ok', 'nama_pasien': 'Lama', 'kolom_tambahan': 'a'},
            {'id_rencana_kontrol': '2', 'no_surat_kontrol': '456', 'inserted_date': '2026-01-12', 'updated_date': '2026-01-12', 'respon_bpjs': 'ok', 'nama_pasien': 'Baru', 'kolom_tambahan': 'b'},
        ]))
        result, new = compare(initialize(base), latest, day=date(2026, 1, 12))
        self.assertEqual(result['id_rencana_kontrol'].tolist(), ['1', '2'])
        self.assertEqual(result.iloc[1]['nama_pasien'], 'Baru')
        self.assertEqual(result.iloc[1]['kolom_tambahan'], 'b')
        self.assertEqual(result.iloc[1]['tanggal_pengambilan_data'], '2026-01-12')
        self.assertEqual(result.iloc[1]['ketersediaan_data'], 'Data awal')
        self.assertEqual(new['id_rencana_kontrol'].tolist(), ['2'])
        again, new_again = compare(result, latest, day=date(2026, 1, 12))
        self.assertEqual(again['id_rencana_kontrol'].tolist(), ['1', '2'])
        self.assertTrue(new_again.empty)

    def test_new_id_uses_existing_columns_despite_header_case_or_spaces(self):
        base = prepare_auto(pd.DataFrame([{
            'id_rencana_kontrol': '1', 'no_surat_kontrol': 'HDUL',
            'inserted_date': '2026-01-10', 'updated_date': '2026-01-10',
            'respon_bpjs': 'gagal', 'nama_pasien': 'Lama',
        }]))
        latest = prepare_auto(pd.DataFrame([{
            'id_rencana_kontrol': '2', 'no_surat_kontrol': '123',
            'inserted_date': '2026-01-12', 'updated_date': '2026-01-12',
            'respon_bpjs': 'ok', ' Nama_Pasien ': 'Baru',
        }]))
        result, _ = compare(initialize(base), latest, day=date(2026, 1, 12))
        self.assertEqual(result['id_rencana_kontrol'].tolist(), ['1', '2'])
        self.assertEqual(result.loc[1, 'nama_pasien'], 'Baru')
        self.assertNotIn(' Nama_Pasien ', result.columns)
        self.assertEqual(result.loc[1, 'no_surat_kontrol_baru'], '')
        again, _ = compare(result, latest, day=date(2026, 1, 12))
        self.assertEqual(again['id_rencana_kontrol'].tolist(), ['1', '2'])

    def test_left_join_and_timestamp_categories(self):
        initial = rows([
            ["001", "HDUL", "2026-01-10 10:00:00", "2026-01-10 10:00:00", "gagal"],
            ["002", "HDUL", "2026-01-10 10:00:00", "2026-01-10 10:00:00", "gagal"],
            ["003", "HDUL", "2026-01-10 10:00:00", "2026-01-10 10:00:00", "gagal"],
            ["004", "123", "2026-01-10 10:00:00", "2026-01-10 10:00:00", "ok"],
            ["005", "HDUL", "2026-01-10 10:00:00", "2026-01-10 10:00:00", "gagal"],
        ])
        latest = rows([
            ["001", "123", "2026-01-10 10:00:00", "2026-01-12 10:00:00", "ok"],
            ["002", "456", "2026-01-10 10:00:00", "2026-01-12 10:00:01", "ok"],
            ["003", "hdul", "2026-01-10 10:00:00", "2026-01-12 10:00:00", "gagal"],
            ["004", "123", "2026-01-10 10:00:00", "2026-01-12 10:00:00", "ok"],
            ["006", "789", "2026-01-10 10:00:00", "2026-01-12 10:00:00", "ok"],
        ])
        result, new = compare(initialize(initial), latest)
        self.assertEqual(result['kategori'].tolist()[:4], ['Sesuai target', 'Melewati target', 'Tidak diubah', 'Tidak HDUL'])
        self.assertEqual(result.iloc[0]['no_surat_kontrol'], 'HDUL')
        self.assertEqual(result.iloc[0]['no_surat_kontrol_baru'], '123')
        self.assertEqual(result.iloc[0]['respon_bpjs_baru'], 'ok')
        self.assertEqual(result.iloc[0]['updated_date_baru'], '2026-01-12 10:00:00')
        self.assertEqual(result.iloc[4]['ketersediaan_data'], 'Belum ada data terbaru')
        self.assertEqual(new.iloc[0]['id_rencana_kontrol'], '006')

    def test_missing_or_unchanged_update_does_not_prove_completion(self):
        base = rows([['1', 'HDUL', '2026-01-10', '2026-01-10', 'gagal']])
        latest = rows([['1', '123', '2026-01-10', '2026-01-10', 'ok']])
        result, _ = compare(initialize(base), latest)
        self.assertTrue(result.iloc[0]['kategori'].startswith('Perlu diperiksa'))
        latest.loc[0, 'updated_date'] = 'invalid'
        result, _ = compare(initialize(base), latest)
        self.assertEqual(result.iloc[0]['updated_date_berubah'], 'Tidak diketahui')

    def test_duplicate_and_text_id(self):
        df = read_csv(b'id_rencana_kontrol,no_surat_kontrol,inserted_date,updated_date,respon_bpjs\n001,HDUL,2026-01-10,2026-01-10,gagal\n')
        self.assertEqual(df.iloc[0]['id_rencana_kontrol'], '001')
        with self.assertRaises(ValueError):
            prepare(pd.concat([df, df], ignore_index=True), 'id_rencana_kontrol', 'no_surat_kontrol')

    def test_auto_csv_and_headers(self):
        for sep in [',', ';', '\t', '|']:
            content = sep.join([' ID_RENCANA_KONTROL ', 'no_surat_kontrol', 'inserted_date', 'updated_date', 'respon_bpjs']) + '\n' + sep.join(['001', 'HDUL', '2026-01-10', '2026-01-10', 'gagal']) + '\n'
            result = prepare_auto(read_csv(content.encode()))
            self.assertEqual(result.iloc[0]['id_rencana_kontrol'], '001')
            self.assertEqual(initialize(result).iloc[0]['kategori_awal'], 'HDUL')

    def test_empty_unnamed_columns_are_removed_without_losing_data(self):
        content = (b'id_rencana_kontrol,no_surat_kontrol,inserted_date,updated_date,respon_bpjs,,\n'
                   b'1,HDUL,2026-01-10,2026-01-10,gagal,,ada isi\n')
        imported = read_csv(content)
        self.assertNotIn('Unnamed: 5', imported.columns)
        self.assertEqual(imported.loc[0, 'Unnamed: 6'], 'ada isi')
        base = initialize(prepare_auto(imported))
        base['Unnamed: 26'] = ''
        result, _ = compare(base, prepare_auto(imported), day=date(2026, 1, 12))
        self.assertNotIn('Unnamed: 26', result.columns)
        self.assertEqual(result.loc[0, 'Unnamed: 6'], 'ada isi')

    def test_hide_equal_values_without_changing_source(self):
        base = rows([['1', 'HDUL', '2026-01-10', '2026-01-10', 'sama'], ['2', '', '2026-01-10', '2026-01-10', 'sama']])
        new = rows([['1', 'HDUL', '2026-01-10', '2026-01-10', 'sama'], ['2', '', '2026-01-10', '2026-01-10', 'berbeda']])
        result, _ = compare(initialize(base), new)
        shown = display_result(result)
        self.assertEqual(shown.iloc[0]['no_surat_kontrol_baru'], '')
        self.assertEqual(shown.iloc[0]['updated_date_baru'], '')
        self.assertEqual(shown.iloc[1]['respon_bpjs_baru'], 'berbeda')
        self.assertEqual(result.iloc[0]['no_surat_kontrol_baru'], '')
        self.assertEqual(shown.iloc[1]['kategori_awal'], 'Tidak HDUL')

if __name__ == '__main__':
    unittest.main()
