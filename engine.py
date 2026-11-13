"""Pencocokan data rencana kontrol berdasarkan isi dan timestamp sumber."""
import io
import csv
import re
from datetime import datetime

import pandas as pd

KEY = "id_rencana_kontrol"
SURAT = "no_surat_kontrol"
INSERTED = "inserted_date"
UPDATED = "updated_date"
RESPON = "respon_bpjs"
SOURCE = [KEY, SURAT, INSERTED, UPDATED, RESPON]
META = ["kategori_awal", "no_surat_kontrol_baru", "respon_bpjs_baru", "updated_date_baru", "updated_date_berubah", "durasi_jam", "tanggal_pengambilan_data", "kategori", "ketersediaan_data"]


def drop_empty_unnamed(df):
    columns = [col for col in df.columns
               if re.fullmatch(r"Unnamed: \d+(?:_level_\d+)?", str(col), re.IGNORECASE)
               and df[col].fillna("").astype(str).str.strip().eq("").all()]
    return df.drop(columns=columns)


def read_csv(data, separator=None, encoding=None):
    if encoding is None:
        try:
            content = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            content = data.decode("cp1252")
    else:
        content = data.decode(encoding)
    if separator is None:
        try:
            separator = csv.Sniffer().sniff("\n".join(content.splitlines()[:30]), delimiters=",;\t|").delimiter
        except csv.Error as exc:
            raise ValueError("Pemisah CSV tidak dapat dikenali. Periksa format file.") from exc
    df = pd.read_csv(io.StringIO(content), sep=separator, dtype=str, keep_default_na=False)
    if df.columns.duplicated().any():
        raise ValueError("Nama kolom harus unik.")
    return drop_empty_unnamed(df)


def read_excel(data, sheet=0):
    return drop_empty_unnamed(pd.read_excel(io.BytesIO(data), sheet_name=sheet, dtype=str, keep_default_na=False, engine="openpyxl"))


def prepare(df, key=KEY, surat=SURAT, inserted=INSERTED, updated=UPDATED, respon=RESPON):
    selected = [key, surat, inserted, updated, respon]
    if len(set(selected)) != len(selected) or any(c not in df.columns for c in selected):
        raise ValueError("Pilih lima kolom sumber yang berbeda dan tersedia.")
    mapping = dict(zip(selected, SOURCE))
    if any(c in (set(SOURCE) | set(META)) and c not in selected for c in df.columns):
        raise ValueError("Nama kolom bertabrakan dengan kolom hasil.")
    out = df.rename(columns=mapping).copy().fillna("")
    for c in out.columns:
        out[c] = out[c].astype(str).str.strip()
    out.loc[out[SURAT].eq(""), SURAT] = "-"
    bad = out[KEY].eq("") | out[KEY].duplicated(keep=False)
    if bad.any():
        raise ValueError("ID kosong atau berulang pada baris: " + ", ".join(str(i + 2) for i in out.index[bad][:20]))
    return out


def prepare_auto(df):
    columns = {}
    for name in df.columns:
        normalized = str(name).strip().lower()
        if normalized in columns:
            raise ValueError(f"Nama kolom tidak unik setelah dirapikan: {normalized}")
        columns[normalized] = name
    missing = [name for name in SOURCE if name not in columns]
    if missing:
        raise ValueError("Kolom wajib tidak ditemukan: " + ", ".join(missing))
    return prepare(df, *(columns[name] for name in SOURCE))


def kind(value):
    value = str(value or "").strip()
    if "hdul" in value.lower():
        return "hdul"
    return "empty" if value in ("", "-") else "filled"


def category_initial(value):
    return "HDUL" if kind(value) == "hdul" else "Tidak HDUL"


def restore_dataset(df):
    out = drop_empty_unnamed(df).copy().fillna("")
    columns = {}
    for col in out.columns:
        normalized = str(col).strip().lower()
        if normalized in columns:
            raise ValueError(f"Nama kolom dataset tersimpan tidak unik: {normalized}")
        columns[normalized] = col
    missing = [col for col in SOURCE if col not in columns]
    if missing:
        raise ValueError("Kolom wajib pada tab Data belum tersedia: " + ", ".join(missing))
    out = out.rename(columns={original: normalized for normalized, original in columns.items()
                              if normalized in SOURCE or normalized in META})
    for col in META:
        if col not in out:
            out[col] = ""
    out["kategori_awal"] = out[SURAT].map(category_initial)
    return out


def display_result(df):
    """Sembunyikan nilai pembanding yang sama tanpa membuang nilai aslinya."""
    out = df.copy()
    for original, new in [(SURAT, "no_surat_kontrol_baru"), (RESPON, "respon_bpjs_baru"), (UPDATED, "updated_date_baru")]:
        if new not in out or original not in out:
            continue
        for idx in out.index:
            a, b = str(out.at[idx, original]).strip(), str(out.at[idx, new]).strip()
            equal = a == b or (a in ("", "-") and b in ("", "-"))
            if original == UPDATED and not equal:
                first, second = timestamp(a), timestamp(b)
                equal = first is not None and second is not None and first == second
            if equal:
                out.at[idx, new] = ""
    return out


def timestamp(value):
    """Format ISO eksplisit; timestamp tanpa zona dibandingkan tanpa konversi zona."""
    try:
        return datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def same_value(column, first, second):
    first, second = str(first).strip(), str(second).strip()
    if column == SURAT and first in ("", "-") and second in ("", "-"):
        return True
    if column == UPDATED:
        a, b = timestamp(first), timestamp(second)
        if a is not None and b is not None:
            return a == b
    return first == second


