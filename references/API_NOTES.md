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

# ADDENDUM (2026-06-06) — EEA Data Portal "DataLake", CSO, and WasteSite

Three more no-login backends, all on `eeaonline.eea.state.ma.us`. NONE is ePlace
(`eplace.eea.mass.gov/EEAPublicAppAPI`) and none is MEPA. Re-verified live 2026-06-06.

> Seed-intel correction: the EEA Data Portal ("Search Data" menu — Permits, Facilities,
> Inspections, Enforcements, Asbestos, Drinking Water, Lead & Copper, LSP, Wetland NOI,
> Well Drilling, NPDES) is NOT an ePlace/Accela call — it's the EEA **DataLake** REST API.
> Sewage Notification and Waste Site Cleanup are two further standalone SPAs/APIs.

## 4. EEA Data Portal — DataLake API

- Frontend SPA: `https://eeaonline.eea.state.ma.us/Portal/` (AngularJS ui-router;
  logic in `…/Portal/dist/scripts/custom.js`).
- **API base: `https://eeaonline.eea.state.ma.us/EEA/DataLake/V1.0/DataLakeAPI/`** — no
  auth, no key, no cookie.
- **Runtime config = an HTML `<meta>` tag, not a JSON file.** `GET /Portal/` → parse
  `<meta name="data-lake-api-url" content="/EEA/DataLake/V1.0/DataLakeAPI/">` (root-relative;
  resolve against the origin). The client streams only the first ~512 KB (the page is ~5.8 MB)
  and regexes the meta. Also inlined: `file-viewer-url`, and a huge entity-encoded
  `data-lake-lookup-tables` (dropdown values). Recommended header `Referer: …/Portal/`.

### 4.1 Generic search — `GET {base}{resource}`
One contract for all 12 resources → `{ "Items": [...], "TotalCount": N }`. Params: the
resource-specific filters (table) + `_start` (0-based, inclusive) / `_end` (exclusive upper
bound) offset window; `ColumnName` + `Direction` (`asc|desc`) sort. No `_start/_end` → first
**100** rows but full `TotalCount`. A single large `_end` (≥ TotalCount) pulls everything.
> **Paging quirks:** most resources treat `_end` as exclusive; **WIRE** & **Well Drilling**
> share the boundary row between windows; **LSP** uses *inclusive* `_start/_end`. The client's
> `datalake_search_all` dedupes on the id column to absorb all three.

### 4.2 Per-resource registry (resource → id column / town-filter key)

| resource | id column | town param | notable filters | detail | docs/export |
|---|---|---|---|---|---|
| `permit` | `Id` | `Town` | `StreetName`,`FacilityName`,`PermitNumber`,`Program`,`PermitType` | `permit/{Id}` | DocumentLinks (empty in current data); `export-to/excel` |
| `facility` | `Id` | `Town` | `FacilityName`,`FacilityType`,`Active` | `facility/{Id}` | roster; excel |
| `inspection` | `Id` | `Town` | `FacilityName`,`FacilityId`,`InspectionDate` | `inspection/{Id}` | **no export** — pull-all via big `_end` |
| `enforcement` | `Id` | `Town` | `FacilityName`,`Address`,`EnforcementType`,`EnforcementDateFrom/To` | `enforcement/{Id}` | **DocumentLinks REAL** → §4.4; excel |
| `asbestos` | `Id` | `TownName` | `FormType`(ANF-001/AQ-06),`FacilityName`,`FacilityAddress`,`StartDate/EndDate` | `asbestos/{Id}/{FormType}` (FormType req.) | excel |
| `drinkingWater` | `Id` | `Town` | `PWSName`,`PWSId`,`Class`,`ChemicalName`,`CollectedDate` | `drinkingWater/{Id}` | excel |
| `leadandcopper` | `dwp_lab_data_id` | `Town` | `FacilityType`(SCH/EECF/CCF),`SchoolName`,`AnalyteName`(LEAD/COPPER),`CollectionDate` | `leadandcopper/{id}` | excel |
| `lsp` | `LSPNumber` | `TownName` | `LSPNumber`,`LicenseStatus`,`LastName` | `lsp/{LSPNumber}` | excel |
| `wire` | `NOIId` | `TownId` (**numeric**) | `NOINum`,`FilingDate` | `wire/{NOIId}` | excel |
| `welldrilling` | `WellID` | `TownName` | `DrillerRegistrationNumber`,`WellType`,`FromDateComplete/ToDateComplete` | **no JSON (500)** | **PDF: `WellDrilling/generatereport/{WellID}`**; excel |
| `npdes` | `lab_data_id` | `citytown_of_sample` | `report_type`(`PFAS NPDES`/`PFAS Residuals`/`PFAS Groundwater Discharge`),`site_name`,`FromCollectionDate/ToCollectionDate` | `npdes/{lab_data_id}` | excel |
| `searchablesite` | `RTN` | `TownName` | Waste Site / Reportable Releases via DataLake (fields: `RTN`,`SiteName`,`Address`,`ChemicalType`,`SiteType`,`RAOClass`,`ComplianceStatus`,`NotificationDate`,`Lat/Long`) | — (use WasteSiteAPI §6 for RTN detail) | excel |

