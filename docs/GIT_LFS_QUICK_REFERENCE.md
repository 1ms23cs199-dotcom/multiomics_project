# Git LFS Quick Reference Guide

**For users having cloning issues or LFS problems**

---

## ⚡ QUICK FIX (2 minutes)

### I see 0-byte files after cloning:

```bash
cd multiomics_project

# Option 1: Simple fix (recommended)
git lfs pull --force

# If that doesn't work, try:
git lfs install --local
git lfs pull

# Verify it worked
ls -lh data/processed/tb_*.csv  # Should show 1-50 MB, not 0 bytes
```

---

## 🔧 INSTALLATION

### First time cloning this repo?

```bash
# Step 1: Install Git LFS (one-time)
git lfs install

# Step 2: Clone normally
git clone https://github.com/<username>/multiomics_project.git
cd multiomics_project

# Step 3: Automatic - LFS files download during clone
# (If not automatic, run: git lfs pull)

# Verify it worked
ls -lh data/processed/
# Should show file sizes like "50M", "1.0M", not "0 bytes"
```

---

## 🐛 TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Files show 0 bytes | `git lfs pull --force` |
| LFS not installed | `git lfs install` |
| Clone is slow | Normal for large files, be patient (~5-10 min) |
| "not a git repository" error | Make sure you're in correct directory: `cd multiomics_project` |
| Still broken after `git lfs pull` | `git lfs install --local` then `git lfs pull` |
| Can't download - GitHub auth issue | `git config --global credential.helper manager` then `git push` (will prompt for auth) |

---

## 📋 DIAGNOSTIC COMMANDS

**Check if Git LFS is working:**
```bash
# Should show LFS is installed
git lfs version

# Should show files tracked by LFS
git lfs ls-files | head

# Check file sizes (look for actual MB values, not 0)
ls -lh data/processed/genomic/*.csv
ls -lh data/processed/tb_*.csv

# Check overall repo size
du -sh .

# Check LFS storage status
git lfs storage  (may not be available, that's ok)
```

---

## 🏠 FOR REPO OWNERS (You)

### Monitor LFS usage:
```bash
# See all LFS files
git lfs ls-files | wc -l

# Check GitHub quota
# Go to: https://github.com/settings/billing/summary
# Look for "GitHub Storage" section

# Estimate LFS usage
git lfs du -s
```

### Something broken? Nuclear option:
```bash
# Remove all local LFS cache and re-download everything
git lfs prune --verify-remote
git lfs pull

# If still broken: fresh clone in temp directory
cd /tmp
git clone https://github.com/<you>/multiomics_project.git test-clone
cd test-clone
ls -lh data/processed/tb_*.csv
```

---

## 📞 IF YOU'RE STILL STUCK

### What to check:

1. **Verify Git LFS is installed:**
   ```bash
   git lfs version
   # Should output version like: git-lfs/3.7.1
   ```

2. **Verify GitHub auth works:**
   ```bash
   git ls-remote https://github.com/<your-username>/multiomics_project.git | head
   # Should list commits/branches
   ```

3. **Check .gitattributes exists:**
   ```bash
   cat .gitattributes
   # Should show LFS rules
   ```

4. **Nuclear option - fresh clone:**
   ```bash
   cd /tmp
   rm -rf multiomics_project
   git lfs install
   git clone https://github.com/<you>/multiomics_project.git
   cd multiomics_project
   ls -lh data/processed/tb_*.csv
   ```

### Still broken? Check:
- Do you have internet connection?
- Is GitHub accessible? (Try: `curl https://github.com -I`)
- Do you have LFS bandwidth available?
- Last resort: Post issue on GitHub with output of: `git lfs version` and file sizes

---

## 📚 MORE INFORMATION

Full documentation available:
- **docs/GIT_LFS_TROUBLESHOOTING.md** — Detailed diagnosis & technical solutions
- **docs/VISUAL_GIT_LFS_GUIDE.md** — Visual before/after explanation
- **docs/INDEX.md** — Navigation guide for all docs

---

## 🎯 SUMMARY

| Action | Command |
|--------|---------|
| Install LFS (first time) | `git lfs install` |
| Clone repo | `git clone https://...` |
| Fix 0-byte files | `git lfs pull --force` |
| Verify files | `ls -lh data/processed/` |
| Check LFS status | `git lfs ls-files` |
| Uninstall LFS (if needed) | `git lfs uninstall` |

---

**Last Updated:** March 18, 2026  
**Status:** Updated after Git LFS .gitattributes fix (Commit b7cae13)
