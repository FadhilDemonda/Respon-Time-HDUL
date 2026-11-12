/**
 * GOOGLE APPS SCRIPT: DASHBOARD & VISUALISASI MONITORING HDUL
 * -------------------------------------------------------------------
 * Penulis: Antigravity Assistant
 * Deskripsi: Mengolah dan memvisualisasikan data rencana kontrol pasien dari tab "Data",
 *            khususnya evaluasi status HDUL (Sesuai target <= 2 hari, Melewati target > 2 hari,
 *            Belum diubah/masih HDUL, dan Belum ada data terbaru / perlu diperiksa).
 */

const HDUL_CONFIG = {
  SOURCE_SHEET: "Data",
  DASHBOARD_SHEET: "Dashboard HDUL",
  SPREADSHEET_ID: "1dbUFFyyseXObg7r4jLofnTrUcWycte4YryeSH62GuII", // ID spreadsheet otomatis jika dibuka via Web App URL
  COLORS: {
    PRIMARY: "#1E293B",      // Navy slate
    HEADER_BG: "#0F172A",    // Dark slate
    SESUAI_TARGET: "#10B981",// Emerald green
    MELEWATI_TARGET: "#F59E0B", // Amber / orange
    MASIH_DALAM: "#3B82F6",  // Blue
    MASIH_LEWAT: "#EF4444",  // Red alert
    TIDAK_DIKETAHUI: "#94A3B8", // Slate gray
    TIDAK_HDUL: "#0D9488",   // Teal
    CARD_BG: "#F8FAFC",
    BORDER: "#CBD5E1"
  }
};

/**
 * FUNGSI WEB APP: doGet(e)
 * Dijalankan otomatis saat skrip dibuka melalui link Web App di browser
 */
function doGet(e) {
  return HtmlService.createHtmlOutputFromFile('DashboardUI')
    .setTitle('📊 Dashboard Monitoring HDUL')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * Mendapatkan referensi Spreadsheet aktif atau via ID (untuk Web App)
 */
function getSpreadsheet_() {
  let ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) {
    try {
      ss = SpreadsheetApp.openById(HDUL_CONFIG.SPREADSHEET_ID);
    } catch (err) {
      throw new Error("Tidak dapat membuka spreadsheet. Pastikan izin akses telah diberikan.");
    }
  }
  return ss;
}

/**
 * Menu otomatis saat Spreadsheet dibuka
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('📊 Dashboard HDUL')
    .addItem('🚀 Buat / Perbarui Dashboard', 'buildDashboard')
    .addItem('📈 Buka Visualisasi Interaktif (Popup)', 'openInteractiveDashboard')
    .addSeparator()
    .addItem('ℹ️ Panduan & Info Indikator', 'showHelpDialog')
    .addToUi();
}

/**
 * Fungsi Utama: Membuat atau memperbarui sheet Dashboard HDUL
 */
