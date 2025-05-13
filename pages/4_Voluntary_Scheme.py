import streamlit as st
import sqlite3
import pandas as pd
import os
import re
import time
from utils.auth import login_required
#login_required()


def slugify(value):
    return re.sub(r'[^\w\-_]', '_', str(value))

st.set_page_config(page_title="📄 Voluntary Rapor İnceleme", layout="wide")
st.title("📄 Voluntary Rapor Detaylı İnceleme")

# Veritabanı bağlantısı
conn = sqlite3.connect("sms_database2.db", check_same_thread=False)
cursor = conn.cursor()


# Risk tablosu
cursor.execute("""
CREATE TABLE IF NOT EXISTS voluntary_risk (
    report_number TEXT PRIMARY KEY,
    tehlike_tanimi TEXT,
    potansiyel_sonuclar TEXT,
    severity TEXT,
    likelihood TEXT,
    mevcut_onlemler TEXT,
    risk_seviyesi TEXT
)
""")

# Önlem tablosu
cursor.execute("""
CREATE TABLE IF NOT EXISTS voluntary_onlem (
    report_number TEXT PRIMARY KEY,
    onlem_aciklamasi TEXT,
    sorumlu_kisi TEXT,
    termin_tarihi TEXT,
    gerceklesme_tarihi TEXT,
    etkinlik_kontrolu TEXT,
    revize_risk TEXT
)
""")

# Geri bildirim tablosu
cursor.execute("""
CREATE TABLE IF NOT EXISTS voluntary_geri_bildirim (
    report_number TEXT PRIMARY KEY,
    gonderen TEXT,
    icerik TEXT,
    tarih TEXT
)
""")

# Kapanış tablosu
cursor.execute("""
CREATE TABLE IF NOT EXISTS voluntary_kapanis (
    report_number TEXT PRIMARY KEY,
    durum TEXT,
    degerlendirme_tarihi TEXT,
    kapanis_tarihi TEXT
)
""")

conn.commit()


cursor.execute("""
CREATE TABLE IF NOT EXISTS voluntary_progress (
    report_number TEXT PRIMARY KEY,
    tamamlanan INTEGER,
    toplam INTEGER,
    yuzde INTEGER,
    eksikler TEXT
)
""")
conn.commit()

def guncelle_tamamlanma_durumu(report_number):
    # Verileri veritabanından çek
    kayit_deger = cursor.execute("SELECT * FROM voluntary_degerlendirme WHERE report_number = ?", (report_number,)).fetchone()
    kayit_risk = cursor.execute("SELECT * FROM voluntary_risk WHERE report_number = ?", (report_number,)).fetchone()
    kayit_onlem = cursor.execute("SELECT * FROM voluntary_onlem WHERE report_number = ?", (report_number,)).fetchone()
    kayit_geri = cursor.execute("SELECT * FROM voluntary_geri_bildirim WHERE report_number = ?", (report_number,)).fetchone()
    kayit_kapanis = cursor.execute("SELECT * FROM voluntary_kapanis WHERE report_number = ?", (report_number,)).fetchone()

    # Kontroller
    bolumler = {
        "Değerlendirme Paneli": bool(kayit_deger),
        "Risk Değerlendirme": bool(kayit_risk),
        "Önlemler ve Takip": bool(kayit_onlem),
        "Geri Bildirim": bool(kayit_geri),
        "Durum ve Kapanış": bool(kayit_kapanis)
    }

    tamamlanan = sum(1 for val in bolumler.values() if val)
    toplam = len(bolumler)
    yuzde = int((tamamlanan / toplam) * 100)
    eksikler = ", ".join([k for k, v in bolumler.items() if not v])

    # Veritabanına yaz
    cursor.execute("""
        INSERT INTO voluntary_progress (report_number, tamamlanan, toplam, yuzde, eksikler)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(report_number) DO UPDATE SET
            tamamlanan=excluded.tamamlanan,
            toplam=excluded.toplam,
            yuzde=excluded.yuzde,
            eksikler=excluded.eksikler
    """, (report_number, tamamlanan, toplam, yuzde, eksikler))
    conn.commit()

def bolum_tamamlanma_goster(bolum_adi, report_number):
    tamamlanma = cursor.execute("SELECT * FROM voluntary_progress WHERE report_number = ?", (report_number,)).fetchone()
    if not tamamlanma:
        st.info("Henüz bu rapor için tamamlanma durumu hesaplanmadı.")
        return
    
    yuzde = tamamlanma[3]
    eksik = tamamlanma[4].split(", ") if tamamlanma[4] else []

    st.markdown("----")
    if bolum_adi in eksik:
        st.error(f"❌ Bu bölüm henüz tamamlanmamış: **{bolum_adi}**")
    else:
        st.success(f"✅ Bu bölüm tamamlanmış: **{bolum_adi}**")

    st.progress(yuzde / 100)
    st.caption(f"Genel ilerleme: **%{yuzde}**")

def raporu_sil(report_number):
    tablolar = [
        "voluntary_reports",
        "voluntary_degerlendirme",
        "voluntary_risk",
        "voluntary_onlem",
        "voluntary_geri_bildirim",
        "voluntary_kapanis",
        "voluntary_progress"
    ]
    for tablo in tablolar:
        cursor.execute(f"DELETE FROM {tablo} WHERE report_number = ?", (report_number,))
    conn.commit()
# Ek dosya klasörü
UPLOAD_KLASORU = "uploads/voluntary_ekler"
os.makedirs(UPLOAD_KLASORU, exist_ok=True)

