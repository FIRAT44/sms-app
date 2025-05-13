import os
import streamlit as st

# ================================================
# 🛑 NETWORK DOSYASI ERİŞİM KONTROLÜ
USER_FILE = r"\\Ayjetfile\shared\SMS\1400-SMS PROGRAM\user.txt"
if not os.path.isfile(USER_FILE):
    st.error("‼️ Erişim hatası: Ağ üzerinde `user.txt` dosyasına ulaşılamıyor.\nLütfen local ağa bağlanın veya VPN ile erişim sağlayın.")
    st.stop()

# --------------------------------
from utils.auth import login_required  # Giriş kontrolü, her şeyden önce gelmeli
# login_required()  # Giriş yapılmadıysa sayfa burada durur

from utils.db_setup import initialize_database
initialize_database()

st.set_page_config(page_title="Ayjet SMS Programı ✈️", layout="wide")

st.title("Ayjet Uçuş Okulu SMS Programı ✈️")
st.markdown("""
Bu uygulama, Emniyet Yönetim Sistemi kapsamındaki raporlar, denetimler ve takip süreçlerini kolaylaştırmak amacıyla geliştirilmiştir.

👈 Soldaki menüden bir sayfa seçerek başlayabilirsiniz.
""")
