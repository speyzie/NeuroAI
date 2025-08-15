# 🚀 NeuroAI Deployment Guide

Bu rehber, NeuroAI uygulamanızı ücretsiz olarak yayınlamanız için adım adım talimatları içerir.

## 📋 Ön Gereksinimler

1. **GitHub Repository**: Kodunuz GitHub'da olmalı
2. **Firebase Projesi**: Firebase Console'da proje kurulu olmalı
3. **API Anahtarları**: Firebase ve Gemini API anahtarları hazır olmalı

## 🌐 Deployment Seçenekleri

### 1. Streamlit Cloud (Önerilen - En Kolay)

**Avantajları:**
- ✅ Tamamen ücretsiz
- ✅ Otomatik deployment
- ✅ GitHub entegrasyonu
- ✅ SSL sertifikası dahil
- ✅ Özel domain desteği

**Adımlar:**

1. **Streamlit Cloud'a Git**
   - https://share.streamlit.io/ adresine git
   - GitHub hesabınızla giriş yap

2. **Repository Seç**
   - "New app" butonuna tıkla
   - GitHub repository'nizi seç: `speyzie/NeuroAI`

3. **Konfigürasyon**
   - **Main file path**: `streamlit_app.py`
   - **App URL**: `neuroai-cognitive-tests` (veya istediğiniz isim)

4. **Secrets Ekle**
   - "Advanced settings" → "Secrets"
   - `.streamlit/secrets.toml` içeriğini yapıştır:

```toml
[firebase]
api_key = "YOUR_FIREBASE_API_KEY"
auth_domain = "YOUR_PROJECT.firebaseapp.com"
database_url = "https://YOUR_PROJECT.firebaseio.com"
project_id = "YOUR_PROJECT"
storage_bucket = "YOUR_PROJECT.appspot.com"
messaging_sender_id = "YOUR_SENDER_ID"
app_id = "YOUR_APP_ID"
service_account_json = '''
{
  "type": "service_account",
  "project_id": "YOUR_PROJECT",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
'''

[gemini]
api_key = "YOUR_GEMINI_API_KEY"
```

5. **Deploy Et**
   - "Deploy!" butonuna tıkla
   - 2-3 dakika bekleyin

**Sonuç:** `https://neuroai-cognitive-tests.streamlit.app`

### 2. Railway (Alternatif)

**Avantajları:**
- ✅ Ücretsiz tier mevcut
- ✅ Otomatik deployment
- ✅ Database desteği

**Adımlar:**

1. **Railway'e Git**
   - https://railway.app/ adresine git
   - GitHub hesabınızla giriş yap

2. **Proje Oluştur**
   - "New Project" → "Deploy from GitHub repo"
   - Repository'nizi seç

3. **Environment Variables**
   - Firebase ve Gemini API anahtarlarını environment variables olarak ekle

4. **Deploy Et**
   - Otomatik olarak deploy edilecek

### 3. Render (Alternatif)

**Avantajları:**
- ✅ Ücretsiz tier mevcut
- ✅ Otomatik SSL
- ✅ Özel domain

**Adımlar:**

1. **Render'e Git**
   - https://render.com/ adresine git
   - GitHub hesabınızla giriş yap

2. **Web Service Oluştur**
   - "New" → "Web Service"
   - Repository'nizi seç

3. **Konfigürasyon**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0`

4. **Environment Variables**
   - Firebase ve Gemini API anahtarlarını ekle

## 🔧 Deployment Sonrası

### 1. Firebase Güvenlik Kuralları

Firestore kurallarınızı production için güncelleyin:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Kullanıcılar sadece kendi verilerine erişebilir
    match /testResults/{document} {
      allow read, write: if request.auth != null && request.auth.uid == resource.data.userId;
    }
    
    // Profil verileri
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

### 2. Domain Ayarları

**Streamlit Cloud için:**
- Settings → Custom domain (isteğe bağlı)

**Özel Domain için:**
- DNS ayarlarınızı yapılandırın
- SSL sertifikası otomatik olarak sağlanır

### 3. Monitoring

- Uygulama loglarını takip edin
- Firebase Console'da kullanım istatistiklerini izleyin
- API kullanım limitlerini kontrol edin

## 🚨 Önemli Notlar

1. **API Anahtarları**: Asla GitHub'a commit etmeyin
2. **Firebase Kuralları**: Production'da sıkılaştırın
3. **Rate Limiting**: API kullanım limitlerini aşmayın
4. **Backup**: Düzenli olarak veri yedeklemesi yapın

## 📞 Destek

Deployment sırasında sorun yaşarsanız:
- Streamlit Cloud: https://docs.streamlit.io/streamlit-community-cloud
- Firebase: https://firebase.google.com/docs
- GitHub Issues: Repository'nizde issue açın

---

**🎉 Tebrikler!** Uygulamanız artık canlıda ve dünyanın her yerinden erişilebilir! 