# Değerlendirme için tablo oluştur
cursor.execute("""
CREATE TABLE IF NOT EXISTS voluntary_degerlendirme (
    report_number TEXT PRIMARY KEY,
    degerlendirme_durumu TEXT,
    sonuc_durumu TEXT,
    geri_bildirim TEXT,
    atanan_kisi TEXT,
    atama_tarihi TEXT
)
""")
conn.commit()

# Verileri oku
df = pd.read_sql("SELECT * FROM voluntary_reports ORDER BY olay_tarihi DESC", conn)

# Rapor filtreleme
st.sidebar.header("🔍 Filtreleme")
secili_rapor_no = st.sidebar.selectbox("Rapor Numarası Seçin", df["report_number"].unique())

# Sekmeler
sekme1, sekme2, sekme3, sekme4, sekme5, gelismis_tab = st.tabs([
    "📄 Rapor", "🛠️ Değerlendirme", "⚠️ Risk", "✅ Önlem", "📤 Geri Bildirim", "⚙️ Gelişmiş"
])

with gelismis_tab:
    sekme6, sekme7, sekme8, sekme9 = st.tabs([
        "📈 Durum ve Kapanış", "📋 Genel Özet", "📋 Tüm Raporlar","📄 Rapor Özeti (Tam Görünüm)"
    ])


with sekme1:
    # Seçilen raporu getir
    secili_rapor = df[df["report_number"] == secili_rapor_no].iloc[0]

    st.markdown(f"### 🧾 Rapor Numarası: `{secili_rapor['report_number']}`")
    st.markdown(f"**Rapor Türü:** {secili_rapor['rapor_turu']}")
    st.markdown(f"**Rapor Konusu:** {secili_rapor['rapor_konusu']}")
    st.markdown(f"**Olay Tarihi:** {secili_rapor['olay_tarihi']}")
    st.markdown(f"**Veri Giriş Tarihi:** {secili_rapor['veri_giris_tarihi']}")

    # Ozel cevaplar
    ozel_cevaplar = secili_rapor.get("ozel_cevaplar")
    if ozel_cevaplar:
        try:
            cevap_dict = eval(ozel_cevaplar) if isinstance(ozel_cevaplar, str) else ozel_cevaplar
            st.markdown("---")
            st.subheader("📝 Form Cevapları")
            for soru, cevap in cevap_dict.items():
                st.markdown(f"**{soru}**: {cevap if cevap else '-'}")
        except Exception as e:
            st.error("❌ Cevaplar ayrıştırılamadı.")
            st.text(ozel_cevaplar)
    else:
        st.info("ℹ️ Bu rapora özel form cevabı girilmemiş.")

    # Ek dosya yükleme bölümü
    st.markdown("---")
    st.subheader("📎 Ek Dosya Yükle")
    ek_dosya = st.file_uploader("Bir ek dosya yükleyin (PDF, Görsel, Belge vb.)", type=None, key="upload")

    # Bu rapora ait özel klasöre kayıt (güvenli klasör ismi)
    klasor_adi = slugify(secili_rapor_no)
    ek_kayit_klasoru = os.path.join(UPLOAD_KLASORU, klasor_adi)
    os.makedirs(ek_kayit_klasoru, exist_ok=True)

    if ek_dosya:
        dosya_yolu = os.path.join(ek_kayit_klasoru, ek_dosya.name)
        with open(dosya_yolu, "wb") as f:
            f.write(ek_dosya.read())
        st.success(f"✅ Dosya yüklendi: {ek_dosya.name}")
        time.sleep(1)
        st.warning("Sayfa yeniden yüklenmesi için F5'e basın.")

    # Yüklenen dosyaları sadece bu rapora göster ve silme opsiyonu ekle
    st.markdown("### 📂 Bu Rapora Ait Ekler")
    ekli_dosyalar = os.listdir(ek_kayit_klasoru)

    if ekli_dosyalar:
        for dosya in ekli_dosyalar:
            dosya_yolu = os.path.join(ek_kayit_klasoru, dosya)
            col1, col2 = st.columns([8, 1])
            with col1:
                st.markdown(f"📄 {dosya}")
            with col2:
                if st.button("🗑 Sil", key=f"sil_{dosya}"):
                    os.remove(dosya_yolu)
                    st.success(f"🗑 {dosya} silindi.")
                    time.sleep(1)
                    st.warning("Sayfa yeniden yüklenmesi için F5'e basın.")
    else:
        st.info("ℹ️ Bu rapora henüz dosya eklenmemiş.")

