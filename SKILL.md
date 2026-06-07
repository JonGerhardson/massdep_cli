---
name: mass-env-permits
description: >
  Massachusetts environmental public data — search MassDEP air-quality plan approvals & all
  DEP/DCR/MDAR permit records (ePlace), MEPA environmental review filings (ENF/EIR/NPC/Secretary's
  Certificates, eMonitor), the whole EEA Data Portal "DataLake" (permits, facilities, inspections,
  enforcements, asbestos, drinking water, lead & copper in schools, LSP roster, wetland NOI, well
  drilling, NPDES/PFAS), MassDEP Waste Site Cleanup (21E / RTN / reportable releases), CSO/SSO sewage
  discharge notifications, and the Source Registration / Greenhouse Gas filers roster; list and
  download attached PDFs. Triggers on: MEPA, eMonitor, ENF, EIR, EENF, NPC, EEA file number, MassDEP,
  ePlace, EEA Data Portal, DataLake, air quality plan approval, AQ permit, 310 CMR 7.00, waste site
  cleanup, 21E, RTN, reportable release, contaminated site, LSP, CSO, SSO, sewage notification, well
  drilling, drinking water, lead and copper, asbestos, NPDES, PFAS, inspections, enforcements, source
  registration, greenhouse gas filers, MA environmental permit/filing, environmental permitting.
---

# mass-env-permits — Massachusetts environmental permitting & filings

Programmatic, read-only access to six public, no-login MA environmental data backends whose REST/JSON
APIs are hidden behind JavaScript SPAs. Use it to check whether a project/proponent/site has filed
environmental paperwork — e.g. *"has a proposed project at a given address filed a MEPA ENF, a MassDEP
Air Quality Plan Approval, or does the parcel have a 21E waste-site-cleanup history?"* — and to pull the
attached documents.

| Source | What it covers | Access |
|--------|----------------|--------|
| **MassDEP ePlace** | Air-quality plan approvals + all DEP/DCR/MDAR permit applications/authorizations, with documents | REST (no auth) |
| **MEPA eMonitor** | Environmental review filings: ENF, EIR (DEIR/FEIR), NPC, Secretary's Certificates, with attachments | REST (public x-api-key) |
| **EEA Data Portal "DataLake"** | The "Search Data" menu: permits, facilities, inspections, enforcements, asbestos, drinking water, lead & copper (schools), LSP roster, wetland NOI, well drilling, NPDES/PFAS | REST (no auth) |
| **WasteSite (21E)** | MassDEP Waste Site Cleanup / Reportable Releases — RTN search, RAO/tier detail, scanned files | REST (no auth) |
| **CSO / SSO** | Combined/sanitary sewer overflow discharge notifications, with attachments | REST (Referer required) |
| **SR-GHG filers** | Annual Source Registration / Greenhouse Gas filer roster (who must file + class + schedule) | xlsx (bundled) |

The client (`mass_env.py`) is polite by default: generic non-identifying User-Agent, ≤1 req/sec,
retries with backoff. API base URLs and keys are **re-discovered from the live config at runtime**
(meta tag for DataLake; `config.json`/`appconfig.json` for the others — never hard-coded), so the
client survives portal redeploys.

## CLI

```
python mass_env.py <command> [options]            # add -v to log requests
```

