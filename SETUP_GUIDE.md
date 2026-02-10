# 🚀 LEX Setup Guide

This guide will help you set up LEX securely for GitHub deployment.

---

## 📋 Pre-GitHub Checklist

Before pushing to GitHub, make sure you've completed these steps:

### ✅ Step 1: Remove Hardcoded Secrets

**Status**: ✅ COMPLETED

All hardcoded API keys have been removed from `app.py`. The application now uses the `config.py` module which loads from `.env` files.

### ✅ Step 2: Create `.env` File

1. Copy the template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your actual API key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   APP_PASSWORD=your_secure_password
   ```

3. **IMPORTANT**: Never commit this file to Git!

### ✅ Step 3: Verify `.gitignore`

**Status**: ✅ COMPLETED

The `.gitignore` file is configured to exclude:
- `.env` files
- `secrets.toml`
- API key files
- Virtual environments
- Sensitive data

### ✅ Step 4: Test Configuration

Run this to verify your setup:

```bash
python -c "from config import config; import json; print(json.dumps(config.get_config_status(), indent=2))"
```

Expected output:
```json
{
  "env_file_loaded": true,
  "api_key_configured": true,
  "api_key_length": 39,
  "model_name": "models/gemini-1.5-pro-latest",
  "pdf_directory": "lender_pdf_database",
  "password_configured": true
}
```

---

## 🔐 Security Checklist

Before pushing to GitHub:

- [ ] `.env` file is NOT in Git (check with `git status`)
- [ ] `.gitignore` includes `.env` and sensitive files
- [ ] No hardcoded API keys in `app.py`
- [ ] `.env.example` contains only placeholders
- [ ] API keys are stored only in `.env` locally

---

## 📤 Push to GitHub

### First Time Setup

1. **Initialize Git** (if not already done):
   ```bash
   git init
   ```

2. **Check what will be committed**:
   ```bash
   git status
   ```
   
   **VERIFY**: `.env` should NOT appear in the list!

3. **Review files to be added**:
   ```bash
   git add -n .
   ```
   
   This does a "dry run" - verify no secrets are included.

4. **Add files**:
   ```bash
   git add .
   ```

5. **Commit**:
   ```bash
   git commit -m "Initial commit: LEX AI with secure configuration"
   ```

6. **Create GitHub repository** (on github.com)

7. **Push to GitHub**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/lex_ai.git
   git branch -M main
   git push -u origin main
   ```

---

## 👥 Team Setup Instructions

When a team member clones the repository:

1. **Clone the repo**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/lex_ai.git
   cd lex_ai
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # OR
   source .venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Copy environment template**:
   ```bash
   cp .env.example .env
   ```

5. **Add their own API key** to `.env`:
   ```env
   GEMINI_API_KEY=their_gemini_api_key_here
   ```

6. **Run the app**:
   ```bash
   streamlit run app.py
   ```

---

## 🔄 Updating API Keys

### If You Need to Change API Keys

The hardcoded key has been removed, so now the process is simple:

1. **Stop the application** (Ctrl+C)

2. **Edit `.env` file**:
   ```env
   GEMINI_API_KEY=your_new_api_key_here
   ```

3. **Restart the application**:
   ```bash
   streamlit run app.py
   ```

4. **Verify** the new key is being used:
   - Check the sidebar settings
   - The config status should show the new key length

### Priority Order

The app reads API keys in this order:

1. **Environment variable** `GEMINI_API_KEY` in `.env` file ✅ RECOMMENDED
2. **Streamlit secrets** in `.streamlit/secrets.toml`
3. **Manual entry** via sidebar UI
4. **None** - user must provide

---

## 🌐 Deployment Options

### Option 1: Streamlit Cloud (Recommended)

1. **Push code to GitHub** (following steps above)

2. **Go to** [Streamlit Cloud](https://streamlit.io/cloud)

3. **Deploy your app**:
   - Connect GitHub repository
   - Select `app.py` as main file

4. **Add secrets** in Streamlit Cloud dashboard:
   - Go to: App Settings → Secrets
   - Add:
     ```toml
     GEMINI_API_KEY = "your_api_key_here"
     APP_PASSWORD = "your_password_here"
     ```

5. **Deploy!** Your app will be live at a `.streamlit.app` URL

### Option 2: Local Server

Just run:
```bash
streamlit run app.py --server.port 8501
```

### Option 3: Docker

Build and run with Docker:
```bash
docker build -t lex-ai .
docker run -p 8501:8501 --env-file .env lex-ai
```

---

## 🧪 Testing After Setup

### Test 1: Configuration Loading

```bash
python
>>> from config import config
>>> api_key = config.get_gemini_api_key()
>>> print(f"API Key loaded: {api_key is not None}")
>>> print(f"API Key length: {len(api_key) if api_key else 0}")
>>> exit()
```

### Test 2: Run the App

```bash
streamlit run app.py
```

Expected behavior:
- App starts without errors
- No hardcoded key warnings
- Settings show "Using API key from .env file"

### Test 3: Make a Query

1. Login with any email
2. Select a lender (e.g., "Mulligan")
3. Ask: "What are the minimum requirements?"
4. Verify response is generated

---

## ⚠️ Common Issues

### Issue: "API Key Required" Error

**Cause**: `.env` file not found or empty

**Fix**:
```bash
# Check if .env exists
ls -la .env  # macOS/Linux
dir .env     # Windows

# Verify content
cat .env     # macOS/Linux
type .env    # Windows

# Should contain:
GEMINI_API_KEY=AIza...
```

### Issue: "Module 'config' not found"

**Cause**: `config.py` not in the same directory as `app.py`

**Fix**:
```bash
# Verify config.py exists
ls config.py

# Run from correct directory
cd c:\Users\ottog\Desktop\lex_ai
streamlit run app.py
```

### Issue: Old API Key Still Being Used

**Cause**: Session state cached the old key

**Fix**:
```bash
# Clear Streamlit cache
streamlit cache clear

# Restart app
streamlit run app.py
```

---

## 🎯 Summary

### What Changed:

1. ✅ **Removed** hardcoded API key from `app.py`
2. ✅ **Created** `config.py` for centralized configuration
3. ✅ **Added** `.env` support with `python-dotenv`
4. ✅ **Created** `.env.example` template
5. ✅ **Updated** `.gitignore` to exclude secrets
6. ✅ **Added** `requirements.txt` with dependencies

### What to Remember:

- 🔐 **NEVER** commit `.env` files
- ✅ **ALWAYS** use `.env.example` as template
- 🔄 **UPDATE** your `.env` when switching API keys
- 📤 **SAFE** to push to GitHub now

---

## 📞 Need Help?

If you encounter issues:

1. Check this guide's troubleshooting section
2. Verify `.env` file is properly formatted
3. Review the main [README.md](README.md)
4. Check configuration status in the app sidebar

---

**You're all set! 🚀 Your LEX application is now secure and ready for GitHub.**

