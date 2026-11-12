import unittest
import pandas as pd
from engine import compare, display_result, initialize, prepare, prepare_auto, read_csv


def rows(values):
    return prepare(pd.DataFrame(values, columns=["id_rencana_kontrol", "no_surat_kontrol", "inserted_date", "updated_date", "respon_bpjs"]), "id_rencana_kontrol", "no_surat_kontrol")


class ComparisonTests(unittest.TestCase):
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

    def test_hide_equal_values_without_changing_source(self):
        base = rows([['1', 'HDUL', '2026-01-10', '2026-01-10', 'sama'], ['2', '', '2026-01-10', '2026-01-10', 'sama']])
        new = rows([['1', 'HDUL', '2026-01-10', '2026-01-10', 'sama'], ['2', '', '2026-01-10', '2026-01-10', 'berbeda']])
        result, _ = compare(initialize(base), new)
        shown = display_result(result)
        self.assertEqual(shown.iloc[0]['no_surat_kontrol_baru'], '')
        self.assertEqual(shown.iloc[0]['updated_date_baru'], '')
        self.assertEqual(shown.iloc[1]['respon_bpjs_baru'], 'berbeda')
        self.assertEqual(result.iloc[0]['no_surat_kontrol_baru'], 'HDUL')
        self.assertEqual(shown.iloc[1]['kategori_awal'], 'Tidak HDUL')

if __name__ == '__main__':
    unittest.main()
