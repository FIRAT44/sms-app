import streamlit as st
from utils.auth import login_required
login_required()

st.set_page_config(page_title="Continuous Improvement Tools", layout="wide")
st.title("📊 Continuous Improvement Tools")


import zipfile
import io
import os
import streamlit as st

def zip_veri_yedegi():
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 📁 Veritabanı dosyasını ekle
        if os.path.exists("sms_database2.db"):
            zip_file.write("sms_database2.db", arcname="sms_database2.db")

        # 📁 Voluntary ekleri
        for root, _, files in os.walk("uploads/voluntary_ekler"):
            for file in files:
                tam_yol = os.path.join(root, file)
                zip_file.write(tam_yol, arcname=os.path.relpath(tam_yol, "uploads"))

        # 📁 Hazard ekleri
        for root, _, files in os.walk("uploads/hazard_ekler"):
            for file in files:
                tam_yol = os.path.join(root, file)
                zip_file.write(tam_yol, arcname=os.path.relpath(tam_yol, "uploads"))

    return zip_buffer.getvalue()

# 📦 Butonla indirilebilir hale getir
st.markdown("### 📥 Veri Yedeği")
st.download_button(
    label="📦 Tüm Sistemi ZIP Olarak İndir",
    data=zip_veri_yedegi(),
    file_name="sms_yedek.zip",
    mime="application/zip"
)