function buildDashboard() {
  const ss = getSpreadsheet_();
  let ui = null;
  try {
    ui = SpreadsheetApp.getUi();
  } catch (e) {
    // Dipanggil di luar konteks UI interaktif
  }
  
  // 1. Ambil & Proses Data
  let processed;
  try {
    processed = processData_();
  } catch (err) {
    if (ui) ui.alert("⚠️ Terjadi Kesalahan", err.message, ui.ButtonSet.OK);
    Logger.log("Error: " + err.message);
    return;
  }
  
  const dailyList = processed.dailyList;
  const totalAll = processed.totalAll;
  
  if (dailyList.length === 0) {
    if (ui) ui.alert("⚠️ Data Kosong", "Tidak ditemukan baris data yang valid pada tab '" + HDUL_CONFIG.SOURCE_SHEET + "'.", ui.ButtonSet.OK);
    return;
  }
  
  // 2. Siapkan Sheet Dashboard
  let dashSheet = ss.getSheetByName(HDUL_CONFIG.DASHBOARD_SHEET);
  if (!dashSheet) {
    dashSheet = ss.insertSheet(HDUL_CONFIG.DASHBOARD_SHEET);
  } else {
    // Hapus grafik lama & bersihkan isi
    const charts = dashSheet.getCharts();
    for (let c = 0; c < charts.length; c++) {
      dashSheet.removeChart(charts[c]);
    }
    dashSheet.clear();
  }
  
  dashSheet.setTabColor(HDUL_CONFIG.COLORS.SESUAI_TARGET);
  dashSheet.showSheet();
  dashSheet.setGridlines(true);
  
  // 3. Render Header Banner
  renderHeaderBanner_(dashSheet);
  
  // 4. Render KPI Metric Cards
  renderKpiCards_(dashSheet, totalAll);
  
  // 5. Render Helper Data untuk Grafik (Kolom R ke atas)
  const chartRanges = renderChartDataBlock_(dashSheet, dailyList, totalAll);
  
  // 6. Buat Embedded Native Charts
  renderCharts_(dashSheet, chartRanges, dailyList.length);
  
  // 7. Render Tabel Rekapitulasi Harian Lengkap
  renderDailyTable_(dashSheet, dailyList, totalAll);
  
  // 8. Auto-adjust Column Widths
  dashSheet.setColumnWidth(1, 120); // Tanggal
  dashSheet.setColumnWidth(2, 95);  // Total Pasien
  dashSheet.setColumnWidth(3, 90);  // Awal Tdk HDUL
  dashSheet.setColumnWidth(4, 85);  // % Tdk HDUL
  dashSheet.setColumnWidth(5, 90);  // Awal HDUL
  dashSheet.setColumnWidth(6, 85);  // % HDUL
  dashSheet.setColumnWidth(7, 100); // Sesuai Target
  dashSheet.setColumnWidth(8, 85);  // % Sesuai
  dashSheet.setColumnWidth(9, 105); // Melewati Target
  dashSheet.setColumnWidth(10, 85); // % Melewati
  dashSheet.setColumnWidth(11, 115); // Masih HDUL (<=2hr)
  dashSheet.setColumnWidth(12, 85);  // % Masih (<=2hr)
  dashSheet.setColumnWidth(13, 115); // Masih HDUL (>2hr)
  dashSheet.setColumnWidth(14, 85);  // % Masih (>2hr)
  dashSheet.setColumnWidth(15, 115); // Belum Ada Data
  dashSheet.setColumnWidth(16, 85);  // % Belum Ada
  
  // Sembunyikan kolom helper grafik agar tampilan bersih
  dashSheet.hideColumns(18, 12);
  
  ss.setActiveSheet(dashSheet);
  ss.toast("Dashboard HDUL berhasil diperbarui dengan data terkini!", "✅ Selesai", 5);
}

/**
 * 1. Banner Judul Dashboard
 */
function renderHeaderBanner_(sheet) {
  sheet.getRange("A1:P1").merge()
    .setValue("DASHBOARD MONITORING & EVALUASI SURAT KONTROL (HDUL)")
    .setBackground(HDUL_CONFIG.COLORS.HEADER_BG)
    .setFontColor("#FFFFFF")
    .setFontSize(14)
    .setFontWeight("bold")
    .setVerticalAlignment("middle");
  sheet.setRowHeight(1, 40);
  
  const nowStr = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "dd MMMM yyyy HH:mm:ss");
  sheet.getRange("A2:P2").merge()
    .setValue("Sumber Data: Tab '" + HDUL_CONFIG.SOURCE_SHEET + "' | Diperbarui: " + nowStr + " | Target Resolusi: <= 2 Hari Kalender sejak inserted_date")
    .setBackground("#1E293B")
    .setFontColor("#94A3B8")
    .setFontSize(9)
    .setFontStyle("italic")
    .setVerticalAlignment("middle");
  sheet.setRowHeight(2, 24);
}

/**
 * 2. Kartu Metrik Utama (KPI Cards)
 */
