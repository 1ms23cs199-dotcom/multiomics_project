
# Human Serum Proteomics — Placeholder Status

## Current Status
- Using SYNTHETIC data for Phase 3-5 testing
- Real data required before model deployment

## How to Replace

1. **Find TB serum studies in ProteomeXchange:**
   https://proteomecentral.proteomexchange.org/cgi/GetDatasetList.cgi
   
   Search filters:
   - Species: Homo sapiens
   - Disease: tuberculosis
   - Sample type: serum or plasma
   
2. **Download the proteomics expression matrix:**
   - Format: rows = samples, columns = proteins
   - Units: log2 intensity, intensity, or abundance ratio
   
3. **Replace serum_proteomics_synthetic.csv:**
   ```bash
   # After downloading real data:
   mv serum_proteomics_real.csv data/processed/proteomic/serum_proteomics.csv
   ```

4. **Expected format:**
   ```
   sample_id,CXCL10,CRP,SAA1,IL6,TNF,IL1B,IL8,IFIT1,IFIT3,OAS1,...
   P0001,5.23,6.12,7.45,4.56,5.89,...
   P0002,4.89,5.67,6.78,5.12,6.34,...
   ```

5. **Recommended TB proteomics studies:**
   - Studies with n>100 TB patient samples
   - Matched healthy controls
   - Serum or plasma proteomics (not tissue)
   - Published 2018+ (more comprehensive MS methods)

## Known TB Serum Biomarkers
- CXCL10: Chemokine, robust TB marker
- CRP, SAA1: Acute phase proteins
- IL6, TNF: Systemic inflammation
- IFIT1, IFIT3: Interferon signature

## Alternative
If real serum data unavailable, consider:
- Use TB-specific mycobacterial proteins only (current data)
- Keep for drug discovery (Phase 7)
- Skip serum proteomics from patient classifier
