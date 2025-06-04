import subprocess
import time
import webbrowser
import os
import sys

# 1) Uygulama dosyanızın yolu (exe içine gömüldüğünde de çalışsın diye)
BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.argv[0])))
app_script = os.path.join(BASE_DIR, 'streamlit_app.py')

# 2) Streamlit server’ı başlat
#    --server.address=0.0.0.0 ile LAN’a açıyoruz
cmd = [
    sys.executable, '-m', 'streamlit', 'run', app_script,
    '--server.address', '0.0.0.0',
    '--server.port', '8501'
]
subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

# 3) Kısa bir bekleme, server ayağa kalksın
time.sleep(3)

# 4) Chrome ile aç
#    Chrome’un path’i Windows’ta varsayılan konumdaysa:
chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if os.path.exists(chrome_path):
    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
    # Launch the Streamlit app on the same port as the server
    webbrowser.get('chrome').open("http://localhost:8501")
else:
    # Chrome bulunamazsa, default tarayıcı
    webbrowser.open("http://localhost:8501")

# 5) Launcher’ı açık tutmak için sonsuz döngü
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