function renderKpiCards_(sheet, totalAll) {
  const cards = [
    {
      title: "TOTAL PASIEN",
      val: totalAll.total,
      sub: "100% Data Masuk",
      bg: "#F8FAFC",
      color: "#0F172A",
      border: "#CBD5E1",
      startCol: "A", endCol: "B"
    },
    {
      title: "AWAL TIDAK HDUL",
      val: totalAll.awalTidakHdul,
      sub: (totalAll.total > 0 ? (totalAll.awalTidakHdul / totalAll.total * 100).toFixed(1) : "0.0") + "% dari Total",
      bg: "#F0FDFA",
      color: HDUL_CONFIG.COLORS.TIDAK_HDUL,
      border: "#99F6E4",
      startCol: "C", endCol: "D"
    },
    {
      title: "AWAL HDUL",
      val: totalAll.awalHdul,
      sub: (totalAll.total > 0 ? (totalAll.awalHdul / totalAll.total * 100).toFixed(1) : "0.0") + "% dari Total",
      bg: "#EEF2FF",
      color: "#4F46E5",
      border: "#C7D2FE",
      startCol: "E", endCol: "F"
    },
    {
      title: "SESUAI TARGET (<=2hr)",
      val: totalAll.sesuaiTarget,
      sub: (totalAll.awalHdul > 0 ? (totalAll.sesuaiTarget / totalAll.awalHdul * 100).toFixed(1) : "0.0") + "% dari HDUL",
      bg: "#ECFDF5",
      color: HDUL_CONFIG.COLORS.SESUAI_TARGET,
      border: "#A7F3D0",
      startCol: "G", endCol: "H"
    },
    {
      title: "MELEWATI TARGET (>2hr)",
      val: totalAll.melewatiTarget,
      sub: (totalAll.awalHdul > 0 ? (totalAll.melewatiTarget / totalAll.awalHdul * 100).toFixed(1) : "0.0") + "% dari HDUL",
      bg: "#FFFBEB",
      color: HDUL_CONFIG.COLORS.MELEWATI_TARGET,
      border: "#FDE68A",
      startCol: "I", endCol: "J"
    },
    {
      title: "MASIH HDUL (>2hr)",
      val: totalAll.belumDiubahLewatTarget,
      sub: (totalAll.awalHdul > 0 ? (totalAll.belumDiubahLewatTarget / totalAll.awalHdul * 100).toFixed(1) : "0.0") + "% - PERLU TINDAKAN!",
      bg: "#FEF2F2",
      color: HDUL_CONFIG.COLORS.MASIH_LEWAT,
      border: "#FECACA",
      startCol: "K", endCol: "L"
    },
    {
      title: "MASIH HDUL (<=2hr)",
      val: totalAll.belumDiubahDalamTarget,
      sub: (totalAll.awalHdul > 0 ? (totalAll.belumDiubahDalamTarget / totalAll.awalHdul * 100).toFixed(1) : "0.0") + "% dalam target",
      bg: "#EFF6FF",
      color: HDUL_CONFIG.COLORS.MASIH_DALAM,
      border: "#BFDBFE",
      startCol: "M", endCol: "N"
    },
    {
      title: "BELUM ADA DATA / CEK",
      val: totalAll.tidakDiketahui,
      sub: (totalAll.awalHdul > 0 ? (totalAll.tidakDiketahui / totalAll.awalHdul * 100).toFixed(1) : "0.0") + "% belum dipasangkan",
      bg: "#F1F5F9",
      color: HDUL_CONFIG.COLORS.TIDAK_DIKETAHUI,
      border: "#E2E8F0",
      startCol: "O", endCol: "P"
    }
  ];
  
  sheet.setRowHeight(4, 20);
  sheet.setRowHeight(5, 32);
  sheet.setRowHeight(6, 20);
  
  for (let i = 0; i < cards.length; i++) {
    const c = cards[i];
    const rTitle = sheet.getRange(c.startCol + "4:" + c.endCol + "4").merge();
    const rVal = sheet.getRange(c.startCol + "5:" + c.endCol + "5").merge();
    const rSub = sheet.getRange(c.startCol + "6:" + c.endCol + "6").merge();
    const rBox = sheet.getRange(c.startCol + "4:" + c.endCol + "6");
    
    rTitle.setValue(c.title).setFontSize(8).setFontWeight("bold").setFontColor(c.color).setHorizontalAlignment("center");
    rVal.setValue(c.val).setFontSize(16).setFontWeight("bold").setFontColor(c.color).setHorizontalAlignment("center").setNumberFormat("#,##0");
    rSub.setValue(c.sub).setFontSize(8).setFontColor("#475569").setHorizontalAlignment("center");
    
    rBox.setBackground(c.bg);
    rBox.setBorder(true, true, true, true, false, false, c.border, SpreadsheetApp.BorderStyle.SOLID_MEDIUM);
  }
}

/**
 * 3. Render Helper Data Block untuk Grafik
 * Diletakkan di kolom R ke kanan (R..AC) agar grafik memiliki range referensi yang rapi dan konsisten
 */