| Command | Purpose |
|---------|---------|
| `search-permits` | Search MassDEP permits (`--city --address --applicant --facility --application-id --permit-types --statuses --from --to`) |
| `permit-detail RECORD_ID` | MassDEP record detail + document list (`--checkbox-code` from the search row) |
| `massdep-download DOC_ID` | Download a MassDEP document by `DocId` (`-o file.pdf`) |
| `search-mepa` | Search MEPA projects (`--project-name --eea-no --town --submittal-type --from --to`; `--proponent` see caveat) |
| `mepa-project PROJECT_ID` | MEPA project detail (JSON) |
| `mepa-attachments SUBMITTAL_ID` | List a submittal's attachments (gives `fileServiceId`) |
| `mepa-download FILE_SERVICE_ID` | Download a MEPA attachment (`-o file.pdf`) |
| `sr-ghg` | Query the SR-GHG filer roster (`--town --facility --refresh`) |
| `search-portal RESOURCE` | Search any EEA DataLake dataset (`--town --filter K=V --start --end --sort --order --all`); RESOURCE ∈ permit, facility, inspection, enforcement, asbestos, drinkingWater, leadandcopper, lsp, wire, welldrilling, npdes, searchablesite |
| `portal-detail RESOURCE ID` | DataLake record detail (`--form-type` required for asbestos) |
| `portal-download RESOURCE FILE_ID` / `portal-export RESOURCE` | Download a DataLake doc / export the dataset to `.xlsx` |
| `welldrilling-report WELL_ID` | Download a well-completion report PDF |
| `search-wastesite` | MassDEP Waste Site Cleanup / 21E (`--town --address --rtn --site-name --chemical --site-type`) |
| `wastesite-detail RTN --reg-obj-id` / `wastesite-files RTN` / `wastesite-download` | RTN detail / scanned-doc list / file download |
| `search-cso` | CSO/SSO sewage incidents (`--municipality --outfall --permitee --event-type --from --to`) |
| `cso-detail` / `cso-attachments` / `cso-download` | CSO incident detail / attachment list / download |
| `info` | Show discovered API bases + reference lists |

All list commands take `-f table|csv|json` and `-o OUTPUT`.

## Examples

```bash
# Air-quality permits in a municipality (AQ = on-site combustion / plan approvals)
python mass_env.py search-permits --city Worcester --permit-types AQ

# A specific air permit's documents, then download one
python mass_env.py permit-detail 26CAP-00000-002QR --checkbox-code TR_CPA_FUEL
python mass_env.py massdep-download 1719226 -o plan_approval.pdf

# Has a project filed a MEPA review? (project name / eeaNo / town are the reliable filters)
python mass_env.py search-mepa --eea-no 3247
python mass_env.py search-mepa --town Worcester -f csv -o worcester_mepa.csv
python mass_env.py search-mepa --project-name "Wastewater"

# Download a MEPA filing's attachment
python mass_env.py mepa-attachments <submittal-id>
python mass_env.py mepa-download <file-service-id> -o filing.pdf

# Which facilities in a town must file Source Registration / GHG?
python mass_env.py sr-ghg --town WORCESTER
python mass_env.py sr-ghg --refresh --facility "treatment"   # re-pull the latest xlsx via wget

# Is a parcel a 21E waste-site-cleanup site? (RTN / reportable releases)
python mass_env.py search-wastesite --address "MAIN ST"               # cross-town, free-text
python mass_env.py search-wastesite --town WORCESTER --order-by "notificationDate desc"
python mass_env.py wastesite-detail 2-0053500 --reg-obj-id 674115     # RAO/tier/chemical sections

# EEA DataLake datasets (one engine, 12 resources; --town maps to each one's town key)
python mass_env.py search-portal facility --town Worcester
python mass_env.py search-portal enforcement --town Worcester --all -f csv -o enf.csv
python mass_env.py search-portal npdes --filter "report_type=PFAS Residuals"
python mass_env.py search-portal welldrilling --town Worcester && python mass_env.py welldrilling-report <WellID> -o well.pdf

# Sewage (CSO/SSO) discharge notifications
python mass_env.py search-cso --municipality WORCESTER
python mass_env.py cso-attachments <incidentId> && python mass_env.py cso-download <incidentId> <fileExternalId> -o cso.pdf
```

## Investigative workflow

To check whether a proposed project has filed: (1) `search-mepa --project-name "<name>"` and
`--town <municipality>` for an ENF/EIR/NPC; (2) `search-permits --city <town> --permit-types AQ` (or
`--applicant`/`--facility`) for an Air Quality Plan Approval; (3) `sr-ghg --town <town>` for the
existing-emitter roster. **"Nothing filed" is a valid, informative result** — a genuine MEPA no-match
returns `totalRecords 0`. Cross-link the sources via `eeaNo` (MEPA) ↔ `MepaProjectNumber` (ePlace) and
`AQ ID#` (SR-GHG) ↔ `FacilityID` (ePlace).