with sekme2:
    st.subheader("🛠️ Değerlendirme Paneli")

    # Önceki kayıtları oku
    kayit = cursor.execute("SELECT * FROM voluntary_degerlendirme WHERE report_number = ?", (secili_rapor_no,)).fetchone()

    durumlar = ["Beklemede", "İşlemde", "Tamamlandı"]

    # Kayıt varsa varsayılan değer olarak kullan, yoksa boş bırak
    degerlendirme_durumu = st.selectbox(
        "Değerlendirme Durumu", 
        durumlar, 
        index=durumlar.index(kayit[1]) if kayit else 0
    )
    sonuc_durumu = st.text_area("Sonuç Durumu", value=kayit[2] if kayit else "")
    geri_bildirim = st.text_area("Geri Bildirim", value=kayit[3] if kayit else "")
    atanan_kisi = st.text_input("Atanan Kişi", value=kayit[4] if kayit else "")
    atama_tarihi = st.date_input("Atama Tarihi", value=pd.to_datetime(kayit[5]).date() if kayit else pd.to_datetime("today").date())

    if st.button("💾 Kaydet"):
        cursor.execute("""
            INSERT INTO voluntary_degerlendirme (report_number, degerlendirme_durumu, sonuc_durumu, geri_bildirim, atanan_kisi, atama_tarihi)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(report_number) DO UPDATE SET
                degerlendirme_durumu=excluded.degerlendirme_durumu,
                sonuc_durumu=excluded.sonuc_durumu,
                geri_bildirim=excluded.geri_bildirim,
                atanan_kisi=excluded.atanan_kisi,
                atama_tarihi=excluded.atama_tarihi
        """, (secili_rapor_no, degerlendirme_durumu, sonuc_durumu, geri_bildirim, atanan_kisi, atama_tarihi))
        conn.commit()
        st.success("✅ Değerlendirme bilgileri kaydedildi.")
        guncelle_tamamlanma_durumu(secili_rapor_no)


    # Kayıtlı bilgiler
    if kayit:
        st.markdown("---")
        st.markdown("### 📌 Kayıtlı Bilgiler")
        st.write({
            "Durum": kayit[1],
            "Sonuç": kayit[2],
            "Geri Bildirim": kayit[3],
            "Atanan Kişi": kayit[4],
            "Atama Tarihi": kayit[5]
        })

    # Bölüm tamamlanma durumu
    bolum_tamamlanma_goster("Değerlendirme Paneli", secili_rapor_no)

with sekme3:
    st.subheader("⚠️ Risk Değerlendirme (ICAO 9859)")

    # Eski risk bilgilerini getir
    risk_kayit = cursor.execute("SELECT * FROM voluntary_risk WHERE report_number = ?", (secili_rapor_no,)).fetchone()

    # Varsayılan değer atamaları
    tehlike_tanimi = st.text_area("Tehlike Tanımı (Hazard Description)", value=risk_kayit[1] if risk_kayit else "")
    potansiyel_sonuclar = st.text_area("Potansiyel Sonuçlar (Consequences)", value=risk_kayit[2] if risk_kayit else "")

    severity_list = ["1 - Negligible", "2 - Minor", "3 - Major", "4 - Hazardous", "5 - Catastrophic"]
    severity = st.selectbox("Şiddet (Severity)", severity_list,
                            index=severity_list.index(risk_kayit[3]) if risk_kayit else 0)

    likelihood_list = ["1 - Rare", "2 - Unlikely", "3 - Possible", "4 - Likely", "5 - Frequent"]
    likelihood = st.selectbox("Olasılık (Likelihood)", likelihood_list,
                              index=likelihood_list.index(risk_kayit[4]) if risk_kayit else 0)

    mevcut_onlemler = st.text_area("Mevcut Önlemler (Existing Mitigations)", value=risk_kayit[5] if risk_kayit else "")

    risk_seviye_list = ["Low", "Medium", "High", "Extreme"]
    risk_seviyesi = st.selectbox("İlk Risk Seviyesi (Initial Risk Level)", risk_seviye_list,
                                 index=risk_seviye_list.index(risk_kayit[6]) if risk_kayit else 0)

    if st.button("💾 Risk Bilgisini Kaydet"):
        cursor.execute("""
            INSERT INTO voluntary_risk (report_number, tehlike_tanimi, potansiyel_sonuclar, severity, likelihood, mevcut_onlemler, risk_seviyesi)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(report_number) DO UPDATE SET
                tehlike_tanimi=excluded.tehlike_tanimi,
                potansiyel_sonuclar=excluded.potansiyel_sonuclar,
                severity=excluded.severity,
                likelihood=excluded.likelihood,
                mevcut_onlemler=excluded.mevcut_onlemler,
                risk_seviyesi=excluded.risk_seviyesi
        """, (secili_rapor_no, tehlike_tanimi, potansiyel_sonuclar, severity, likelihood, mevcut_onlemler, risk_seviyesi))
        conn.commit()
        st.success("✅ Risk değerlendirme bilgileri kaydedildi.")
        guncelle_tamamlanma_durumu(secili_rapor_no)


    # Kayıtlı bilgiler
    if kayit:
        st.markdown("---")
        st.markdown("### 📌 Kayıtlı Bilgiler")
        st.write({
            "Durum": kayit[1],
            "Sonuç": kayit[2],
            "Geri Bildirim": kayit[3],
            "Atanan Kişi": kayit[4],
            "Atama Tarihi": kayit[5]
        })

    # Bölüm tamamlanma durumu
    bolum_tamamlanma_goster("Değerlendirme Paneli", secili_rapor_no)