function renderChartDataBlock_(sheet, dailyList, totalAll) {
  // Blok 1: Stacked Bar Chart Tren Harian (R24:W...)
  const barStartRow = 25;
  sheet.getRange("R24").setValue("Data Grafik Tren Harian Status HDUL");
  const barHeaders = [["Tanggal", "Sesuai Target", "Melewati Target", "Masih HDUL (<=2hr)", "Masih HDUL (>2hr)", "Belum Ada Data"]];
  sheet.getRange(barStartRow, 18, 1, 6).setValues(barHeaders);
  
  const barRows = [];
  for (let i = 0; i < dailyList.length; i++) {
    const d = dailyList[i];
    barRows.push([
      d.date,
      d.sesuaiTarget,
      d.melewatiTarget,
      d.belumDiubahDalamTarget,
      d.belumDiubahLewatTarget,
      d.tidakDiketahui
    ]);
  }
  sheet.getRange(barStartRow + 1, 18, barRows.length, 6).setValues(barRows);
  const barRange = sheet.getRange(barStartRow, 18, barRows.length + 1, 6);
  
  // Blok 2: Donut Chart Proporsi Pasien Awal HDUL (Y24:Z30)
  sheet.getRange("Y24").setValue("Data Donut Status HDUL");
  const donutHeaders = [["Kategori", "Jumlah"]];
  const donutRows = [
    ["Sesuai Target", totalAll.sesuaiTarget],
    ["Melewati Target", totalAll.melewatiTarget],
    ["Masih HDUL (<=2hr)", totalAll.belumDiubahDalamTarget],
    ["Masih HDUL (>2hr)", totalAll.belumDiubahLewatTarget],
    ["Belum Ada Data / Cek", totalAll.tidakDiketahui]
  ];
  sheet.getRange(barStartRow, 25, 1, 2).setValues(donutHeaders);
  sheet.getRange(barStartRow + 1, 25, donutRows.length, 2).setValues(donutRows);
  const donutHdulRange = sheet.getRange(barStartRow, 25, donutRows.length + 1, 2);
  
  // Blok 3: Donut Chart Kondisi Awal (AB24:AC27)
  sheet.getRange("AB24").setValue("Data Donut Kondisi Awal");
  const awalHeaders = [["Kondisi Awal", "Jumlah"]];
  const awalRows = [
    ["Tidak HDUL", totalAll.awalTidakHdul],
    ["HDUL", totalAll.awalHdul]
  ];
  sheet.getRange(barStartRow, 28, 1, 2).setValues(awalHeaders);
  sheet.getRange(barStartRow + 1, 28, awalRows.length, 2).setValues(awalRows);
  const donutAwalRange = sheet.getRange(barStartRow, 28, awalRows.length + 1, 2);
  
  return {
    barRange: barRange,
    donutHdulRange: donutHdulRange,
    donutAwalRange: donutAwalRange
  };
}

/**
 * 4. Buat Embedded Charts
 */
function renderCharts_(sheet, ranges, rowCount) {
  // Chart 1: Stacked Column Chart - Tren Harian Pasien Awal HDUL
  const colChart = sheet.newChart()
    .setChartType(Charts.ChartType.COLUMN)
    .addRange(ranges.barRange)
    .setPosition(8, 1, 0, 0)
    .setOption('title', 'Tren Penyelesaian Pasien Awal HDUL per Tanggal')
    .setOption('isStacked', true)
    .setOption('width', 660)
    .setOption('height', 310)
    .setOption('colors', [
      HDUL_CONFIG.COLORS.SESUAI_TARGET,
      HDUL_CONFIG.COLORS.MELEWATI_TARGET,
      HDUL_CONFIG.COLORS.MASIH_DALAM,
      HDUL_CONFIG.COLORS.MASIH_LEWAT,
      HDUL_CONFIG.COLORS.TIDAK_DIKETAHUI
    ])
    .setOption('legend', { position: 'top', textStyle: { fontSize: 10 } })
    .setOption('hAxis', { title: 'Tanggal Pembuatan (inserted_date)', textStyle: { fontSize: 10 } })
    .setOption('vAxis', { title: 'Jumlah Pasien' })
    .build();
  sheet.insertChart(colChart);
  
  // Chart 2: Donut Chart - Evaluasi Status Awal HDUL
  const donutHdul = sheet.newChart()
    .setChartType(Charts.ChartType.PIE)
    .addRange(ranges.donutHdulRange)
    .setPosition(8, 9, 0, 0)
    .setOption('title', 'Distribusi Status Pasien Awal HDUL')
    .setOption('pieHole', 0.45)
    .setOption('width', 360)
    .setOption('height', 310)
    .setOption('colors', [
      HDUL_CONFIG.COLORS.SESUAI_TARGET,
      HDUL_CONFIG.COLORS.MELEWATI_TARGET,
      HDUL_CONFIG.COLORS.MASIH_DALAM,
      HDUL_CONFIG.COLORS.MASIH_LEWAT,
      HDUL_CONFIG.COLORS.TIDAK_DIKETAHUI
    ])
    .setOption('legend', { position: 'right', textStyle: { fontSize: 10 } })
    .build();
  sheet.insertChart(donutHdul);
  
  // Chart 3: Donut Chart - Proporsi Kondisi Awal
  const donutAwal = sheet.newChart()
    .setChartType(Charts.ChartType.PIE)
    .addRange(ranges.donutAwalRange)
    .setPosition(8, 13, 0, 0)
    .setOption('title', 'Proporsi Kondisi Awal')
    .setOption('pieHole', 0.45)
    .setOption('width', 330)
    .setOption('height', 310)
    .setOption('colors', [HDUL_CONFIG.COLORS.TIDAK_HDUL, '#6366F1'])
    .setOption('legend', { position: 'right', textStyle: { fontSize: 10 } })
    .build();
  sheet.insertChart(donutAwal);
}

