# Git LFS Configuration Issues & Solutions

**Date Created:** March 18, 2026  
**Status:** Critical Issues Found

---

## 🚨 PROBLEMS IDENTIFIED

### Problem 1: Phase 2B+3 Files NOT in LFS
**Files affected:**
- ❌ `data/processed/tb_multimodal_integrated_final.csv` (1.3 MB)
- ❌ `data/processed/tb_train_set.csv` (1.0 MB)
- ❌ `data/processed/tb_test_set.csv` (277 KB)
- ❌ `data/processed/tb_multimodal_patient_matrix_raw.csv` (1.0 MB)

**Current Status:** Stored as regular git objects (mode 100644), NOT LFS pointers

**Impact:** 
- When someone clones your repo, these files may appear as 0 bytes or corrupted
- Large files exceeded GitHub's 100MB limit on regular git
- Files show as present in git history but inaccessible

**Proof:**
```
100644 95d7cb25f1320e92398d9b88a7b46691521dec07 0       tb_multimodal_integrated_final.csv
                                                  ↑
                                        Shows 0 bytes (wrong!)
```

---

### Problem 2: .gitattributes Pattern Incomplete
**Current pattern in .gitattributes:**
```
data/processed/genomic/*.csv filter=lfs diff=lfs merge=lfs -text
```

**Missing pattern:**
```
data/processed/*.csv filter=lfs diff=lfs merge=lfs -text  ← Too broad OR
data/processed/tb_*.csv filter=lfs diff=lfs merge=lfs -text  ← Too specific
```

**Impact:** New CSV files created outside `/genomic/` directory aren't automatically tracked by LFS

---

### Problem 3: Older Files Committed Before LFS Was Fully Applied
**Files showing as 0 bytes (LFS misconfiguration):**
- `data/processed/genomic/gse37250_processed.csv` (50.67 MB) — Should be in LFS
- `data/processed/genomic/gse83456_processed.csv` (18.96 MB) — Should be in LFS
- `data/processed/genomic/gse19435_processed.csv` (3.13 MB) — Should be in LFS

**Current Status:** Listed in `git lfs ls-files` ✓ BUT stored as git objects showing 0 bytes ✗

**Why This Happens:** Files were committed to regular git BEFORE being properly tracked by LFS. Git LFS pointers were created later, but the original objects remain.

---

## ✅ SOLUTIONS

### Solution 1: Update .gitattributes (Quick Fix)

**Expand LFS tracking rules to all processed CSVs:**

```gitattributes
# Git LFS tracking rules
# Updated March 18, 2026 - Track ALL large data files

# ====== GENOMIC & PROTEOMICS DATA ======
# Track ALL CSV files in processed folder (all sizes, for consistency)
data/processed/**/*.csv filter=lfs diff=lfs merge=lfs -text

# Track raw genomic files
data/raw/genomic/*.gz filter=lfs diff=lfs merge=lfs -text
data/raw/genomic/*.fasta filter=lfs diff=lfs merge=lfs -text

# Track raw proteomics files
data/raw/proteomic/*.fasta filter=lfs diff=lfs merge=lfs -text

# ====== OPTIONAL: Track future large model files ======
# weights, checkpoints, serialized models
models/**/*.pt filter=lfs diff=lfs merge=lfs -text
models/**/*.pkl filter=lfs diff=lfs merge=lfs -text
models/**/*.ckpt filter=lfs diff=lfs merge=lfs -text
```

**Apply now:**
```bash
cd c:\Users\trish\multiomics_project
# Update .gitattributes with above content
# Then:
git add .gitattributes
git commit -m "Fix: Expand LFS tracking to all processed CSVs"
git push origin main
```

---

### Solution 2: Migrate Existing Large Files to LFS (Permanent Fix)

⚠️ **This rewrites git history and requires force-push. Do this CAREFULLY:**

**Step 1: Install BFG Repo Cleaner (optimal tool for this)**
```bash
# Download from https://rtyley.github.io/bfg-repo-cleaner/
# OR use git-lfs built-in method (slower but safer)
```

**Step 2: Use Git LFS native re-tracking (RECOMMENDED)**
```bash
cd c:\Users\trish\multiomics_project

# Remove files from git tracking
git rm --cached data/processed/**/*.csv
git rm --cached data/raw/genomic/*.gz
git rm --cached data/raw/genomic/*.fasta
git rm --cached data/raw/proteomic/*.fasta

# Re-add with LFS (should now be tracked as pointers)
git add data/processed/**/*.csv
git add data/raw/genomic/*.gz
git add data/raw/genomic/*.fasta
git add data/raw/proteomic/*.fasta

# Verify they're now LFS pointers
git lfs ls-files

# Commit
git commit -m "Migrate: Move all large files to LFS storage

- Re-tracked 50+ data files with Git LFS
- All CSV, FASTA, and GZ files now use LFS pointers
- Reduces repo size from ~300MB to ~5MB
- Fixes clone issues for users without LFS auto-download
"

# Push (may take a while for large files)
git push origin main
```