with sekme4:
    st.subheader("✅ Önlemler ve Takip")

    # Mevcut kayıt varsa getir
    onlem_kayit = cursor.execute("SELECT * FROM voluntary_onlem WHERE report_number = ?", (secili_rapor_no,)).fetchone()

    onlem_aciklamasi = st.text_area("Düzeltici/Önleyici Faaliyet Açıklaması", value=onlem_kayit[1] if onlem_kayit else "")
    sorumlu_kisi = st.text_input("Sorumlu Kişi veya Birim", value=onlem_kayit[2] if onlem_kayit else "")
    
    termin_tarihi = st.date_input(
        "Termin Tarihi", 
        value=pd.to_datetime(onlem_kayit[3]).date() if onlem_kayit and onlem_kayit[3] else pd.to_datetime("today").date()
    )
    gerceklesme_tarihi = st.date_input(
        "Gerçekleşme Tarihi", 
        value=pd.to_datetime(onlem_kayit[4]).date() if onlem_kayit and onlem_kayit[4] else pd.to_datetime("today").date()
    )

    etkinlik_listesi = ["Etkili", "Kısmen Etkili", "Etkisiz"]
    etkinlik_kontrolu = st.selectbox("Etkinlik Kontrolü Sonucu", etkinlik_listesi, 
                                     index=etkinlik_listesi.index(onlem_kayit[5]) if onlem_kayit else 0)

    risk_listesi = ["Low", "Medium", "High", "Extreme"]
    revize_risk = st.selectbox("Revize Edilmiş Risk Seviyesi", risk_listesi, 
                               index=risk_listesi.index(onlem_kayit[6]) if onlem_kayit else 0)

    if st.button("💾 Önlemleri Kaydet"):
        cursor.execute("""
            INSERT INTO voluntary_onlem (report_number, onlem_aciklamasi, sorumlu_kisi, termin_tarihi, gerceklesme_tarihi, etkinlik_kontrolu, revize_risk)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(report_number) DO UPDATE SET
                onlem_aciklamasi=excluded.onlem_aciklamasi,
                sorumlu_kisi=excluded.sorumlu_kisi,
                termin_tarihi=excluded.termin_tarihi,
                gerceklesme_tarihi=excluded.gerceklesme_tarihi,
                etkinlik_kontrolu=excluded.etkinlik_kontrolu,
                revize_risk=excluded.revize_risk
        """, (secili_rapor_no, onlem_aciklamasi, sorumlu_kisi, termin_tarihi, gerceklesme_tarihi, etkinlik_kontrolu, revize_risk))
        conn.commit()
        st.success("✅ Önlemler ve takip bilgileri kaydedildi.")
        guncelle_tamamlanma_durumu(secili_rapor_no)


    # Kayıtlı bilgiler
    if kayit:
        st.markdown("---")
        st.markdown("### 📌 Kayıtlı Bilgiler")
        st.write({
            "Durum": kayit[1],
            "Sonuç": kayit[2],
            "Geri Bildirim": kayit[3],
            "Atanan Kişi": kayit[4],
            "Atama Tarihi": kayit[5]
        })

    # Bölüm tamamlanma durumu
    bolum_tamamlanma_goster("Değerlendirme Paneli", secili_rapor_no)

with sekme5:
    st.subheader("📤 Geri Bildirim")

    # Mevcut kayıt varsa getir
    geri_kayit = cursor.execute("SELECT * FROM voluntary_geri_bildirim WHERE report_number = ?", (secili_rapor_no,)).fetchone()

    geri_gonderen = st.text_input("Geri Bildirim Gönderen", value=geri_kayit[1] if geri_kayit else "")
    geri_icerik = st.text_area("Geri Bildirim Metni", value=geri_kayit[2] if geri_kayit else "")
    geri_tarih = st.date_input(
        "Gönderim Tarihi", 
        value=pd.to_datetime(geri_kayit[3]).date() if geri_kayit and geri_kayit[3] else pd.to_datetime("today").date()
    )

    if st.button("📨 Geri Bildirimi Kaydet"):
        cursor.execute("""
            INSERT INTO voluntary_geri_bildirim (report_number, gonderen, icerik, tarih)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(report_number) DO UPDATE SET
                gonderen=excluded.gonderen,
                icerik=excluded.icerik,
                tarih=excluded.tarih
        """, (secili_rapor_no, geri_gonderen, geri_icerik, geri_tarih))
        conn.commit()
        st.success("✅ Geri bildirim kaydedildi.")
        guncelle_tamamlanma_durumu(secili_rapor_no)


    # Kayıtlı bilgiler
    if kayit:
        st.markdown("---")
        st.markdown("### 📌 Kayıtlı Bilgiler")
        st.write({
            "Durum": kayit[1],
            "Sonuç": kayit[2],
            "Geri Bildirim": kayit[3],
            "Atanan Kişi": kayit[4],
            "Atama Tarihi": kayit[5]
        })

    # Bölüm tamamlanma durumu
    bolum_tamamlanma_goster("Değerlendirme Paneli", secili_rapor_no)



