# mass-env-permits

**Search Massachusetts environmental data and pull source documents from the command line.**

Massachusetts publishes a lot of environmental data through public, no-login websites. The trouble is
they're single-page JavaScript apps: easy to click through one record at a time, impossible to query
in bulk. This tool talks directly to the JSON APIs behind those apps, so you can search by town,
address, applicant, permit type, file/RTN number, or date — across permitting, environmental review,
compliance & enforcement, drinking water, wetlands, waste-site cleanups, sewage overflows, and more —
and download the attached documents.

It works as a plain Python CLI, and as a skill that a coding agent can drive for you.

---

## What it covers

Six portals, ~17 distinct datasets:

| Source | What's in it | Good for |
|--------|--------------|----------|
| **MassDEP ePlace** | Air-quality plan approvals and every other DEP / DCR / MDAR permit application & authorization, with attached documents | "Did someone apply for an air permit / wetlands permit / etc. here?" + the supporting PDFs |
| **MEPA eMonitor** | Environmental review filings — Environmental Notification Forms (ENF), Environmental Impact Reports (DEIR/FEIR), Notices of Project Change (NPC), Secretary's Certificates | "Has this project gone through state environmental review?" + the filed documents |
| **EEA DataLake** | One engine, **12 datasets**: permits, facilities, inspections, **enforcement** actions, asbestos notifications, drinking-water & lead/copper sampling, Licensed Site Professionals, wetlands Notices of Intent, well-drilling, NPDES sampling, and searchable waste sites | Bulk compliance/enforcement history, sampling results, well logs — by town, exportable to Excel |
| **CSO / SSO notifications** | Combined- and sanitary-sewer overflow discharge incident reports (who discharged, where, when, into which waterbody) | "Has there been a sewage discharge here?" + the incident PDFs |
| **Waste Site Cleanup (21E)** | Reportable releases / contaminated-site cleanups by Release Tracking Number (RTN) — chemicals, RAO/tier status, Licensed Site Professional, documents | "Is this parcel a contaminated-site cleanup?" + the filed reports |
| **SR-GHG filers list** | Annual roster of facilities required to file Source Registration / Greenhouse-Gas reports, with air-quality classification and filing schedule | "Which facilities in this town are regulated air-emission sources?" |

Everything except the SR-GHG list is a live REST API. The SR-GHG list is a spreadsheet MassDEP
publishes; a recent snapshot is bundled in `data/` and you can refresh it on demand.

---

## Install

Requires **Python 3.8+** and `wget` on your PATH.

```bash
pip install requests openpyxl
# pandas is optional, only if you want to crunch the JSON/CSV output
```

No accounts, no API keys to obtain — everything here is public record.

---

## Quick start

```bash
# Air-quality permits in a city (AQ covers plan approvals incl. on-site combustion)
python mass_env.py search-permits --city Worcester --permit-types AQ

# Look at one permit's documents, then download one
python mass_env.py permit-detail 26CAP-00000-002QR --checkbox-code TR_CPA_FUEL
python mass_env.py massdep-download 1719226 -o plan_approval.pdf

# Find a MEPA review filing by file number, town, or name; grab an attachment
python mass_env.py search-mepa --eea-no 3247
python mass_env.py search-mepa --town Worcester -f csv -o worcester.csv
python mass_env.py mepa-attachments <submittal-id>
python mass_env.py mepa-download <file-service-id> -o filing.pdf

# EEA DataLake — pick a dataset; --town maps to that dataset's town key
python mass_env.py search-portal facility --town Worcester
python mass_env.py search-portal enforcement --town Worcester --all -f csv -o enforcement.csv
python mass_env.py portal-download enforcement <file-id> -o order.pdf
python mass_env.py welldrilling-report <well-id> -o well.pdf

# Sewage (CSO/SSO) discharge notifications
python mass_env.py search-cso --municipality WORCESTER
python mass_env.py cso-download <incident-id> <file-external-id> -o cso.pdf

# Waste-site cleanups / reportable releases (21E / RTN)
python mass_env.py search-wastesite --town WORCESTER
python mass_env.py wastesite-detail 2-0053500 --reg-obj-id 674115

# Which facilities in a town must file Source Registration / GHG?
python mass_env.py sr-ghg --town WORCESTER
python mass_env.py sr-ghg --refresh        # pull the latest spreadsheet first

# Show the API endpoints the tool discovered, plus reference lists
python mass_env.py info
```