## Key concepts

- **MassDEP authorization types** (`--permit-types`, comma list of AccelaType codes):
  DEP: `AQ` (air quality), `DW`, `HW`, `SW`, `TUR`, `WM`, `WW`, `WP`, `LES`; DCR: `SUP`, `CAP`;
  MDAR: `Pesticide`, `Plant Industries`. **Air permits = `AQ`**; AQ02**F** = a *Fuel/combustion*
  plan-approval application (emergency/stationary engines, turbines under 310 CMR 7.00/7.02).
- **MassDEP statuses** (`--statuses`): `In Review`, `Public Comment Pending`, `Approved`, `Denied`,
  `Withdrawn`.
- **MEPA submittal types**: `ENF` (Environmental Notification Form), `EENF`, `DEIR`/`FEIR`/`EIR`,
  `NPC` (Notice of Project Change), `* Cert` (Secretary's Certificate), `EDR`. `eeaNo` = the public
  EEA/MEPA file number.
- **MEPA `--proponent` is unreliable**: the public API's `ProponentName` filter is non-functional
  (proponent names live in a separate contacts system). A proponent query returns the global total
  with an empty list; the CLI prints a warning. Search by `--project-name` / `--town` / `--eea-no`
  instead.
- **Detail params**: MassDEP `permit-detail` needs the `RecordId` **and** the `CheckBoxCode` from the
  search row. MEPA downloads need the `fileServiceId` (short token), not the `attachmentId` GUID.

## Architecture notes

- MassDEP ePlace API base `https://eplace.eea.mass.gov/EEAPublicAppAPI` (no auth). Search is a single
  `POST /api/Search/Applications`; there is no server pagination (>200 rows → "refine search").
- MEPA is an AWS API Gateway requiring a **public** `x-api-key` read from the SPA's
  `assets/config/config.json`. Attachment download is a 3-step token dance ending at a presigned S3
  URL that must be fetched *without* auth headers.
- SR-GHG: mass.gov bot-blocks curl/requests; the client uses **wget** to refresh, else the bundled
  `data/sr-ghg-filers-list.xlsx` snapshot.
- **EEA DataLake** (`…/EEA/DataLake/V1.0/DataLakeAPI/`, no auth): one engine serves 12 datasets, all
  `{Items, TotalCount}` with `_start`/`_end` offset paging. Base is read from a `<meta>` tag in the
  ~5.8 MB Portal shell (client streams only the head). **Town-key gotcha:** each resource has its own
  town param (`Town` / `TownName` / numeric `TownId` / `citytown_of_sample`); a wrong key is *silently
  ignored* and returns the global total — the client hard-codes the mapping (`DATALAKE_RESOURCES`) and
  resolves `wire`'s numeric `TownId` via the MEPA postal lookup. `--all` dedupes on the id column
  (WIRE/Well-Drilling overlap the page boundary; LSP uses inclusive ends).
- **WasteSite (21E)** (`…/dep/WasteSiteAPI/`): search returns a *top-level array*; total is on every
  row as string `totalCount`. **CSO** (`…/dep/CSOAPI/api/`): a `Referer` header is a hard server gate
  (HTTP 500 without it). Both discover their base from `appconfig.json` like MEPA.
- Full endpoint/field documentation incl. the per-resource registry: **`references/API_NOTES.md`**
  (see the 2026-06-06 ADDENDUM).

## Dependencies

`requests` (APIs), `openpyxl` (SR-GHG xlsx), and `wget` on PATH (SR-GHG refresh). `pandas` optional
for analysis of the JSON/CSV output.

## Relationship to other skills

Same MA-government public-data family as **commbuys** (procurement) and **govqa** (public-records
requests). When a MEPA/MassDEP record references a contractor or contract, COMMBUYS can cross-reference
the vendor; for documents not online, file a request via govqa.

## Source

Client + CLI: `mass_env.py` (in this skill dir). Endpoint reference: `references/API_NOTES.md`.
Bundled data: `data/sr-ghg-filers-list.xlsx`.
