"""
Lila XLS / XLSX import sayfası.
XLS parse: eski projeden alınan regex yöntemi — ad/soyad dahil tüm sütunlar okunur.
XLSX parse: zipfile + XML yöntemi.
Sadece BİREYSEL+GRUP öğrenciler aktarılır.
"""
import re
import io
import zipfile
import xml.etree.ElementTree as ET
import unicodedata
import streamlit as st
from datetime import date, timedelta, datetime
import api_client as api

# ── Tanı → Grup Modül Haritası ────────────────────────────────────────────────
TANI_MODUL_MAP = {
    "Bedensel Yetersizliği Olan Bireyler İçin Destek Eğitim Programı": [
        "Günlük Yaşam Aktiviteleri",
    ],
    "Dil ve Konuşma Bozukluğu Olan Bireyler İçin Destek Eğitim Programı": [
        "Dil",
        "Dil ve İletişim",
    ],
    "Görme Yetersizliği Olan Bireyler İçin Destek Eğitim Programı": [
        "Dil ve İletişim",
        "Erken Matematik",
        "Günlük Yaşam Becerileri",
        "Matematik",
        "Okuma ve Yazma",
        "Sosyal Beceriler",
        "Toplumsal Yaşam Becerileri",
    ],
    "İşitme Yetersizliği Olan Bireyler İçin Destek Eğitim Programı": [
        "Erken Matematik",
        "Matematik",
        "Okuma ve Yazma",
        "Sosyal İletişim",
    ],
    "Otizm Spektrum Bozukluğu Olan Bireyler İçin Destek Eğitim Programı": [
        "Birey ve Çevre",
        "Dil, İletişim ve Oyun",
        "Erken Matematik",
        "Günlük Yaşam Becerileri",
        "Matematik",
        "Okuma ve Yazma",
        "Sosyal Beceriler",
        "Toplumsal Yaşam Becerileri",
    ],
    "Öğrenme Güçlüğü Olan Bireyler İçin Destek Eğitim Programı": [
        "Dil ve İletişim",
        "Erken Matematik",
        "Matematik",
        "Okuma ve Yazma",
        "Sosyal Etkileşim",
    ],
    "Zihinsel Yetersizliği Olan Bireyler İçin Destek Eğitim Programı": [
        "Birey ve Çevre",
        "Dil, İletişim ve Oyun",
        "Erken Matematik",
        "Günlük Yaşam Becerileri",
        "Matematik",
        "Okuma ve Yazma",
        "Sosyal Beceriler",
        "Toplumsal Yaşam Becerileri",
    ],
}


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    return " ".join(s.split()).strip()


def modul_from_tani(taniler: list) -> list:
    """Tanı listesine göre grup modüllerini döndür."""
    moduller = set()
    for tani in taniler:
        tani_norm = normalize(tani)
        for key, mods in TANI_MODUL_MAP.items():
            if normalize(key) in tani_norm or tani_norm in normalize(key):
                moduller.update(mods)
    return sorted(moduller)


def excel_serial_to_date(serial: str):
    try:
        n = int(float(serial))
        if n <= 0:
            return None
        return (date(1899, 12, 30) + timedelta(days=n)).isoformat()
    except Exception:
        return None