Every list command accepts `-f table|csv|json` and `-o FILE`. Add `-v` to see the requests as they go out.

---

## Commands

**MassDEP ePlace (permits)**

| Command | What it does |
|---------|--------------|
| `search-permits` | Search permits. Filters: `--city --address --zip --applicant --facility --application-id --permit-types --statuses --from --to` |
| `permit-detail RECORD_ID` | Full record + document list. Needs `--checkbox-code` (it's in the search results) |
| `massdep-download DOC_ID` | Download a document by its `DocId` |

**MEPA eMonitor (environmental review)**

| Command | What it does |
|---------|--------------|
| `search-mepa` | Search projects. Filters: `--project-name --eea-no --town --submittal-type --from --to` |
| `mepa-project PROJECT_ID` | Full project detail (JSON) |
| `mepa-attachments SUBMITTAL_ID` | List a submittal's attachments (gives you the `fileServiceId`) |
| `mepa-download FILE_SERVICE_ID` | Download an attachment |

**EEA DataLake (12 datasets)**

| Command | What it does |
|---------|--------------|
| `search-portal RESOURCE` | Search a dataset (`facility`, `permit`, `inspection`, `enforcement`, `asbestos`, `drinkingWater`, `leadandcopper`, `lsp`, `wire`, `welldrilling`, `npdes`, `searchablesite`). `--town`, repeatable `--filter k=v`, `--all` to auto-paginate |
| `portal-detail RESOURCE ID` | Record detail (JSON; `asbestos` needs `--form-type`) |
| `portal-download RESOURCE FILE_ID` | Download a document by `fileId` |
| `portal-export RESOURCE` | Export the dataset to `.xlsx` |
| `welldrilling-report WELL_ID` | Download a well-completion report PDF |

**CSO / SSO sewage notifications**

| Command | What it does |
|---------|--------------|
| `search-cso` | Search incidents. Filters: `--municipality --permitee --outfall --waterbody --event-type --from --to` |
| `cso-detail INCIDENT_ID` | Incident detail |
| `cso-attachments INCIDENT_ID` | List an incident's attachments |
| `cso-download INCIDENT_ID FILE_EXTERNAL_ID` | Download an attachment |

**Waste Site Cleanup (21E / RTN)**

| Command | What it does |
|---------|--------------|
| `search-wastesite` | Search sites. Filters: `--town --address --rtn --site-name --lsp --chemical --zip --site-type --regulatory-status` |
| `wastesite-detail RTN` | Site detail (needs `--reg-obj-id`): chemicals, RAO/tier, LSP sections |
| `wastesite-files RTN` | List scanned / electronically-filed documents |
| `wastesite-download PATH` | Download a file by its path |
| `wastesite-export` | Export search results to `.xlsx` |

**Other**

| Command | What it does |
|---------|--------------|
| `sr-ghg` | Query the SR-GHG filer roster. Filters: `--town --facility`; `--refresh` to re-download |
| `info` | Show resolved API base URLs and reference lists |

### A few field notes
- **Permit types** (`--permit-types`, comma-separated): `AQ` (air quality), `DW` (drinking water),
  `HW` (hazardous waste), `SW` (solid waste), `WW` (wetlands & waterways), `WP` (water pollution),
  `WM`, `TUR`, `LES`, `SUP`, `CAP`, `Pesticide`, `Plant Industries`. Air permits are `AQ`.
- **Statuses** (`--statuses`): `In Review`, `Public Comment Pending`, `Approved`, `Denied`, `Withdrawn`.
- **Dates** are `YYYY-MM-DD`.
- **`eeaNo`** is the public MEPA/EEA file number. It's the same identifier MassDEP records call
  `MepaProjectNumber`, so you can pivot between the two systems.

---

## Tying the sources together

The datasets share keys, so you can follow a site or project across portals:

- MEPA `eeaNo` ⇄ MassDEP ePlace `MepaProjectNumber`
- SR-GHG `AQ ID#` ⇄ ePlace / DataLake `FacilityID`
- A town + address ties together permits, inspections, enforcement, waste-site RTNs, and sewage outfalls

A typical "what's going on at this site?" sweep: MEPA for a review filing, ePlace for permits,
DataLake `enforcement`/`inspection` for compliance history, `search-wastesite` for a cleanup RTN,
`search-cso` for discharges, and the SR-GHG roster for emitter status. **Finding nothing is a real
answer** — a genuine MEPA no-match returns a total of `0`.

---

## How it works (and why it keeps working)

- **No hardcoded secrets.** The portals' API base URLs (and MEPA's public API key) ship inside each
  web app's runtime config or a `<meta>` tag. The tool re-reads those at runtime, so when the state
  redeploys and the URLs/keys change, this keeps working without edits.