/**
 * 5. Render Tabel Rekapitulasi Harian Lengkap
 */
function renderDailyTable_(sheet, dailyList, totalAll) {
  const startRow = 24;
  
  // Section Header
  sheet.getRange(startRow, 1, 1, 16).merge()
    .setValue("📋 RINCIAN REKAPITULASI HARIAN (STATUS HDUL & PERSENTASE TARGET)")
    .setBackground("#1E293B")
    .setFontColor("#FFFFFF")
    .setFontWeight("bold")
    .setFontSize(11)
    .setVerticalAlignment("middle");
  sheet.setRowHeight(startRow, 28);
  
  // Two-Tier Table Headers
  const hRow1 = startRow + 1;
  const hRow2 = startRow + 2;
  
  sheet.getRange(hRow1, 1, 2, 1).merge().setValue("Tanggal Dibuat\n(inserted_date)").setHorizontalAlignment("center").setVerticalAlignment("middle");
  sheet.getRange(hRow1, 2, 2, 1).merge().setValue("Total\nPasien").setHorizontalAlignment("center").setVerticalAlignment("middle");
  
  sheet.getRange(hRow1, 3, 1, 2).merge().setValue("Awal Tidak HDUL").setHorizontalAlignment("center").setVerticalAlignment("middle");
  sheet.getRange(hRow2, 3).setValue("Jml").setHorizontalAlignment("center");
  sheet.getRange(hRow2, 4).setValue("%").setHorizontalAlignment("center");
  
  sheet.getRange(hRow1, 5, 1, 2).merge().setValue("Awal HDUL").setHorizontalAlignment("center").setVerticalAlignment("middle");
  sheet.getRange(hRow2, 5).setValue("Jml").setHorizontalAlignment("center");
  sheet.getRange(hRow2, 6).setValue("%").setHorizontalAlignment("center");
  
  sheet.getRange(hRow1, 7, 1, 10).merge().setValue("--- EVALUASI PASIEN AWAL HDUL (Basis: Jml Awal HDUL) ---").setHorizontalAlignment("center").setVerticalAlignment("middle");
  
  sheet.getRange(hRow2, 7).setValue("Sesuai (<=2hr)");
  sheet.getRange(hRow2, 8).setValue("% Sesuai");
  sheet.getRange(hRow2, 9).setValue("Lewat (>2hr)");
  sheet.getRange(hRow2, 10).setValue("% Lewat");
  sheet.getRange(hRow2, 11).setValue("Masih HDUL (<=2hr)");
  sheet.getRange(hRow2, 12).setValue("% Masih (<=)");
  sheet.getRange(hRow2, 13).setValue("Masih HDUL (>2hr)");
  sheet.getRange(hRow2, 14).setValue("% Masih (>)");
  sheet.getRange(hRow2, 15).setValue("Belum Ada / Cek");
  sheet.getRange(hRow2, 16).setValue("% Belum Ada");
  
  const headerRange = sheet.getRange(hRow1, 1, 2, 16);
  headerRange.setBackground("#334155")
    .setFontColor("#F8FAFC")
    .setFontWeight("bold")
    .setFontSize(9)
    .setWrap(true);
  sheet.setRowHeight(hRow1, 24);
  sheet.setRowHeight(hRow2, 24);
  
  // Data Rows
  const rowsData = [];
  for (let i = 0; i < dailyList.length; i++) {
    const d = dailyList[i];
    const pctTdkHdul = d.total > 0 ? (d.awalTidakHdul / d.total) : 0;
    const pctHdul = d.total > 0 ? (d.awalHdul / d.total) : 0;
    
    const pctSesuai = d.awalHdul > 0 ? (d.sesuaiTarget / d.awalHdul) : 0;
    const pctMelewati = d.awalHdul > 0 ? (d.melewatiTarget / d.awalHdul) : 0;
    const pctMasihDalam = d.awalHdul > 0 ? (d.belumDiubahDalamTarget / d.awalHdul) : 0;
    const pctMasihLewat = d.awalHdul > 0 ? (d.belumDiubahLewatTarget / d.awalHdul) : 0;
    const pctTidakDiketahui = d.awalHdul > 0 ? (d.tidakDiketahui / d.awalHdul) : 0;
    
    rowsData.push([
      d.date,
      d.total,
      d.awalTidakHdul,
      pctTdkHdul,
      d.awalHdul,
      pctHdul,
      d.sesuaiTarget,
      pctSesuai,
      d.melewatiTarget,
      pctMelewati,
      d.belumDiubahDalamTarget,
      pctMasihDalam,
      d.belumDiubahLewatTarget,
      pctMasihLewat,
      d.tidakDiketahui,
      pctTidakDiketahui
    ]);
  }
  
  const dataStartRow = startRow + 3;
  const numRows = rowsData.length;
  const tableDataRange = sheet.getRange(dataStartRow, 1, numRows, 16);
  tableDataRange.setValues(rowsData)
    .setFontSize(9)
    .setVerticalAlignment("middle");
  
  for (let r = 0; r < numRows; r++) {
    sheet.setRowHeight(dataStartRow + r, 22);
    // Alternating zebra striping
    if (r % 2 === 1) {
      sheet.getRange(dataStartRow + r, 1, 1, 16).setBackground("#F8FAFC");
    }
  }
  
  // Number Formatting: Numbers & Percentages
  sheet.getRange(dataStartRow, 1, numRows, 1).setHorizontalAlignment("center");
  sheet.getRange(dataStartRow, 2, numRows, 1).setNumberFormat("#,##0").setHorizontalAlignment("right");
  sheet.getRange(dataStartRow, 3, numRows, 1).setNumberFormat("#,##0").setHorizontalAlignment("right");
  sheet.getRange(dataStartRow, 4, numRows, 1).setNumberFormat("0.0%").setHorizontalAlignment("right");
  sheet.getRange(dataStartRow, 5, numRows, 1).setNumberFormat("#,##0").setHorizontalAlignment("right");
  sheet.getRange(dataStartRow, 6, numRows, 1).setNumberFormat("0.0%").setHorizontalAlignment("right");
  sheet.getRange(dataStartRow, 7, numRows, 1).setNumberFormat("#,##0").setHorizontalAlignment("right");
  sheet.getRange(dataStartRow, 8, numRows, 1).setNumberFormat("0.0%").setHorizontalAlignment("right");
  sheet.getRange(dataStartRow, 9, numRows, 1).setNumberFormat("#,##0").setHorizontalAlignment("right");
  sheet.getRange(dataStartRow, 10, numRows, 1).setNumberFormat("0.0%").setHorizontalAlignment("right");
  sheet.getRange(dataStartRow, 11, numRows, 1).setNumberFormat("#,##0").setHorizontalAlignment("right");
  sheet.getRange(dataStartRow, 12, numRows, 1).setNumberFormat("0.0%").setHorizontalAlignment("right");
  sheet.getRange(dataStartRow, 13, numRows, 1).setNumberFormat("#,##0").setHorizontalAlignment("right");
  sheet.getRange(dataStartRow, 14, numRows, 1).setNumberFormat("0.0%").setHorizontalAlignment("right");
  sheet.getRange(dataStartRow, 15, numRows, 1).setNumberFormat("#,##0").setHorizontalAlignment("right");
  sheet.getRange(dataStartRow, 16, numRows, 1).setNumberFormat("0.0%").setHorizontalAlignment("right");
  
  // Total Keseluruhan Row
  const totalRowIndex = dataStartRow + numRows;
  const totPctTdkHdul = totalAll.total > 0 ? (totalAll.awalTidakHdul / totalAll.total) : 0;
  const totPctHdul = totalAll.total > 0 ? (totalAll.awalHdul / totalAll.total) : 0;
  const totPctSesuai = totalAll.awalHdul > 0 ? (totalAll.sesuaiTarget / totalAll.awalHdul) : 0;
  const totPctMelewati = totalAll.awalHdul > 0 ? (totalAll.melewatiTarget / totalAll.awalHdul) : 0;
  const totPctMasihDalam = totalAll.awalHdul > 0 ? (totalAll.belumDiubahDalamTarget / totalAll.awalHdul) : 0;
  const totPctMasihLewat = totalAll.awalHdul > 0 ? (totalAll.belumDiubahLewatTarget / totalAll.awalHdul) : 0;
  const totPctTidakDiketahui = totalAll.awalHdul > 0 ? (totalAll.tidakDiketahui / totalAll.awalHdul) : 0;
  
  const totalRowData = [
    "TOTAL",
    totalAll.total,
    totalAll.awalTidakHdul,
    totPctTdkHdul,
    totalAll.awalHdul,
    totPctHdul,
    totalAll.sesuaiTarget,
    totPctSesuai,
    totalAll.melewatiTarget,
    totPctMelewati,
    totalAll.belumDiubahDalamTarget,
    totPctMasihDalam,
    totalAll.belumDiubahLewatTarget,
    totPctMasihLewat,
    totalAll.tidakDiketahui,
    totPctTidakDiketahui
  ];
  
  const totalRange = sheet.getRange(totalRowIndex, 1, 1, 16);
  totalRange.setValues([totalRowData])
    .setBackground("#E2E8F0")
    .setFontWeight("bold")
    .setFontSize(9)
    .setVerticalAlignment("middle");
  sheet.setRowHeight(totalRowIndex, 26);
  
  totalRange.getCell(1, 1).setHorizontalAlignment("center");
  for (let c = 2; c <= 16; c++) {
    if ([4, 6, 8, 10, 12, 14, 16].indexOf(c) !== -1) {
      totalRange.getCell(1, c).setNumberFormat("0.0%").setHorizontalAlignment("right");
    } else {
      totalRange.getCell(1, c).setNumberFormat("#,##0").setHorizontalAlignment("right");
    }
  }
  
  // Borders
  const fullTableRange = sheet.getRange(hRow1, 1, numRows + 3, 16);
  fullTableRange.setBorder(true, true, true, true, true, true, "#CBD5E1", SpreadsheetApp.BorderStyle.SOLID);
  
  // Highlight Column 13 (Masih HDUL >2hr) with soft red if > 0
  for (let r = 0; r < numRows; r++) {
    const val = rowsData[r][12];
    if (val > 0) {
      sheet.getRange(dataStartRow + r, 13).setBackground("#FEE2E2").setFontColor("#991B1B").setFontWeight("bold");
    }
  }
}

