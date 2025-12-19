# 🔑 Where to Update API Keys - OFFICIAL GUIDE

## ✅ ANSWER: Update in ONE Place Only

### **`.env` file at project root**

```
C:\PROJETOS\wingtradebot_github\.env
```

## 📝 How It Works

### Current Setup:
1. **`.env` file** (if exists) → **READ FIRST** ← **UPDATE HERE**
2. **Hardcoded defaults** (in config files) → **FALLBACK ONLY**

### Priority:
```
.env file → Highest Priority (if exists)
Defaults   → Lowest Priority (only if .env missing)
```

## 🎯 Steps to Update

### 1. Create `.env` file (if doesn't exist)
```bash
# At project root, create .env file:
copy .env.example .env
```

### 2. Edit `.env` file
Open `C:\PROJETOS\wingtradebot_github\.env` and update:
```env
SIMPLEFX_API_KEY=your_new_api_key
SIMPLEFX_API_SECRET=your_new_api_secret
SIMPLEFX_API_KEY2=your_secondary_key (optional)
SIMPLEFX_API_SECRET2=your_secondary_secret (optional)
```

### 3. Restart services
After updating, restart FastAPI/Flask/Django

## 📋 Where Keys Are Currently Defined

| Location | Purpose | Should Edit? |
|---------|---------|--------------|
| **`.env`** (project root) | **Official source** | ✅ **YES - UPDATE HERE** |
| `shared/config.py` | Python config (reads .env, has defaults) | ❌ No - Don't edit defaults |
| `src/config.ts` | TypeScript config (deprecated) | ❌ No - Deprecated |

## ⚠️ Important

- **`.env` is in `.gitignore`** - Safe to store secrets
- **Don't edit hardcoded defaults** - Always use `.env`
- **Both Python and TypeScript** read from same `.env` file
- **Single source of truth** = `.env` file

## ✅ Verification

Check which keys are being used:
```bash
scripts\setup\CHECK_API_KEYS.bat
```

## 🎯 Summary

**Official place to update API keys:**
```
C:\PROJETOS\wingtradebot_github\.env
```

**That's it! One file, one place, all services use it.**