# ── XLS (HTML tabanlı) Parser — eski projeden alındı ─────────────────────────
def parse_xls(file_bytes: bytes) -> list:
    content = file_bytes.decode("utf-8", errors="ignore")
    rows = re.findall(r'<tr[^>]*>(.*?)</tr>', content, re.DOTALL | re.IGNORECASE)

    parsed = []
    for row in rows:
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL | re.IGNORECASE)
        cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
        parsed.append(cells)

    if len(parsed) < 3:
        return []

    headers = parsed[2]
    data_rows = parsed[3:]

    def col(name):
        try:
            return headers.index(name)
        except ValueError:
            return None

    idx_adi         = col("ADI")
    idx_soyadi      = col("SOYADI")
    idx_dob         = col("DOĞUM TARİHİ")
    idx_program     = col("EĞİTİM PROGRAMI")
    idx_rapor_bitis = col("BİTİŞ TARİHİ")
    idx_sekil       = col("EĞİTSEL TANI VE EĞİTİM ÖNERİSİ")

    students = []
    seen = set()

    for row in data_rows:
        if not row:
            continue

        # BİREYSEL+GRUP kontrolü
        sekil = row[idx_sekil].strip().upper() if idx_sekil is not None and len(row) > idx_sekil else ""
        if "GRUP" not in sekil:
            continue

        ad    = row[idx_adi].strip()    if idx_adi    is not None and len(row) > idx_adi    else ""
        soyad = row[idx_soyadi].strip() if idx_soyadi is not None and len(row) > idx_soyadi else ""
        tam_ad = f"{ad} {soyad}".strip()
        if not tam_ad or tam_ad in seen:
            continue
        seen.add(tam_ad)

        # Doğum tarihi
        dob = None
        if idx_dob is not None and len(row) > idx_dob:
            try:
                dob = datetime.strptime(row[idx_dob].strip(), "%d.%m.%Y").date().isoformat()
            except Exception:
                pass

        # Rapor bitiş
        rapor_bitis = None
        if idx_rapor_bitis is not None and len(row) > idx_rapor_bitis:
            try:
                rapor_bitis = datetime.strptime(row[idx_rapor_bitis].strip(), "%d.%m.%Y").date().isoformat()
            except Exception:
                pass

        # Tanılar
        prog_str = row[idx_program].strip() if idx_program is not None and len(row) > idx_program else ""
        taniler = list(dict.fromkeys(t.strip() for t in prog_str.split(",") if t.strip()))

        students.append({
            "name": tam_ad,
            "dob": dob,
            "rapor_bitis": rapor_bitis,
            "taniler": taniler,
            "moduller": modul_from_tani(taniler),
        })

    return students