/**
 * Parsing & Aggregasi Data dari Sheet "Data"
 */
function processData_() {
  const ss = getSpreadsheet_();
  const sheet = ss.getSheetByName(HDUL_CONFIG.SOURCE_SHEET);
  if (!sheet) {
    throw new Error("Tab '" + HDUL_CONFIG.SOURCE_SHEET + "' tidak ditemukan. Pastikan nama tab tempat data disimpan sesuai.");
  }
  
  const values = sheet.getDataRange().getValues();
  if (values.length < 2) {
    throw new Error("Tab '" + HDUL_CONFIG.SOURCE_SHEET + "' tidak memiliki baris data.");
  }
  
  const headers = values[0];
  const colMap = {};
  for (let i = 0; i < headers.length; i++) {
    colMap[String(headers[i]).trim().toLowerCase()] = i;
  }
  
  const colInserted = colMap["inserted_date"];
  const colKategori = colMap["kategori"];
  const colKategoriAwal = colMap["kategori_awal"];
  const colSurat = colMap["no_surat_kontrol"];
  const colId = colMap["id_rencana_kontrol"];
  
  if (colInserted === undefined || colKategori === undefined) {
    throw new Error("Kolom 'inserted_date' atau 'kategori' tidak ditemukan pada baris 1 tab '" + HDUL_CONFIG.SOURCE_SHEET + "'.");
  }
  
  const daily = {};
  const totalAll = {
    total: 0,
    awalTidakHdul: 0,
    awalHdul: 0,
    sesuaiTarget: 0,
    melewatiTarget: 0,
    belumDiubahDalamTarget: 0,
    belumDiubahLewatTarget: 0,
    tidakDiketahui: 0
  };
  
  const rows = values.slice(1);
  for (let i = 0; i < rows.length; i++) {
    const r = rows[i];
    const rawDate = r[colInserted];
    const dateKey = extractDateOnly_(rawDate);
    
    // Abaikan baris kosong
    if (dateKey === "Tidak Ada Tanggal" && (!r[colId] || String(r[colId]).trim() === "")) {
      continue;
    }
    
    if (!daily[dateKey]) {
      daily[dateKey] = {
        date: dateKey,
        total: 0,
        awalTidakHdul: 0,
        awalHdul: 0,
        sesuaiTarget: 0,
        melewatiTarget: 0,
        belumDiubahDalamTarget: 0,
        belumDiubahLewatTarget: 0,
        tidakDiketahui: 0
      };
    }
    
    const katVal = colKategori !== undefined ? String(r[colKategori] || "").trim() : "";
    const katAwalVal = colKategoriAwal !== undefined ? String(r[colKategoriAwal] || "").trim() : "";
    const suratVal = colSurat !== undefined ? String(r[colSurat] || "").trim() : "";
    
    // Tentukan apakah kondisi awal HDUL
    const isAwalHdul = (katAwalVal === "HDUL") || (suratVal.toLowerCase().indexOf("hdul") !== -1);
    
    daily[dateKey].total++;
    totalAll.total++;
    
    if (!isAwalHdul || katVal === "Tidak HDUL") {
      daily[dateKey].awalTidakHdul++;
      totalAll.awalTidakHdul++;
    } else {
      daily[dateKey].awalHdul++;
      totalAll.awalHdul++;
      
      if (katVal === "Sesuai target") {
        daily[dateKey].sesuaiTarget++;
        totalAll.sesuaiTarget++;
      } else if (katVal === "Melewati target") {
        daily[dateKey].melewatiTarget++;
        totalAll.melewatiTarget++;
      } else if (katVal === "Belum diubah, masih dalam target") {
        daily[dateKey].belumDiubahDalamTarget++;
        totalAll.belumDiubahDalamTarget++;
      } else if (katVal === "Belum diubah, melewati target") {
        daily[dateKey].belumDiubahLewatTarget++;
        totalAll.belumDiubahLewatTarget++;
      } else {
        // "Belum ada data terbaru", "Belum ada pembanding", "Perlu diperiksa...", dll.
        daily[dateKey].tidakDiketahui++;
        totalAll.tidakDiketahui++;
      }
    }
  }
  
  const sortedDates = Object.keys(daily).sort();
  const dailyList = [];
  for (let j = 0; j < sortedDates.length; j++) {
    dailyList.push(daily[sortedDates[j]]);
  }
  
  return {
    dailyList: dailyList,
    totalAll: totalAll
  };
}