> **Resource set is closed (probed 2026-06-06).** The Portal `custom.js` `apiUrl` registry lists exactly
> 13 segments; all return `{Items,TotalCount}` except `cso` (500 on the plain path — use the dedicated
> CSOAPI §5). Brute-probing ~75 MassDEP program-area names (tier2, ust, septic, brownfields, chapter91,
> wetlands, ghg, c21e, rtn, …) returned 404 for every one; no discovery/swagger/OData endpoint exists.
> So the 12 usable DataLake resources above are the full set the API routes. (Caveat: an
> unguessable-token resource used by some other EEA app can't be ruled out, but nothing surfaced.)

> **Town-key landmine:** a wrong town key is *silently ignored* (returns the global total,
> not an error/empty). The client hard-codes the registry mapping above; for `wire` the numeric
> `TownId` is resolved via the MEPA postal lookup (DataLake TownId == MEPA TownId, e.g.
> Worcester=450). Date params are `From<Col>`/`To<Col>` (server bumps `To` +1 day).
> Validated Worcester counts: facility 1060, permit 1086, inspection 2017, enforcement 1188,
> asbestos 22456, drinkingWater 7798, leadandcopper 19989, wire 1027, welldrilling 1191
> (npdes is keyed on the sample's `citytown_of_sample` and is sparse — 0 for many towns).

### 4.3 Detail / export / download
- Detail: `GET {base}{resource}/{id}` (asbestos also `/{FormType}`; welldrilling → PDF, not JSON).
- Export: `GET {base}{resource}/export-to/excel?{filters}` → `.xlsx` (GET only; not `inspection`).
- Autocomplete: `GET {base}{resource}/autocomplete/{Column}?substring=`.
- **4.4 Doc download:** `GET {base}{resource}/downloadFile/{fileId}` where `fileId` = last
  path segment of a detail record's `DocumentLinks[i].DocumentLinks` URL. VALIDATED on
  `enforcement` (5.8 MB PDF); only enforcement returns non-empty DocumentLinks in current data
  (others unproven — see §gaps).

## 5. CSO / SSO Sewage Notification (CSOAPI)
- SPA `…/portal/dep/cso-data-portal/`; **API base `…/dep/CSOAPI/api/`** (no key).
  Config (house way, BOM): `GET …/cso-data-portal/assets/config/appconfig.json` → `AppConfig.API_ENDPOINT`.
- **REQUIRED header `Referer: …/portal/dep/cso-data-portal/`** — hard 500 without it.
- Search: `GET Incident/GetIncidentsBySearchFields/?{params}&pageNumber=&pageSize=` →
  `{results, rowCount, …}`. Params: `Municipality`(town NAME), `OutfallId`, `PermiteeName`,
  `PermiteeClass`(CSO/Non-CSO), `EventType`, `ReportingType`, `WaterBody`, `IncidentFromDate/ToDate`,
  `orderBy`. No street-address field. Validated Worcester=159 (e.g. outfall WOR001 → Mill Brook to Blackstone R.).
- Detail `Incident/GetIncidentById?id=`; attachments `Attachment/GetActiveAttachments?id=…` →
  `fileExternalId`; download `Attachment/PortalDownload/{incidentId}/{fileExternalId}` (token, NOT GUID).

## 6. Waste Site Cleanup (WasteSiteAPI) — 21E / RTN
- SPA `…/portal/dep/wastesite/`; **API base `…/dep/WasteSiteAPI/`** (no auth). Config:
  `GET …/wastesite/assets/config/appconfig.json` → `AppConfig.API_ENDPOINT` + `FILESERVICEURL`.
- Search: `GET viewer/GetViewerBySearchFields/?{params}&pageNumber=&pageSize=` → **a top-level
  JSON ARRAY** (no wrapper); total is on every row as string `totalCount` (read `row[0].totalCount`).
  Params: `townName`(UPPER), `address`(free text, cross-town), `rtn`, `siteName`, `lsp`, `chemical`,
  `zipCode`, `siteType`, `regulatoryStatus`, `orderBy`. Fields: `rtn`, `regulateObjectId`, `townName`,
  `address`, `siteName`, `siteType`, `category`, `chemicalType`, `releaseType`, `notificationDate`,
  `complianceStatus`, `raoClass`, `lsp`, `latitude/longitude`, `aulInfo`. Validated Worcester=1782;
  `address=` is free-text and matches across towns (e.g. `address="SOUTHWEST CUTOFF"` → 75 rows,
  including RTN `2-0053500`/regObjId 674115 — DIESEL DIRECT, OPEN).
- Detail: `GET viewer/GetDetailsByRTN/{rtn}/{regulateObjectId}/{false}` (8 result sections).
- Files: `GET viewer/Get{Scanned|Electronically}Files/{rtn}/{sortCol}/{sortDir}/{page}/{size}`.
  Download: `GET {FILESERVICEURL}{fileName-path}` (INFERRED — no sampled RTN had files).
- Bulk: `GET viewer/ExportExcel/?{params}` → `{data: <base64 xlsx>}` (decode before writing).

> NOTE — two distinct "Waste Site" things: the in-Portal **DataLake `searchablesite`** resource
> (`?TownName=WORCESTER`→1775) and this standalone **WasteSiteAPI** viewer (Worcester=1782). The client
> uses the WasteSiteAPI viewer (richer: RTN detail, file lists, RAO/tier sections).

### Gaps / cautions
- DataLake doc download proven only for `enforcement`; other resources' `downloadFile`/permit
  direct-link variant are inferred from JS.
- WasteSite file download is fully inferred (no sampled RTN had populated file lists).
- WIRE/WellDrilling overlap the page boundary; LSP uses inclusive ends → always dedupe on the id col.

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