def ongoing_category(inserted, day):
    start = timestamp(inserted)
    if start is None or day is None or day < start.date():
        return "Perlu diperiksa: tanggal tidak valid atau belum tersedia"
    if (day - start.date()).days <= 2:
        return "Belum diubah, masih dalam target"
    return "Belum diubah, melewati target"


def initialize(df, day=None):
    out = df.drop(columns=[c for c in META if c in df], errors="ignore").copy()
    for col in META:
        out[col] = ""
    out["kategori_awal"] = out[SURAT].map(category_initial)
    out["tanggal_pengambilan_data"] = day.isoformat() if day else ""
    out["kategori"] = out[SURAT].map(lambda x: "Tidak HDUL" if kind(x) == "filled" else "Belum ada pembanding")
    for idx, row in out.iterrows():
        if kind(row[SURAT]) == "hdul":
            out.at[idx, "kategori"] = ongoing_category(row[INSERTED], day)
    out["ketersediaan_data"] = "Data awal"
    return out


def compare(base, newer, day=None):
    base, newer = drop_empty_unnamed(base), drop_empty_unnamed(newer)
    base_names = {}
    for col in base.columns:
        normalized = str(col).strip().casefold()
        if normalized in base_names:
            raise ValueError(f"Nama kolom dataset tersimpan tidak unik setelah dirapikan: {normalized}")
        base_names[normalized] = col
    rename = {col: base_names[str(col).strip().casefold()] for col in newer.columns
              if str(col).strip().casefold() in base_names}
    if any(target in META for target in rename.values()):
        raise ValueError("Nama kolom file bertabrakan dengan kolom hasil.")
    newer = newer.rename(columns=rename)
    if newer.columns.duplicated().any():
        raise ValueError("Nama kolom file tidak unik setelah disesuaikan dengan dataset tersimpan.")
    for frame in (base, newer):
        if any(c not in frame for c in SOURCE):
            raise ValueError("Dataset lama belum memiliki kolom timestamp dan respons. Impor ulang data awal dengan format baru.")
        if frame[KEY].duplicated().any() or frame[KEY].eq("").any():
            raise ValueError("ID kosong atau duplikat.")
    incoming = newer.set_index(KEY)
    result = base.copy().fillna("")
    for col in META:
        if col not in result:
            result[col] = ""
    result["kategori_awal"] = result[SURAT].map(category_initial)
    for idx, row in result.iterrows():
        key = row[KEY]
        if key not in incoming.index:
            for col in ["no_surat_kontrol_baru", "respon_bpjs_baru", "updated_date_baru", "updated_date_berubah"]:
                result.at[idx, col] = ""
            result.at[idx, "ketersediaan_data"] = "Belum ada data terbaru"
            result.at[idx, "kategori"] = "Belum ada data terbaru"
            result.at[idx, "durasi_jam"] = ""
            result.at[idx, "tanggal_pengambilan_data"] = day.isoformat() if day and kind(row[SURAT]) == "hdul" else ""
            continue
        update = incoming.loc[key]
        previous_columns = {SURAT: "no_surat_kontrol_baru", RESPON: "respon_bpjs_baru", UPDATED: "updated_date_baru"}
        has_previous = row.get("ketersediaan_data") != "Data awal" and any(
            str(row.get(col, "")).strip() for col in previous_columns.values()
        )
        unchanged = all(same_value(col, row[previous_columns[col]] if has_previous else row[col], update[col])
                        for col in previous_columns)
        result.at[idx, "ketersediaan_data"] = "Belum ada data terbaru" if unchanged else "Ditemukan"
        result.at[idx, "tanggal_pengambilan_data"] = day.isoformat() if day else ""
        result.at[idx, "no_surat_kontrol_baru"] = update[SURAT]
        result.at[idx, "respon_bpjs_baru"] = update[RESPON]
        result.at[idx, "updated_date_baru"] = update[UPDATED]
        before, after = timestamp(row[UPDATED]), timestamp(update[UPDATED])
        initial, latest = kind(row[SURAT]), kind(update[SURAT])
        result.at[idx, "durasi_jam"] = ""
        try:
            changed = before != after if before is not None and after is not None else None
            if changed is not None and (before.tzinfo is None) != (after.tzinfo is None):
                changed = None
        except (TypeError, ValueError):
            changed = None
        result.at[idx, "updated_date_berubah"] = "Ya" if changed else "Tidak" if changed is False else "Tidak diketahui"
        if initial == "filled":
            category = "Tidak HDUL" if latest != "hdul" else "Perlu diperiksa: kembali HDUL"
        elif initial == "empty" or latest == "empty":
            category = "Perlu diperiksa"
        elif latest == "hdul":
            category = ongoing_category(row[INSERTED], day)
        else:
            start, end = timestamp(row[INSERTED]), timestamp(update[UPDATED])
            try:
                hours = (end - start).total_seconds() / 3600 if start and end else None
            except TypeError:
                hours = None
            if hours is None or hours < 0:
                category = "Perlu diperiksa: tanggal tidak valid"
            else:
                result.at[idx, "durasi_jam"] = f"{hours:.2f}"
                days = (end.date() - start.date()).days
                category = "Sesuai target" if days <= 2 else "Melewati target"
        result.at[idx, "kategori"] = category
        if all(same_value(col, row[col], update[col]) for col in previous_columns):
            for col in previous_columns.values():
                result.at[idx, col] = ""
    new_rows = newer[~newer[KEY].isin(base[KEY])].copy()
    if not new_rows.empty:
        result = pd.concat([result, initialize(new_rows, day=day)], ignore_index=True).fillna("")
    return result, new_rows