/**
 * Ekstraksi Tanggal YYYY-MM-DD dari berbagai format input
 */
function extractDateOnly_(val) {
  if (!val) return "Tidak Ada Tanggal";
  if (val instanceof Date) {
    const y = val.getFullYear();
    const m = ("0" + (val.getMonth() + 1)).slice(-2);
    const d = ("0" + val.getDate()).slice(-2);
    return y + "-" + m + "-" + d;
  }
  const s = String(val).trim();
  if (!s || s === "-") return "Tidak Ada Tanggal";
  
  // Format ISO YYYY-MM-DD
  const isoMatch = s.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})/);
  if (isoMatch) {
    return isoMatch[1] + "-" + ("0" + isoMatch[2]).slice(-2) + "-" + ("0" + isoMatch[3]).slice(-2);
  }
  
  // Format DD/MM/YYYY
  const dmyMatch = s.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})/);
  if (dmyMatch) {
    return dmyMatch[3] + "-" + ("0" + dmyMatch[2]).slice(-2) + "-" + ("0" + dmyMatch[1]).slice(-2);
  }
  
  return s.split(" ")[0];
}

/**
 * Membuka Popup Dialog Visualisasi Interaktif
 */
function openInteractiveDashboard() {
  const html = HtmlService.createHtmlOutputFromFile('DashboardUI')
    .setWidth(1150)
    .setHeight(720);
  SpreadsheetApp.getUi().showModalDialog(html, '📊 Visualisasi Interaktif Monitoring HDUL');
}

