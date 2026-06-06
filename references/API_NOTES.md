# API_NOTES — MA environmental-permitting public data

Reverse-engineered and live-verified 2026-06-05. Three sources:

1. **MassDEP "ePlace"** — air-quality plan approvals + all DEP/DCR/MDAR permit records.
2. **MEPA eMonitor** — environmental review filings (ENF / EIR / NPC / Secretary's Certificates).
3. **SR-GHG filers list** — annual Source Registration / Greenhouse Gas filer roster (xlsx).

All read-only, public, no login. Be polite: generic User-Agent, ≤1 req/s, retries. None of the
base URLs or the MEPA key are hard-coded in the client — they are re-scraped from the live runtime
config (`appConfig.json` / `config.json`) on each run, because they change on redeploy.

> Note: the seed intel pointed at `eeaonline.eea.state.ma.us/EEA/PublicApp`; the **current** MassDEP
> portal is `eplace.eea.mass.gov`. MEPA still lives under `eeaonline.eea.state.ma.us`.

---

## 1. MassDEP ePlace

- Frontend SPA: `https://eplace.eea.mass.gov/EEAPublicApp/` (AngularJS 1.4.8, **unminified** — the
  controllers/services under `…/Application/` are readable and are the source of this doc).
- **API base: `https://eplace.eea.mass.gov/EEAPublicAppAPI`** — no auth, no API key.
- Runtime config: `GET /EEAPublicApp/js/appConfig.json` → `SEARCH_API_URL` / `ROOTSCOPE_API_URL` /
  `RECORD_DETAIL_API_URL` (all = the API base). Served with a UTF-8 BOM.
- Reference list: `GET /EEAPublicApp/js/tooltips.json` → permit-code groups + help text.
- Recommended headers: `Content-Type: application/json`, `Referer: https://eplace.eea.mass.gov/EEAPublicApp/`.

### 1.1 Search — `POST /api/Search/Applications`

Request body (`searchCriteriaDto`):

```json
{
  "FacilityName": "",            // facility/site/park name (free text)
  "ApplicantName": "",          // individual applicant/licensee (free text)
  "ApplicationId": "",          // exact record/application id (no partial match)
  "AuthorizationStatuses": [],  // subset of: In Review, Public Comment Pending, Approved, Denied, Withdrawn
  "AuthorizationTypes": [ {"AccelaGroup":"DEP","AccelaType":"AQ","AccelaSubType":null} ],
  "AddressDetails": {"AddressLine1":"","State":"MA","City":"Worcester","Country":"US","ZipCode":""},
  "FromDate": null,             // filed-date range; null or "YYYY-MM-DDT00:00:00"
  "ToDate": null,
  "OperationType": 0,
  "MaxRecords": false
}
```

Response: `{ ..., "List": [ recordItem, ... ] }` (the request criteria are echoed back; the data is in
`List`; the echo also includes a top-level `MepaProjectNumber` field — a DEP↔MEPA cross-link). >200
results triggers a "refine your search" warning in the UI; there is no server pagination on this call.

`recordItem` fields (used downstream in **bold**):
`AuthorizationNumber, **ApplicationId**, **RecordId**, **ContactId**, **CheckBoxCode**, **ApplicantName**,
OwnerName, ProjectNumber, **FacilityName**, **FacilityID**, Status (= **Status**), **FiledDate**,
FiledDateSort, RecordCategory, **RecordType**, **RecordTypeAlias**, ApplicantAddress{AddressLine1,
City, State, ZipCode}, X_COORD, Y_COORD, ProjectName, ProjectDescription, PerGroup, MepaProjectNumber`.

**AuthorizationTypes** (`AccelaGroup` → `AccelaType`):

| Group | AccelaTypes |
|-------|-------------|
| DEP   | AQ (Air quality), DW (Drinking water), HW (Hazardous waste), SW (Solid waste), TUR, WM (Watershed/NPDES), WW (Wetlands & Waterways), WP (Water Pollution), LES (Lab Certification) |
| DCR   | SUP (Special Use Permits), CAP (Construction & Vehicle Access Permits) |
| MDAR  | Pesticide (AccelaSubType = "Pesticide Credential" or "Product Registration"), Plant Industries |

**Air-permit signal of interest** = `{AccelaGroup:"DEP", AccelaType:"AQ"}`. AQ record types seen:
AQ01/AQ01M (Limited Plan Approval), AQ02/AQ02F (Non-Major Comprehensive Plan Approval; **F = Fuel /
combustion** application), AQ03, AQ14 (Operating Permit), AQ34 (LPA/CPA amendment), AQ50/25, AQMM.
AQ codes from `tooltips.json`: `AQ50/25, AQ01, AQ01M, AQ02, AQ03, AQ08A/B/22, AQ09, AQ14/12, AQ18,
AQ30, AQ33, AQMM`.

### 1.2 Detail — `POST /api/Application/Detail`

Body `{"RecordId","ContactId","CheckBoxCode"}` (all three from a search row; `ContactId` is usually
`""`). Response:

```
{ RecordDetail{RecordNumber, RecordType, Status, FiledDate, IssueDate, AccessCode, ...},
  Comments[],
  ApplicationDocuments[ {DocId, Name, Type(mime), Category, Group, Description, DocDate, Size} ],
  AgencyName, AgencyEmail, Date_Assigned, Date_due, Task, Task_Status }
```

`ApplicationDocuments[].DocId` is what you pass to the download endpoint. Categories are descriptive,
e.g. *"Combustion Equipment Manufacturer Specifications…"*, *"AQ Modeling Analysis/Report"*.

Alternate detail (no ContactId/CheckBoxCode needed): `GET /api/Transaction/{recordId}`.
Also exists: `POST /api/Search/Record` (search by code).

### 1.3 Document download — `GET /api/Application/GetS3Document?docID={DocId}`

Returns the file bytes (PDF). `MAX_DOCUMENTS_ALLOWED`/`MAX_TOTAL_DOC_SIZE` in appConfig are upload-side.

---

## 2. MEPA eMonitor

- Frontend SPA: `https://eeaonline.eea.state.ma.us/EEA/MEPA-eMonitor/` (Angular es2015; hashed bundles
  — re-scrape the home page for `main-es2015.<hash>.js` if you need to re-derive endpoints).
- **Runtime config (re-scrape; do not hard-code): `GET …/MEPA-eMonitor/assets/config/config.json`**
  → `ApiConfig` with:
  - `API_ENDPOINT` — main API (AWS API Gateway), e.g.
    `https://<gateway-id>.execute-api.us-east-1.amazonaws.com/PROD/V<ver>/api/`
  - `Api_Key` — **public** key; **required** as `x-api-key` (403 without it, 200 with).
  - `POSTAL_API_ENDPOINT` + `POSTAL_API_KEY` — town/address lookups.
  - `ATTACHMENT_API_ENDPOINT` (a `…/FileService.Api/` host), `ATTACHMENT_API_KEY`,
    `Authorization` (`FS-StaticAuth …`) — file download.

  > The concrete gateway IDs/keys are **not reproduced here** — they are public (baked into the SPA's
  > `config.json`) but change on redeploy, so the client reads them live each run. To see the current
  > values, fetch `config.json` (or run `python mass_env.py info` for the resolved base URLs).
- Recommended header: `Referer: …/MEPA-eMonitor/search`.

### 2.1 Project search — `GET {API_ENDPOINT}Project/search`

Query params (all optional; combine freely):

| Param | Meaning |
|-------|---------|
| `ProjectName` | project name (free text) — **reliable** |
| `ProjectNumber` | EEA/MEPA file number (`eeaNo`) |
| `ProjectId` | project GUID |
| `ProponentName` | **NON-FUNCTIONAL** — see note below |
| `ProjectType` | projectTypeId (see `GET ProjectType`) |
| `SubmittalType` | submittalTypeId |
| `City` | numeric **TownId** (resolve via the postal lookup, §2.5) |
| `Watershed`, `CountyId` | numeric ids |
| `SubmittalDateFrom`, `SubmittalDateTo` | `M/D/YYYY` |
| `isExactAgency`, `isExactAction`, `isExactThresholdCat` | `true/false` (send `false`) |
| `currentPage` | 1-based page; server `pageSize` = 1000 |

Response: `{ totalRecords, currentPage, pageSize, list:[ project ] }` where each `project` =
`{ projectId, projectName, eeaNo, location, cityTown(TownId), municipalId, mepaAnalyst,
submittals:[ {submittalId, submittalType (ENF/EIR/DEIR/FEIR/NPC/NPC Cert/EENF/EDR/…), submitDate,
actionDate, status, determination, publishDate, commentsDueDate} ], projectTypes[], watersheds[],
thresholds[], contacts[] } }`.

`eeaNo` is the public MEPA/EEA file number; it cross-references the MassDEP `MepaProjectNumber`.

> **ProponentName is broken in the public API.** Proponent/developer names are stored in a separate
> contacts/people system (the project only carries contact GUIDs; resolving names needs the
> PeopleAndOrg API + key). A `ProponentName=` query returns the *global* `totalRecords` with an **empty
> list**. Detector: `totalRecords > 0 && list == []` ⇒ a filter was ignored (a genuine no-match returns
> `totalRecords == 0`). To search by developer, use `ProjectName` (developer names often appear there),
> `town`, or `eeaNo`.

### 2.2 Project detail — `GET {API_ENDPOINT}Project/{projectId}`

Returns `{ projectId, projectName, eeaNo, projectTypeId, estimatedCost, notes, location,
cityTownIds, cityTown, thresholds, addressWatershed, latitude, longitude, agencyActions[], … }`.

### 2.3 Attachment list — `GET {API_ENDPOINT}Attachment/ListBySubmitalId/{submittalId}`

(Note the single-`t` typo `Submital` is the real path.) Also `Attachment/ListByPublicationHistoryId/{id}`.
Returns `[{attachmentId, fileName, size, uploadedDate, fileServiceId, documentDescription}]`.
Use **`fileServiceId`** (a short token like `aegebahaj`) for download, *not* the `attachmentId` GUID.

### 2.4 Attachment download (3-step)

1. `GET {API_ENDPOINT}Attachment/GetEncryptedTokens` (with `x-api-key`) →
   `{encryptedAppToken, appDataReadToken, encryptedAuthToken}`.
2. `GET {ATTACHMENT_API_ENDPOINT}file/MEPA/{fileServiceId}` with headers:
   `x-api-key: <ATTACHMENT_API_KEY>`, `Authorization: <config.Authorization>`,
   `appToken: <encryptedAppToken>`, `dataToken: <appDataReadToken>`, `authToken: <encryptedAuthToken>`.
   → **302 redirect** to a presigned S3 URL (`eea-datalake-prod.s3.us-east-1.amazonaws.com/...`).
3. `GET <presigned S3 URL>` **with no auth headers** (S3 rejects "two auth mechanisms" if you resend
   `Authorization`) → file bytes.

### 2.5 Lookups

- Towns: `GET {POSTAL_API_ENDPOINT}Lookup/towns/byState/22` (with `POSTAL_API_KEY`); **MA = StateId 22**.
  Returns `[{TownId, TownName, IsOfficial, CountyId, CountyName}]` (1017 MA towns; resolve any name to
  its numeric TownId for the `City` filter).
- Single town: `GET {POSTAL_API_ENDPOINT}Lookup/town/{id}`.
- Project types: `GET {API_ENDPOINT}ProjectType`. Also `Determination`, `Action/GetByAgencyId`,
  `Watershed`, `Lookup/publications`, `Contact/GetByProjectId/{projectId}` (GUID-only).

---

## 3. SR-GHG filers list (xlsx)

- mass.gov page (`/info-details/search-source-registration-greenhouse-gas-filers-list`) is a Power BI
  embed, but a **direct spreadsheet** exists: `https://www.mass.gov/doc/sr-ghg-filers-list/download`
  → 301-redirects to the year file (`…/sr-ghg-filers-list-for-2026/download`), ~223 KB xlsx.
- **mass.gov Akamai-blocks curl/requests (403); `wget` works** (follows the 301). The client refreshes
  via `wget` and otherwise reads the bundled snapshot in `data/sr-ghg-filers-list.xlsx`.
- This is a *roster* (who must file + class + schedule), **not** emission tonnage. It's lagging
  (only established facilities are listed) so it won't show a not-yet-built project; value is the
  facility roster by town + classification + cross-linking to permits.
- Sheet `SRGHG-All-Filers-List_<date>` (≈1,421 rows). Columns: `SR Status, AQ ID#, Facility Name,
  Town, MassDEP Region, Current Class` (e.g. SM50/NM99/OP3 = Synthetic Minor / Natural Minor /
  Operating Permit class), `What to File` (SR / GHG / SR-GHG), `File By`, `SR Schedule`, `GHG Schedule`,
  `Current Class Since`, `Current Class Description`, `Facility Type` (PRIVATE/STATE/FEDERAL/LOCAL
  GOVERNMENT), `Site Account #`, … plus a `ReadMe` sheet with the "Updated" date.
- `AQ ID#` / `Site Account #` is a likely join key to ePlace `FacilityID`.

---

## Field cross-reference

| Concept | MassDEP ePlace | MEPA eMonitor | SR-GHG |
|---------|----------------|---------------|--------|
| Record/file id | `ApplicationId`, `RecordId` | `eeaNo`, `projectId` | `AQ ID#` |
| MEPA link | `MepaProjectNumber` | `eeaNo` | — |
| Applicant/proponent | `ApplicantName`, `FacilityName` | (contacts only — not searchable) | `Facility Name` |
| Municipality | `ApplicantAddress.City` | `cityTown` (TownId) | `Town` |
| Status | `Status` | submittal `status`/`determination` | `SR Status` |
| Documents | `ApplicationDocuments[].DocId` | `Attachment…/fileServiceId` | — |