with sekme6:
    st.subheader("📈 Durum ve Kapanış")

    # Mevcut kayıt varsa getir
    kapanis_kayit = cursor.execute("SELECT * FROM voluntary_kapanis WHERE report_number = ?", (secili_rapor_no,)).fetchone()

    durumlar = ["Açık", "İşlemde", "Kapandı"]
    durum = st.selectbox("Rapor Durumu", durumlar,
                         index=durumlar.index(kapanis_kayit[1]) if kapanis_kayit else 0)

    degerlendirme_tarihi = st.date_input(
        "Değerlendirme Tarihi",
        value=pd.to_datetime(kapanis_kayit[2]).date() if kapanis_kayit and kapanis_kayit[2] else pd.to_datetime("today").date()
    )
    kapanis_tarihi = st.date_input(
        "Kapanış Tarihi",
        value=pd.to_datetime(kapanis_kayit[3]).date() if kapanis_kayit and kapanis_kayit[3] else pd.to_datetime("today").date()
    )

    if st.button("📌 Durum Bilgilerini Kaydet"):
        cursor.execute("""
            INSERT INTO voluntary_kapanis (report_number, durum, degerlendirme_tarihi, kapanis_tarihi)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(report_number) DO UPDATE SET
                durum=excluded.durum,
                degerlendirme_tarihi=excluded.degerlendirme_tarihi,
                kapanis_tarihi=excluded.kapanis_tarihi
        """, (secili_rapor_no, durum, degerlendirme_tarihi, kapanis_tarihi))
        conn.commit()
        st.success("✅ Durum ve kapanış bilgileri kaydedildi.")
        guncelle_tamamlanma_durumu(secili_rapor_no)


    # Kayıtlı bilgiler
    if kayit:
        st.markdown("---")
        st.markdown("### 📌 Kayıtlı Bilgiler")
        st.write({
            "Durum": kayit[1],
            "Sonuç": kayit[2],
            "Geri Bildirim": kayit[3],
            "Atanan Kişi": kayit[4],
            "Atama Tarihi": kayit[5]
        })

    # Bölüm tamamlanma durumu
    bolum_tamamlanma_goster("Değerlendirme Paneli", secili_rapor_no)


    st.markdown("---")
    st.subheader("📋 Tüm Raporların Kapanış Durumu ve Değerlendirme Durumu")

    # Kapanış bilgisiyle birlikte tüm raporları getir (sol join yapısı)
    query = """
    SELECT vr.report_number, vr.olay_tarihi, 
           COALESCE(vk.durum, 'Henüz Değerlendirilmedi') AS durum
    FROM voluntary_reports vr
    LEFT JOIN voluntary_kapanis vk ON vr.report_number = vk.report_number
    ORDER BY 
        CASE COALESCE(vk.durum, 'Henüz Değerlendirilmedi')
            WHEN 'Açık' THEN 0
            WHEN 'İşlemde' THEN 1
            WHEN 'Henüz Değerlendirilmedi' THEN 2
            WHEN 'Kapandı' THEN 3
            ELSE 4
        END,
        vr.olay_tarihi DESC
    """

    tum_durumlar_df = pd.read_sql_query(query, conn)

    # Renkli rozet oluşturucu
    def durum_rozet(durum):
        renk_map = {
            "Açık": "#ef4444",
            "İşlemde": "#facc15",
            "Kapandı": "#10b981",
            "Henüz Değerlendirilmedi": "#9ca3af"
        }
        renk = renk_map.get(durum, "#d1d5db")
        return f"<span style='background-color:{renk}; color:white; padding:4px 10px; border-radius:12px;'>{durum}</span>"

    if not tum_durumlar_df.empty:
        tum_durumlar_df["Durum"] = tum_durumlar_df["durum"].apply(durum_rozet)
        tum_durumlar_df["Tarih"] = pd.to_datetime(tum_durumlar_df["olay_tarihi"]).dt.strftime("%Y-%m-%d")
        tum_durumlar_df = tum_durumlar_df[["report_number", "Tarih", "Durum"]]
        tum_durumlar_df.columns = ["Rapor No", "Olay Tarihi", "Durum"]

        # Scrollable stil
        st.markdown("""
        <style>
        .scrollable-table {
            overflow-x: auto;
            height: 400px;
            border: 1px solid #ccc;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            color: inherit;
        }

        thead th {
            position: sticky;
            top: 0;
            background-color: #333333;  /* ✅ koyu gri başlık */
            color: white;
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #666;
        }

        tbody td {
            padding: 8px;
            border-bottom: 1px solid #ddd;
            background-color: #1e1e1e; /* ✅ koyu satır zemini (dark mode uyumlu) */
        }
        </style>
        """, unsafe_allow_html=True)

        html_table = tum_durumlar_df.to_html(escape=False, index=False)
        st.markdown(f"<div class='scrollable-table'>{html_table}</div>", unsafe_allow_html=True)

    else:
        st.info("Henüz hiçbir rapor kayıtlı değil.")

