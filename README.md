# massdep_cli

**Search Massachusetts environmental permitting and review filings from the command line — and pull the PDFs.**

Massachusetts publishes a lot of environmental data through public, no-login websites. The trouble is
they're single-page JavaScript apps: easy to click through one record at a time, impossible to query
in bulk. This tool talks directly to the JSON APIs behind those apps, so you can search by town,
address, applicant, permit type, file number, or date — and download the attached documents.

It works as a plain Python CLI, or as a skill that an agentic coding agent  can drive for you. Like this:


<img width="1211" height="577" alt="image" src="https://github.com/user-attachments/assets/f4153a9a-eb2a-4d6e-b830-8887a16daa58" />

---

## What it covers

| Source | What's in it | Good for |
|--------|--------------|----------|
| **MassDEP ePlace** | Air-quality plan approvals and every other DEP / DCR / MDAR permit application & authorization, with attached documents | "Did someone apply for an air permit / wetlands permit / etc. here?" + the supporting PDFs |
| **MEPA eMonitor** | Environmental review filings — Environmental Notification Forms (ENF), Environmental Impact Reports (DEIR/FEIR), Notices of Project Change (NPC), Secretary's Certificates | "Has this project gone through state environmental review?" + the filed documents |
| **SR-GHG filers list** | Annual roster of facilities required to file Source Registration / Greenhouse-Gas reports, with their air-quality classification and filing schedule | "Which facilities in this town are regulated air-emission sources?" |

The first two are live REST APIs. The third is a spreadsheet MassDEP publishes; a recent snapshot is
bundled in `data/` and you can refresh it on demand.

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

# Find a MEPA project by file number, town, or name
python mass_env.py search-mepa --eea-no 3247
python mass_env.py search-mepa --town Worcester -f csv -o worcester.csv

# Grab a MEPA filing's attachment
python mass_env.py mepa-attachments <submittal-id>
python mass_env.py mepa-download <file-service-id> -o filing.pdf

# Which facilities in a town must file Source Registration / GHG?
python mass_env.py sr-ghg --town WORCESTER
python mass_env.py sr-ghg --refresh        # pull the latest spreadsheet first

# Show the API endpoints the tool discovered, plus reference lists
python mass_env.py info
```

Every list command accepts `-f table|csv|json` and `-o FILE`. Add `-v` to see the requests as they go out.

---

## Commands

| Command | What it does |
|---------|--------------|
| `search-permits` | Search MassDEP permits. Filters: `--city --address --zip --applicant --facility --application-id --permit-types --statuses --from --to` |
| `permit-detail RECORD_ID` | Full record + document list. Needs `--checkbox-code` (it's in the search results) |
| `massdep-download DOC_ID` | Download a MassDEP document by its `DocId` |
| `search-mepa` | Search MEPA projects. Filters: `--project-name --eea-no --town --submittal-type --from --to` |
| `mepa-project PROJECT_ID` | Full MEPA project detail (JSON) |
| `mepa-attachments SUBMITTAL_ID` | List a submittal's attachments (gives you the `fileServiceId`) |
| `mepa-download FILE_SERVICE_ID` | Download a MEPA attachment |
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

The three datasets share keys, so you can follow a project across them:

- MEPA `eeaNo` ⇄ MassDEP `MepaProjectNumber`
- SR-GHG `AQ ID#` ⇄ MassDEP `FacilityID`

A typical check on "has project X filed anything?": search MEPA by project name/town for a review
filing, search MassDEP by city/applicant for a permit, and check the SR-GHG roster for the town.
**Finding nothing is a real answer** — a genuine MEPA no-match returns a total of `0`.

---

## How it works (and why it keeps working)

- **No hardcoded secrets.** The MEPA portal uses a public API key that ships inside its web app's
  config. The tool re-reads that config (and MassDEP's) at runtime, so when the state redeploys and
  the URLs or key change, this keeps working without edits.
- **Polite by default.** One request per second, a generic User-Agent, and automatic retries with
  backoff. Please keep it that way — this hits government servers.
- **Read-only.** It only searches and downloads. It never submits, edits, or logs into anything.

Endpoint-level documentation lives in [`references/API_NOTES.md`](references/API_NOTES.md), and a
run-through proving each piece works is in [`references/VALIDATION.md`](references/VALIDATION.md).

---

## Known limitations

- **No proponent search in MEPA.** The MEPA API exposes a `ProponentName` filter, but it doesn't
  actually work — developer/proponent names live in a separate contacts system. Search by project
  name, town, or `eeaNo` instead. (The CLI warns you when a filter was silently ignored.)
- **MassDEP search isn't paginated.** A very broad search (>200 results) gets truncated; narrow it
  with a town, date range, or permit type.
- **The SR-GHG list is a snapshot**, not live. The bundled copy is dated **Mar 6, 2026**; `--refresh`
  pulls the current file. It's also a *roster* (who must file + their class/schedule), not emissions
  totals — and it only lists established facilities, so it won't show a not-yet-built project.
- **mass.gov blocks some download tools.** That's why the spreadsheet refresh uses `wget`.

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
about MA environmental permits, MEPA filings, air-quality plan approvals, and the like.

---

## Disclaimer

This tool accesses **public records** from Massachusetts state websites. It's intended for research,
journalism, and civic transparency. Be considerate of the servers, and verify anything important
against the official source before relying on it.
