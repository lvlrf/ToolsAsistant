# Changelog

All notable changes to Backhaul Premium Bulk Config Generator.

---

## [2.0.0] - 2026-01-06

### 🎉 Major Changes

#### Interactive Generator
- ✅ **Interactive menu system** - Choose what to generate
- ✅ **Integrated dashboard generation** - No separate scripts
- ✅ **View state** option - Check current ports, tokens, subnets
- ✅ **Input validation** - Proper yes/no prompts with validation

#### Dashboard Improvements
- ✅ **Auto IP detection** - Reads IPs from config.json
- ✅ **Direct web panel opening** - Opens in new tab automatically
- ✅ **English interface** - Clean, professional English UI
- ✅ **Vazir font** - Better Persian support via CDN
- ✅ **Transport guide** - Built-in guide accessible from header and footer
- ✅ **Server-specific actions** - Actions use actual server names
- ✅ **Extract & Chmod** - Quick action for binary setup
- ✅ **Start/Stop buttons** - Individual service control

#### Code Quality
- ✅ **Simplified file structure** - Removed redundant scripts
- ✅ **Better error handling** - Clear error messages
- ✅ **Input validation** - Supports "all", ["all"], and specific transports
- ✅ **Code comments** - Better documented

### 🗑️ Removed

- ❌ `update-state.py` - Integrated into generator
- ❌ `generate-dashboard.py` - Integrated into generator
- ❌ Stats display in dashboard - Simplified UI

### 🐛 Bug Fixes

- ✅ Fixed `["all"]` transport handling
- ✅ Fixed double `.service` extension bug
- ✅ Fixed terminal encoding issues (English messages)
- ✅ Fixed yes/no prompt validation

### 📝 Documentation

- ✅ Updated README with v2.0 features
- ✅ Added CHANGELOG
- ✅ Updated QUICKSTART guide

---

## [1.0.0] - 2026-01-05

### Initial Release

- ✅ Support for 13 transport types
- ✅ Three optimization profiles (speed, stable, balanced)
- ✅ Mux versions v1 and v2
- ✅ TUN transport support
- ✅ Service management scripts
- ✅ Optimization scripts for Iran and Kharej
- ✅ State management
- ✅ Token generation
- ✅ Port allocation
- ✅ Subnet management
- ✅ Basic dashboard
- ✅ Comprehensive documentation

---

## Migration Guide: v1.0 → v2.0

### What Changed

1. **File Structure:**
   ```
   v1.0:
   - generator.py
   - generate-dashboard.py
   - update-state.py
   
   v2.0:
   - generator.py (all-in-one)
   ```

2. **Usage:**
   ```bash
   # v1.0
   python3 generator.py
   python3 generate-dashboard.py
   python3 update-state.py summary
   
   # v2.0
   python3 generator.py
   # Then choose from menu: [1-5]
   ```

3. **Dashboard:**
   - v1.0: Required copying SERVER_IP manually
   - v2.0: Auto-detects IPs from config.json

### Breaking Changes

None! Your existing config.json and state.json files work perfectly.

### Recommendations

1. Delete v1.0 files: `update-state.py`, `generate-dashboard.py`
2. Use new `generator.py` with interactive menu
3. Regenerate dashboard with option [2] or [4]

---

**Note:** This project follows [Semantic Versioning](https://semver.org/).