with sekme7:


    # Bölüm tamamlanma durumu
    bolum_tamamlanma_goster("Genel Özet ve İnceleme", secili_rapor_no)
    st.subheader("📋 Rapor Genel Özeti")
    
    
    # 1. Temel bilgiler
    st.markdown(f"**Rapor Numarası:** `{secili_rapor['report_number']}`")
    st.markdown(f"**Rapor Türü:** {secili_rapor['rapor_turu']}")
    st.markdown(f"**Rapor Konusu:** {secili_rapor['rapor_konusu']}")
    st.markdown(f"**Olay Tarihi:** {secili_rapor['olay_tarihi']}")
    st.markdown(f"**Veri Giriş Tarihi:** {secili_rapor['veri_giris_tarihi']}")

    # 2. Form cevapları
    if ozel_cevaplar:
        st.markdown("---")
        st.subheader("📝 Form Cevapları")
        for soru, cevap in cevap_dict.items():
            st.markdown(f"- **{soru}**: {cevap if cevap else '-'}")
    
    # 3. Değerlendirme
    kayit = cursor.execute("SELECT * FROM voluntary_degerlendirme WHERE report_number = ?", (secili_rapor_no,)).fetchone()
    if kayit:
        st.markdown("---")
        st.subheader("🛠️ Değerlendirme Bilgileri")
        st.write({
            "Durum": kayit[1],
            "Sonuç": kayit[2],
            "Geri Bildirim": kayit[3],
            "Atanan Kişi": kayit[4],
            "Atama Tarihi": kayit[5]
        })

    # 4. Risk
    risk = cursor.execute("SELECT * FROM voluntary_risk WHERE report_number = ?", (secili_rapor_no,)).fetchone()
    if risk:
        st.markdown("---")
        st.subheader("⚠️ Risk Değerlendirme")
        st.write({
            "Tehlike Tanımı": risk[1],
            "Potansiyel Sonuçlar": risk[2],
            "Severity": risk[3],
            "Likelihood": risk[4],
            "Mevcut Önlemler": risk[5],
            "İlk Risk Seviyesi": risk[6],
        })

    # 5. Önlemler
    onlem = cursor.execute("SELECT * FROM voluntary_onlem WHERE report_number = ?", (secili_rapor_no,)).fetchone()
    if onlem:
        st.markdown("---")
        st.subheader("✅ Önlem ve Faaliyetler")
        st.write({
            "Açıklama": onlem[1],
            "Sorumlu Kişi": onlem[2],
            "Termin": onlem[3],
            "Gerçekleşme": onlem[4],
            "Etkinlik Kontrolü": onlem[5],
            "Revize Risk": onlem[6],
        })

    # 6. Geri bildirim
    geri = cursor.execute("SELECT * FROM voluntary_geri_bildirim WHERE report_number = ?", (secili_rapor_no,)).fetchone()
    if geri:
        st.markdown("---")
        st.subheader("📤 Geri Bildirim")
        st.write({
            "Gönderen": geri[1],
            "İçerik": geri[2],
            "Tarih": geri[3]
        })

    # 7. Kapanış
    kapanis = cursor.execute("SELECT * FROM voluntary_kapanis WHERE report_number = ?", (secili_rapor_no,)).fetchone()
    if kapanis:
        st.markdown("---")
        st.subheader("📈 Durum ve Kapanış")
        st.write({
            "Durum": kapanis[1],
            "Değerlendirme Tarihi": kapanis[2],
            "Kapanış Tarihi": kapanis[3]
        })

    # 8. Ekler
    st.markdown("---")
    st.subheader("📎 Ek Dosyalar")
    if ekli_dosyalar:
        for dosya in ekli_dosyalar:
            st.markdown(f"- 📄 {dosya}")
    else:
        st.info("Ekli dosya bulunmamaktadır.")