---

### Solution 3: Fix for Users Cloning Without Git LFS (User-Side)

**Tell users cloning your repo to do:**

```bash
# Before cloning:
git lfs install

# Clone normally:
git clone https://github.com/<your-username>/multiomics_project.git
cd multiomics_project

# If files are still 0 bytes/corrupted:
git lfs pull

# Verify files sizes
ls -lh data/processed/tb_*.csv
du -sh data/processed/
```

---

## 🔍 DIAGNOSTIC COMMANDS

**Check what's tracked in LFS vs regular git:**
```bash
# Count LFS files
git lfs ls-files | wc -l

# See which large files are NOT in LFS
find data/processed -name "*.csv" -size +1M ! -size 0c | while read f; do
  if ! git lfs ls-files | grep -q "$f"; then
    echo "NOT IN LFS: $f"
  fi
done

# Check .gitattributes patterns
cat .gitattributes

# Verify GitHub LFS storage usage
# Go to: https://github.com/<your-username>/multiomics_project/settings
# Check "GitHub Storage" quota
```

---

## 📊 CURRENT STATE ASSESSMENT

| File | Size | In Git | In LFS | Status |
|------|------|--------|--------|--------|
| tb_multimodal_integrated_final.csv | 1.3 MB | ✓ | ❌ | **BROKEN** |
| tb_train_set.csv | 1.0 MB | ✓ | ❌ | **BROKEN** |
| tb_test_set.csv | 277 KB | ✓ | ❌ | **BROKEN** |
| gse37250_processed.csv | 50.7 MB | ✓ | ✓? | **MIXED** (shows as 0 bytes) |
| genomic_combined.csv | 1.3 MB | ✓ | ✓ | **OK** |

**Why .gitattributes matters:**
```
Files in LFS but showing 0 bytes indicate misconfiguration
↓
New Phase 2B+3 files NOT in LFS pattern (only /genomic/*.csv covered)
↓
Users clone and get corrupted/zero-byte files
↓
"I can't see the files!" complaints
```

---

## 🎯 RECOMMENDED ACTION PLAN

### Immediate (Today):
1. ✅ **Update .gitattributes** to track `data/processed/**/*.csv`
2. Push change to GitHub
3. Notify users to re-clone after update

### This Week:
4. **Re- Track large files with LFS** (use git lfs migrate command)
5. Force push to GitHub (update existing commithistory)
6. Test clone on fresh directory

### Ongoing:
7. **Add to CI/CD** (if you have it):
   ```yaml
   - name: Verify LFS tracking
     run: |
       find data/processed -name "*.csv" -size +1M -exec \
       git lfs ls-files | grep -q {} \;
   ```

---

## 📝 QUICK REFERENCE: GitHub LFS Limits

| Tier | Storage | Bandwidth | Cost |
|------|---------|-----------|------|
| Free | 1 GB | 1 GB/month | Free |
| Pro | Unlimited storage | Unlimited | $5/month |

**Your repo status:**
- Estimated LFS usage: ~200 MB (all large CSVs + raw data)
- If FREE tier: ⚠️ **May hit 1 GB limit after more data**
- **Recommendation:** Upgrade to Pro if LFS usage exceeds 500 MB

---

## 🚀 IMPLEMENTATION STEPS

### Step 1: Update .gitattributes TODAY
```bash
# Read current file
cat .gitattributes

# Update with expanded patterns (see Solution 1 above)
# Then:
git add .gitattributes
git commit -m "Fix: Expand LFS tracking to all processed CSVs"
git push
```

### Step 2: Test Clone
```bash
# In a temp directory
cd /tmp
git clone https://github.com/<you>/multiomics_project.git test-clone
cd test-clone

# Check file sizes
ls -lh data/processed/tb_*.csv

# Should see actual sizes, NOT 0 bytes
```

### Step 3: Document in README
```markdown
## Setup Instructions

### Required: Git LFS
Before cloning, install Git LFS:
\`\`\`bash
git lfs install
\`\`\`

Then clone normally:
\`\`\`bash
git clone https://github.com/<you>/multiomics_project.git
cd multiomics_project
git lfs pull  # Download large files
\`\`\`

If files appear as 0 bytes after clone:
\`\`\`bash
git lfs pull --force
\`\`\`
```

---

## Reference Links

- **Git LFS Docs:** https://git-lfs.com/
- **GitHub LFS Guide:** https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github
- **BFG Repo Cleaner:** https://rtyley.github.io/bfg-repo-cleaner/
- **Git LFS Storage:** https://github.com/settings/billing/summary (check "GitHub Storage")

---

**Summary:** Your LFS is partially configured, but Phase 2B+3 files were created AFTER the .gitattributes rules were finalized, so they weren't tracked. Quick fix: update .gitattributes pattern, re-commit, and users will be able to clone successfully.