- **Polite by default.** One request per second, a generic User-Agent, and automatic retries with
  backoff. Please keep it that way — this hits government servers.
- **Read-only.** It only searches and downloads. It never submits, edits, or logs into anything.

Endpoint-level documentation lives in [`references/API_NOTES.md`](references/API_NOTES.md), and a
run-through proving each piece works is in [`references/VALIDATION.md`](references/VALIDATION.md).

---

## Known limitations / gotchas

- **No proponent search in MEPA.** The MEPA API exposes a `ProponentName` filter, but it doesn't
  actually work — developer/proponent names live in a separate contacts system. Search by project
  name, town, or `eeaNo` instead. (The CLI warns you when a filter was silently ignored.)
- **DataLake town-key landmine.** Each dataset uses a *different* town parameter (`Town` / `TownName`
  / numeric `TownId` / `citytown_of_sample`); a wrong one is silently ignored and you get the global
  total. The client maps each dataset's key for you — just use `--town`.
- **`npdes` is sparse.** It's keyed on the sampling location's town and returns 0 for many towns.
- **MassDEP ePlace search isn't paginated.** A very broad search (>200 results) gets truncated; narrow
  it with a town, date range, or permit type. (The DataLake datasets *do* paginate — use `--all`.)
- **Two "waste site" views.** The DataLake `searchablesite` resource and the dedicated
  `search-wastesite` viewer cover the same RTNs; `search-wastesite` is richer (chemicals, RAO/tier,
  file lists), so prefer it.
- **The SR-GHG list is a snapshot**, not live. The bundled copy is dated **Mar 6, 2026**; `--refresh`
  pulls the current file. It's a *roster* (who must file + class/schedule), not emissions totals — and
  it only lists established facilities, so it won't show a not-yet-built project.
- **mass.gov blocks some download tools.** That's why the SR-GHG refresh uses `wget`.

---

## What's in here

```
mass-env-permits/
├── README.md                      # you are here
├── SKILL.md                       # Claude Code skill manifest
├── mass_env.py                    # the client + CLI (single file)
├── data/
│   └── sr-ghg-filers-list.xlsx    # bundled SR-GHG snapshot
└── references/
    ├── API_NOTES.md               # full endpoint + field documentation
    └── VALIDATION.md              # end-to-end validation run
```

### Using it as a Claude Code skill
Drop the `mass-env-permits/` folder into your Claude Code skills directory (e.g.
`~/.claude/skills/`). Claude will pick it up automatically and run the right command when you ask
about MA environmental permits, MEPA filings, air-quality plan approvals, waste-site cleanups,
sewage discharges, and the like.

---

## Disclaimer

This tool accesses **public records** from Massachusetts state websites. It's intended for research,
journalism, and civic transparency. Be considerate of the servers, and verify anything important
against the official source before relying on it.