with sekme8:
    st.subheader("📋 Tüm Raporların Tamamlanma Durumu")

    progress_df = pd.read_sql_query("SELECT * FROM voluntary_progress ORDER BY yuzde DESC", conn)

    if not progress_df.empty:
        progress_df["Tamamlanma (%)"] = progress_df["yuzde"].astype(str) + "%"

        for i, row in progress_df.iterrows():
            with st.expander(f"📄 {row['report_number']} - {row['yuzde']}% tamamlandı"):
                st.markdown(f"""
                - **Tamamlanan:** {row['tamamlanan']} / {row['toplam']}
                - **Eksik Bölümler:** {row['eksikler'] or 'YOK'}
                """)

                with st.form(f"silme_formu_{row['report_number']}"):
                    st.warning("⚠️ Bu raporla ilişkili tüm veriler silinecektir.")
                    onay = st.checkbox("Evet, bu raporu silmek istiyorum.")
                    submitted = st.form_submit_button("🗑 Raporu Kalıcı Olarak Sil")

                    if submitted and onay:
                        raporu_sil(row['report_number'])
                        st.success("✅ Rapor ve bağlı tüm veriler silindi.")
                        st.rerun()
                    elif submitted and not onay:
                        st.error("Silme işlemi için onay vermediniz.")

        st.markdown(f"📊 Toplam kayıtlı rapor: **{len(progress_df)}**")

    else:
        st.info("Henüz hiçbir rapor için tamamlanma bilgisi kaydedilmemiş.")


    # Veriyi birleştir: reports + kapanis + progress
    query = """
    SELECT vr.report_number, vr.olay_tarihi, vk.durum, vp.tamamlanan, vp.toplam, vp.yuzde, vp.eksikler
    FROM voluntary_reports vr
    LEFT JOIN voluntary_kapanis vk ON vr.report_number = vk.report_number
    LEFT JOIN voluntary_progress vp ON vr.report_number = vp.report_number
    ORDER BY vr.olay_tarihi DESC
    """
    rapor_df = pd.read_sql_query(query, conn)

    if rapor_df.empty:
        st.info("Henüz kayıtlı rapor bulunmuyor.")
    else:
        st.markdown("### 🔍 Filtreleme Seçenekleri")
        filtre_tipi = st.selectbox("Filtre türü seçin", ["Tarihe göre", "Duruma göre", "Tümünü Göster"])

        if filtre_tipi == "Tarihe göre":
            rapor_df["olay_tarihi"] = pd.to_datetime(rapor_df["olay_tarihi"])
            min_tarih, max_tarih = rapor_df["olay_tarihi"].min(), rapor_df["olay_tarihi"].max()
            baslangic, bitis = st.date_input("Tarih Aralığı Seçin", [min_tarih, max_tarih])
            mask = (rapor_df["olay_tarihi"] >= pd.to_datetime(baslangic)) & (rapor_df["olay_tarihi"] <= pd.to_datetime(bitis))
            filtreli_df = rapor_df[mask]

        elif filtre_tipi == "Duruma göre":
            mevcut_durumlar = rapor_df["durum"].dropna().unique().tolist()
            secilen_durum = st.multiselect("Rapor Durumu Seçin", mevcut_durumlar, default=mevcut_durumlar)
            filtreli_df = rapor_df[rapor_df["durum"].isin(secilen_durum)]
        else:
            filtreli_df = rapor_df

        st.markdown(f"Toplam filtrelenmiş kayıt: **{len(filtreli_df)}**")

        for i, row in enumerate(filtreli_df.iterrows()):
            row_data = row[1]  # DataFrameRow içeriği

            with st.expander(f"📄 {row_data['report_number']} - {row_data['yuzde']}% tamamlandı"):
                st.markdown(f"""
                - 🗓️ **Olay Tarihi:** {row_data['olay_tarihi']}
                - 📌 **Durum:** {row_data['durum'] or '-'}
                - ✅ **Tamamlanan:** {row_data['tamamlanan']} / {row_data['toplam']}
                - 🚧 **Eksik Bölümler:** {row_data['eksikler'] or 'YOK'}
                """)

                # 🔑 FORM KEY EŞSİZ OLACAK ŞEKİLDE i ile birlikte veriliyor
                with st.form(f"silme_formu_{row_data['report_number']}_{i}"):
                    st.warning("⚠️ Bu raporla ilişkili tüm veriler kalıcı olarak silinecektir.")
                    onay = st.checkbox("Evet, bu raporu silmek istiyorum.", key=f"onay_{i}")
                    submitted = st.form_submit_button("🗑 Raporu Kalıcı Olarak Sil", type="primary")

                    if submitted and onay:
                        raporu_sil(row_data['report_number'])
                        st.success("✅ Rapor ve tüm ilişkili veriler başarıyla silindi.")
                        st.rerun()
                    elif submitted and not onay:
                        st.error("Silme işlemi için onay vermediniz.")

        # Takvim görünümü
        # 📅 RAPOR TAKVİMİ
        st.subheader("📅 Aylık Rapor Takvimi")

        try:
            from streamlit_calendar import calendar

            renkler = {
                "Kapandı": "#10b981",     # yeşil
                "İşlemde": "#facc15",     # sarı
                "Açık": "#ef4444",        # kırmızı
                None: "#9ca3af"           # gri
            }

            # Gerekli veriyi birleştir
            query = """
            SELECT vr.report_number, vr.olay_tarihi, vk.durum, vr.rapor_turu, vr.rapor_konusu
            FROM voluntary_reports vr
            LEFT JOIN voluntary_kapanis vk ON vr.report_number = vk.report_number
            ORDER BY vr.olay_tarihi DESC
            """
            raporlar_df = pd.read_sql_query(query, conn)
            raporlar_df["olay_tarihi"] = pd.to_datetime(raporlar_df["olay_tarihi"])

            events = []
            for _, row in raporlar_df.iterrows():
                events.append({
                    "title": row["report_number"],
                    "start": row["olay_tarihi"].strftime("%Y-%m-%d"),
                    "end": row["olay_tarihi"].strftime("%Y-%m-%d"),
                    "color": renkler.get(row["durum"], "#9ca3af"),
                    "extendedProps": {
                        "durum": row["durum"],
                        "rapor_turu": row["rapor_turu"],
                        "rapor_konusu": row["rapor_konusu"]
                    }
                })

            calendar_options = {
                "initialView": "dayGridMonth",
                "locale": "tr",
                "headerToolbar": {
                    "left": "prev,next today",
                    "center": "title",
                    "right": ""
                },
                "height": 600
            }

            selected_event = calendar(events=events, options=calendar_options, key="rapor_takvim")

            event = selected_event.get("event", {})
            if event:
                with st.expander(f"📋 Rapor: {event['title']}", expanded=True):
                    st.markdown(f"📅 **Tarih:** {event['start']}")
                    st.markdown(f"🧾 **Rapor Türü:** {event['extendedProps']['rapor_turu']}")
                    st.markdown(f"🔖 **Konu:** {event['extendedProps']['rapor_konusu']}")
                    st.markdown(f"📊 **Durum:** `{event['extendedProps']['durum'] or 'Bilinmiyor'}`")

        except ModuleNotFoundError:
            st.error("📦 `streamlit-calendar` modülü yüklü değil. Takvim için `pip install streamlit-calendar` komutunu çalıştırın.")


from fpdf import FPDF
import zipfile
import tempfile
import shutil
import textwrap
from openpyxl import Workbook

