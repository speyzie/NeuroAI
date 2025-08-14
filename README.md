## NeuroAI

Streamlit tabanlı bilişsel değerlendirme platformu. Firebase (Auth + Firestore) ve Google Gemini 2.5 Flash ile raporlama yapar.

### Hızlı Başlangıç
1. `pip install -r requirements.txt`
2. `.streamlit/secrets.toml` dosyasını, örneğe göre oluşturun.
3. `streamlit run app.py`

### Gerekli Secrets
`.streamlit/secrets.toml` içeriğini örneğe göre doldurun:

```
[firebase]
api_key = "YOUR_API_KEY"
auth_domain = "YOUR_PROJECT.firebaseapp.com"
database_url = "https://YOUR_PROJECT.firebaseio.com"
project_id = "YOUR_PROJECT"
storage_bucket = "YOUR_PROJECT.appspot.com"
messaging_sender_id = "..."
app_id = "..."

# Firebase Admin (Service Account JSON içeriğini tek satır JSON olarak koyun)
service_account_json = "{\"type\":\"service_account\",...}"

[gemini]
api_key = "YOUR_GEMINI_API_KEY"
```

### Sayfalar
- `auth.py`: Kayıt/Giriş
- `dashboard.py`: Ana panel
- `tests.py`: Testler
- `results.py`: Sonuçlar
- `reports.py`: Raporlar (Gemini + PDF)
- `settings.py`: Ayarlar

### Not
- Üretimde Firestore kuralları, kimlik doğrulama ve gizlilik ayarlarını sıkılaştırın.
