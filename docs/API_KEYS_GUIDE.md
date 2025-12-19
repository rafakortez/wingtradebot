# 🔑 API Keys - Official Update Guide

## ✅ SINGLE SOURCE OF TRUTH

**Update API keys in ONE place only: `.env` file at project root**

```
wingtradebot_github/
  └── .env  ← UPDATE HERE (create if doesn't exist)
```

## 📝 How to Update

### Step 1: Create/Edit `.env` file

If `.env` doesn't exist, create it at the project root:
```bash
# Copy from example
copy .env.example .env
```

### Step 2: Edit `.env` file

Open `.env` and update these values:
```env
SIMPLEFX_API_KEY=your_actual_api_key
SIMPLEFX_API_SECRET=your_actual_api_secret
SIMPLEFX_API_KEY2=your_secondary_key (optional)
SIMPLEFX_API_SECRET2=your_secondary_secret (optional)
```

### Step 3: Restart Services

After updating, restart your services:
```bash
# Stop current services (Ctrl+C)
# Then restart:
scripts\setup\START_FLASK.bat
# or
scripts\setup\START_DJANGO.bat
```

## 🔍 Current Configuration

### Where API Keys Are Read From:

1. **`.env` file** (if exists) ← **OFFICIAL - UPDATE HERE**
   - Location: Project root (`wingtradebot_github/.env`)
   - Used by: Both Python and TypeScript services
   - Priority: **HIGHEST** (overrides defaults)

2. **Hardcoded defaults** (fallback only)
   - `shared/config.py` - Python defaults (same as config.ts)
   - `src/config.ts` - TypeScript defaults (deprecated)
   - Priority: **LOWEST** (only used if .env doesn't exist)

### Priority Order:
```
1. .env file (if exists) ← UPDATE HERE
2. Hardcoded defaults (fallback)
```

## ⚠️ Important Notes

1. **`.env` is in `.gitignore`** ✅
   - Your secrets won't be committed to git
   - Safe to store API keys here

2. **Never edit hardcoded defaults** ❌
   - Don't edit `shared/config.py` defaults
   - Don't edit `src/config.ts` defaults
   - Always update `.env` instead

3. **Both services use same `.env`** ✅
   - Python services read from `.env`
   - TypeScript services read from `.env` (if running)
   - Single source of truth

## ✅ Verify Your Keys

Check which keys are being used:
```bash
scripts\setup\CHECK_API_KEYS.bat
```

This will show:
- Which keys are configured (masked for security)
- Whether `.env` file exists
- Which source is being used

## 📋 File Locations Reference

| File | Purpose | Should Edit? |
|------|---------|--------------|
| `.env` | **Official API keys** | ✅ **YES - UPDATE HERE** |
| `.env.example` | Template/example | ❌ No (reference only) |
| `shared/config.py` | Python config (reads .env) | ❌ No (has defaults, reads .env) |
| `src/config.ts` | TypeScript config (deprecated) | ❌ No (deprecated) |

## 🎯 Summary

**To update API keys:**
1. Edit `.env` file at project root
2. Save the file
3. Restart services

**That's it!** All services will automatically use the new keys from `.env`.