# ── XLSX Parser ───────────────────────────────────────────────────────────────
def parse_xlsx(file_bytes: bytes) -> list:
    ns = {"ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

    with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
        with z.open("xl/sharedStrings.xml") as f:
            ss_tree = ET.parse(f)
        shared = []
        for si in ss_tree.findall(".//ns:si", ns):
            text = "".join(t.text or "" for t in si.findall(".//ns:t", ns))
            shared.append(text)

        with z.open("xl/worksheets/sheet1.xml") as f:
            sheet_tree = ET.parse(f)

    def cell_val(cell):
        t = cell.get("t", "")
        v_el = cell.find("ns:v", ns)
        if v_el is None:
            return ""
        val = v_el.text or ""
        if t == "s":
            return shared[int(val)]
        return val

    rows = []
    for row_el in sheet_tree.findall(".//ns:row", ns):
        row = {}
        for cell in row_el.findall("ns:c", ns):
            ref = cell.get("r", "")
            col = "".join(c for c in ref if c.isalpha())
            row[col] = cell_val(cell)
        rows.append(row)

    seen = set()
    students = []

    for row in rows[3:]:
        # BN = EĞİTSEL TANI VE EĞİTİM ÖNERİSİ
        sekil = row.get("BN", "").strip().upper()
        if "GRUP" not in sekil:
            continue

        ad    = row.get("D", "").strip()
        soyad = row.get("E", "").strip()
        tam_ad = f"{ad} {soyad}".strip()
        if not tam_ad or tam_ad in seen:
            continue
        seen.add(tam_ad)

        dob   = excel_serial_to_date(row.get("J", ""))
        rapor = excel_serial_to_date(row.get("BK", ""))

        tani_raw = row.get("BO", "")
        taniler = list(dict.fromkeys(t.strip() for t in tani_raw.split(",") if t.strip()))

        students.append({
            "name": tam_ad,
            "dob": dob,
            "rapor_bitis": rapor,
            "taniler": taniler,
            "moduller": modul_from_tani(taniler),
        })

    return students


# ── Sayfa ─────────────────────────────────────────────────────────────────────
def show():
    st.header("📥 Lila'dan Öğrenci İçe Aktar")

    st.info(
        "Lila'dan indirdiğiniz öğrenci listesini yükleyin. "
        "**XLS** veya **XLSX** formatı desteklenir. "
        "Yalnızca **BİREYSEL+GRUP** öğrenciler aktarılır."
    )

    uploaded = st.file_uploader("Lila dosyasını seç", type=["xls", "xlsx"])
    if not uploaded:
        return

    with st.spinner("Dosya okunuyor..."):
        try:
            file_bytes = uploaded.read()
            if uploaded.name.endswith(".xlsx"):
                students = parse_xlsx(file_bytes)
                st.caption("📋 XLSX formatı — ad/soyad ve doğum tarihi okundu")
            else:
                students = parse_xls(file_bytes)
                st.caption("📋 XLS formatı — ad/soyad ve doğum tarihi okundu")
        except Exception as e:
            st.error(f"Dosya okunamadı: {e}")
            return

    if not students:
        st.warning("Dosyada BİREYSEL+GRUP öğrenci bulunamadı.")
        return

    st.success(f"**{len(students)}** öğrenci bulundu.")

    import pandas as pd
    preview = pd.DataFrame([
        {
            "Ad Soyad": s["name"],
            "Doğum": s["dob"] or "–",
            "Rapor Bitiş": s["rapor_bitis"] or "–",
            "Tanılar": ", ".join(s["taniler"]),
            "Grup Modülleri": ", ".join(s["moduller"]),
        }
        for s in students
    ])
    st.dataframe(preview, use_container_width=True)

    st.divider()

    mevcut_taniler    = {d["name"]: d["id"] for d in api.get_diagnoses()}
    mevcut_moduller   = {m["name"]: m["id"] for m in api.get_modules()}
    mevcut_ogrenciler = {s["name"] for s in api.get_students()}

    tum_taniler  = set(t for s in students for t in s["taniler"])
    tum_moduller = set(m for s in students for m in s["moduller"])
    eksik_taniler  = tum_taniler  - set(mevcut_taniler.keys())
    eksik_moduller = tum_moduller - set(mevcut_moduller.keys())

    if eksik_taniler or eksik_moduller:
        with st.expander("⚠️ Import sırasında otomatik eklenecek yeni tanı/modüller"):
            if eksik_taniler:
                st.write("**Yeni tanılar:**", ", ".join(sorted(eksik_taniler)))
            if eksik_moduller:
                st.write("**Yeni modüller:**", ", ".join(sorted(eksik_moduller)))

    zaten_kayitli = [s for s in students if s["name"] in mevcut_ogrenciler]
    if zaten_kayitli:
        st.warning(f"{len(zaten_kayitli)} öğrenci zaten sistemde, rapor tarihleri güncellenecek.")

    if st.button("🚀 İçe Aktar", type="primary"):
        # 1. Eksik tanıları ekle
        for adi in eksik_taniler:
            r = api.create_diagnosis(adi)
            if r:
                mevcut_taniler[adi] = r["id"]

        # 2. Eksik modülleri ekle
        for adi in eksik_moduller:
            r = api.create_module(adi)
            if r:
                mevcut_moduller[adi] = r["id"]

        # 3. Öğrencileri ekle veya güncelle
        eklendi = guncellendi = hatali = 0
        progress = st.progress(0)

        for i, s in enumerate(students):
            diag_ids = [mevcut_taniler[t] for t in s["taniler"] if t in mevcut_taniler]
            mod_ids  = [mevcut_moduller[m] for m in s["moduller"] if m in mevcut_moduller]

            if s["name"] in mevcut_ogrenciler:
                # Mevcut öğrenciyi bul ve rapor tarihini güncelle
                tum = api.get_students()
                mevcut = next((x for x in tum if x["name"] == s["name"]), None)
                if mevcut:
                    payload = {
                        "rapor_bitis": s["rapor_bitis"],
                        "diagnosis_ids": diag_ids,
                        "module_ids": mod_ids,
                    }
                    api.update_student(mevcut["id"], payload)
                    guncellendi += 1
            else:
                payload = {
                    "name": s["name"],
                    "dob": s["dob"],
                    "rapor_bitis": s["rapor_bitis"],
                    "diagnosis_ids": diag_ids,
                    "module_ids": mod_ids,
                }
                result = api.create_student(payload)
                if result:
                    eklendi += 1
                else:
                    hatali += 1

            progress.progress((i + 1) / len(students))

        progress.empty()
        st.success(
            f"✅ **{eklendi}** yeni eklendi &nbsp;|&nbsp; "
            f"🔄 {guncellendi} güncellendi &nbsp;|&nbsp; "
            f"❌ {hatali} hata"
        )
        st.rerun()
