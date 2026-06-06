# Validation log — mass-env-permits

Run against the live portals via `mass_env.py` (generic UA, ≤1 req/s). Examples below use large,
public, unrelated subjects purely to exercise the client.

## Endpoint/config discovery (`info`)
- ePlace API base re-read from `appConfig.json` ✔
- MEPA API base, attachment API, and postal API re-read from MEPA `config.json` ✔
  (no keys hard-coded; they resolve at runtime)

## MassDEP ePlace
- `search-permits --city Worcester --permit-types AQ` → **37 records** (e.g. ABBVIE BIORESEARCH
  CENTER INC AQ01P/AQ02F, FURNITURE PLUS AQ34, …). ✔
- `permit-detail 26CAP-00000-002QR --checkbox-code TR_CPA_FUEL` → **14 documents** listed with
  `DocId` / `Name` / `Type` / `Category`. ✔
- `massdep-download 1719226` → **8,428,092-byte PDF** ("Non-Major Comprehensive Plan Approval…",
  `%PDF-1.4`). ✔

## MEPA eMonitor
- `search-mepa --eea-no 3247` → 3 project records (Boston Logan International Airport family). ✔
- `search-mepa --town Worcester` → 236 projects on page 1 (ENF/EIR/NPC). ✔
- `mepa-attachments <submittal-id>` → attachment list with `fileServiceId`. ✔
- `mepa-download <file-service-id>` → **4,651,198-byte PDF** (`%PDF-1.7`) via the 3-step chain
  (tokens → FileService 302 → presigned S3, fetched without auth headers). ✔

## SR-GHG roster
- `sr-ghg --town WORCESTER` → **38 filers** (facility, MassDEP region, current class, filing
  schedule). Cross-validates the permit search (overlapping facilities). ✔
- `sr-ghg --refresh` re-downloads the xlsx via wget (301 → current-year file). ✔

## "Nothing filed" behavior
- A genuine MEPA no-match returns `totalRecords 0` (e.g. an unused project-name string → 0 projects),
  which is how the client distinguishes a real negative from the ignored-`ProponentName`-filter case
  (that one returns the global total with an empty list, and the CLI prints a warning).

This confirms search, detail, document listing, and document download work end-to-end for all three
sources.
