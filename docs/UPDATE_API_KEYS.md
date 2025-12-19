# 🔑 How to Update API Keys - SIMPLE GUIDE

## ✅ UPDATE IN ONE PLACE

### **File: `shared/config.py`**

**Location:** `C:\PROJETOS\wingtradebot_github\shared\config.py`

## 📝 Steps

1. **Open** `shared/config.py`
2. **Find these lines** (around line 36-39):
   ```python
   SIMPLEFX_API_KEY = os.getenv('SIMPLEFX_API_KEY', '71f8b73762e2437fa95f95b7798eb79e')  # ← UPDATE HERE
   SIMPLEFX_API_SECRET = os.getenv('SIMPLEFX_API_SECRET', '8207dff8-0ff5-4149-9e93-cec503bcc01e')  # ← UPDATE HERE
   ```
3. **Replace the default values** (the long strings) with your actual API keys:
   ```python
   SIMPLEFX_API_KEY = os.getenv('SIMPLEFX_API_KEY', 'YOUR_ACTUAL_API_KEY_HERE')
   SIMPLEFX_API_SECRET = os.getenv('SIMPLEFX_API_SECRET', 'YOUR_ACTUAL_API_SECRET_HERE')
   ```
4. **Save the file**
5. **Restart your services** (FastAPI, Flask, or Django)

## 🎯 That's It!

**One file, one place: `shared/config.py`**

All Python services (FastAPI, Flask, Django) use this file automatically.

## ⚠️ Note About .env File

- If you create a `.env` file, it will override the values in `config.py`
- But you don't need `.env` - just edit `shared/config.py` directly
- `.env` is optional, `shared/config.py` is the main source

## ✅ Verify

After updating, restart your service and check the logs:
- You should see: `[CONFIG] Using API keys from: config.py defaults`
- Or: `[CONFIG] Loaded .env from: ...` (if you use .env)

## 📋 Summary

**To update API keys:**
1. Edit `shared/config.py`
2. Update the default values in the `os.getenv()` calls
3. Save and restart services

**Simple and straightforward!**