def create_excel_and_zip(report_number, data_dict, ek_dosya_klasoru):
    # 1. Geçici dizin ve Excel dosya yolu
    temp_dir = tempfile.mkdtemp()
    excel_path = os.path.join(temp_dir, f"{report_number}_ozet.xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = "Rapor Özeti"

    # Başlık satırı
    ws.append(["Bölüm", "Alan", "Değer"])

    for bolum, bilgiler in data_dict.items():
        ws.append([bolum, "", ""])  # Bölüm başlığı
        for k, v in bilgiler.items():
            v_str = str(v).replace("\n", " ").strip()
            ws.append(["", k, v_str])
        ws.append(["", "", ""])  # Bölüm arası boşluk

    wb.save(excel_path)

    # 2. ZIP dosyasını oluştur
    zip_path = os.path.join(temp_dir, f"{report_number}_rapor.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(excel_path, arcname=f"{report_number}_ozet.xlsx")
        if os.path.exists(ek_dosya_klasoru):
            for dosya in os.listdir(ek_dosya_klasoru):
                tam_yol = os.path.join(ek_dosya_klasoru, dosya)
                zipf.write(tam_yol, arcname=f"ekler/{dosya}")

    return zip_path


with sekme9:
    
    
    st.subheader(f"📄 Rapor Özeti: {secili_rapor_no}")

    st.markdown("### 🧾 Temel Bilgiler")
    st.write({
        "Rapor Türü": secili_rapor["rapor_turu"],
        "Rapor Konusu": secili_rapor["rapor_konusu"],
        "Olay Tarihi": secili_rapor["olay_tarihi"],
        "Veri Giriş Tarihi": secili_rapor["veri_giris_tarihi"]
    })

    if secili_rapor.get("ozel_cevaplar"):
        try:
            cevap_dict = eval(secili_rapor["ozel_cevaplar"]) if isinstance(secili_rapor["ozel_cevaplar"], str) else secili_rapor["ozel_cevaplar"]
            st.markdown("### 📝 Form Cevapları")
            for soru, cevap in cevap_dict.items():
                st.markdown(f"- **{soru}**: {cevap if cevap else '-'}")
        except:
            st.error("❌ Form cevapları ayrıştırılamadı.")

    st.markdown("### 🛠️ Değerlendirme Paneli")
    kayit = cursor.execute("SELECT * FROM voluntary_degerlendirme WHERE report_number = ?", (secili_rapor_no,)).fetchone()
    if kayit:
        st.write({
            "Durum": kayit[1],
            "Sonuç": kayit[2],
            "Geri Bildirim": kayit[3],
            "Atanan Kişi": kayit[4],
            "Atama Tarihi": kayit[5]
        })

    st.markdown("### ⚠️ Risk Değerlendirme")
    risk = cursor.execute("SELECT * FROM voluntary_risk WHERE report_number = ?", (secili_rapor_no,)).fetchone()
    if risk:
        st.write({
            "Tehlike Tanımı": risk[1],
            "Potansiyel Sonuçlar": risk[2],
            "Şiddet (Severity)": risk[3],
            "Olasılık (Likelihood)": risk[4],
            "Mevcut Önlemler": risk[5],
            "İlk Risk Seviyesi": risk[6]
        })

    st.markdown("### ✅ Önlemler ve Takip")
    onlem = cursor.execute("SELECT * FROM voluntary_onlem WHERE report_number = ?", (secili_rapor_no,)).fetchone()
    if onlem:
        st.write({
            "Açıklama": onlem[1],
            "Sorumlu Kişi": onlem[2],
            "Termin": onlem[3],
            "Gerçekleşme": onlem[4],
            "Etkinlik Kontrolü": onlem[5],
            "Revize Risk": onlem[6]
        })

    st.markdown("### 📤 Geri Bildirim")
    geri = cursor.execute("SELECT * FROM voluntary_geri_bildirim WHERE report_number = ?", (secili_rapor_no,)).fetchone()
    if geri:
        st.write({
            "Gönderen": geri[1],
            "İçerik": geri[2],
            "Tarih": geri[3]
        })

    st.markdown("### 📈 Kapanış Bilgisi")
    kapanis = cursor.execute("SELECT * FROM voluntary_kapanis WHERE report_number = ?", (secili_rapor_no,)).fetchone()
    if kapanis:
        st.write({
            "Durum": kapanis[1],
            "Değerlendirme Tarihi": kapanis[2],
            "Kapanış Tarihi": kapanis[3]
        })

    st.markdown("### 📎 Ekli Dosyalar")
    ek_klasor = os.path.join("uploads/voluntary_ekler", slugify(secili_rapor_no))
    if os.path.exists(ek_klasor):
        dosyalar = os.listdir(ek_klasor)
        for d in dosyalar:
            st.markdown(f"- 📎 {d}")
    else:
        st.info("Bu rapora ait ek bulunmamaktadır.")

    
    st.markdown("---")
    st.subheader("📤 Dışa Aktarma")

    # CSV için veri sözlüğü (aynı PDF gibi)
    rapor_data = {
        "Temel Bilgiler": {
            "Rapor Türü": secili_rapor["rapor_turu"],
            "Rapor Konusu": secili_rapor["rapor_konusu"],
            "Olay Tarihi": secili_rapor["olay_tarihi"],
            "Veri Giriş Tarihi": secili_rapor["veri_giris_tarihi"]
        }
    }
    if kayit:
        rapor_data["Değerlendirme"] = {
            "Durum": kayit[1], "Sonuç": kayit[2], "Geri Bildirim": kayit[3],
            "Atanan Kişi": kayit[4], "Atama Tarihi": kayit[5]
        }
    if risk:
        rapor_data["Risk"] = {
            "Tehlike Tanımı": risk[1], "Potansiyel Sonuçlar": risk[2],
            "Severity": risk[3], "Likelihood": risk[4],
            "Önlemler": risk[5], "İlk Risk Seviyesi": risk[6]
        }
    if onlem:
        rapor_data["Önlemler"] = {
            "Açıklama": onlem[1], "Sorumlu": onlem[2],
            "Termin": onlem[3], "Gerçekleşme": onlem[4],
            "Etkinlik": onlem[5], "Revize Risk": onlem[6]
        }
    if geri:
        rapor_data["Geri Bildirim"] = {
            "Gönderen": geri[1], "İçerik": geri[2], "Tarih": geri[3]
        }
    if kapanis:
        rapor_data["Kapanış"] = {
            "Durum": kapanis[1], "Değerlendirme Tarihi": kapanis[2],
            "Kapanış Tarihi": kapanis[3]
        }

    ek_klasor = os.path.join("uploads/voluntary_ekler", slugify(secili_rapor_no))

    if st.button("🗜️ Excel + Eklerle ZIP Olarak İndir"):
        zip_path = create_excel_and_zip(secili_rapor_no, rapor_data, ek_klasor)
        with open(zip_path, "rb") as f:
            st.download_button("📥 ZIP Dosyasını İndir", f, file_name=f"{secili_rapor_no}_rapor.zip")