/**
 * API untuk Frontend Popup: Mengambil data JSON teragregasi
 */
function getDashboardDataJson() {
  return processData_();
}

/**
 * Menampilkan Dialog Informasi & Panduan Indikator
 */
function showHelpDialog() {
  const msg = 
    "PENJELASAN INDIKATOR STATUS HDUL:\n\n" +
    "1. Tidak HDUL: Nomor surat awal sudah valid dan tidak mengandung HDUL.\n\n" +
    "2. Sesuai target (<= 2 hari): Awalnya HDUL, kemudian berhasil diterbitkan nomor surat dalam waktu <= 2 hari kalender sejak inserted_date.\n\n" +
    "3. Melewati target (> 2 hari): Awalnya HDUL, diterbitkan nomor surat setelah lebih dari 2 hari kalender.\n\n" +
    "4. Belum diubah, masih dalam target: Data terbaru masih HDUL dan jarak hari sampai pengambilan data masih <= 2 hari kalender.\n\n" +
    "5. Belum diubah, melewati target: Data terbaru masih HDUL dan jarak hari sudah > 2 hari kalender (PERLU DITINDAKLANJUTI SEGERA).\n\n" +
    "6. Belum ada data terbaru / Perlu diperiksa: Pasien belum ditemukan pada file pembanding atau statusnya memerlukan pengecekan sistem asal.";
    
  SpreadsheetApp.getUi().alert("ℹ️ Panduan Indikator Status Surat Kontrol", msg, SpreadsheetApp.getUi().ButtonSet.OK);
}
