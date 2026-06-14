# DATA_DICTIONARIES — official MA-state column & code definitions

Comprehensive companion to `API_NOTES.md`. `API_NOTES.md` documents the APIs' wire format
(reverse-engineered — **no API ships a schema**). This file gives the **officially published**,
verbatim field/column definitions and code lists for each endpoint, transcribed from the source
artifacts bundled in `../data/dictionaries/`. Compiled & live-verified 2026-06-13.

**Access:** every `mass.gov` / `eeaonline…` URL Akamai-403s curl/requests — refresh with **`wget`** +
a generic UA. The FGDC XMLs come from AGOL (`…/FeatureServer/0/metadata?format=fgdc&f=xml`) or the
layer's S3 shapefile zip.

**Primary sources** (all bundled offline):
- **EEA Data Portal FAQ** (`eea-data-portal-general-query-search-faqs.pdf`, dated 7/19/2024) — the
  official dictionary for **10** DataLake resources: permit, facility, inspection, enforcement,
  drinking water, asbestos, wetlands NOI, **lead & copper**, **LSP**, waste site — plus the master
  permit/program-type code list (pp.46–57). Section/page anchors cited below.
- **PFAS Field-Definitions-for-Labs** XLSX ×2 (npdes).
- **"Understanding the Waste Site/Release Look Up"** PDF (21E codes).
- **SR-GHG xlsx** `ReadMe` tab + `Current Class Description` column.
- **MassGIS FGDC** XML (Major Facilities `BWPMAJOR_PT`; 21E `C21E_PT`).
- **Well Completion Report Codes** page (well codes).
- **Regulations** (the legal source of truth for codes): 301 CMR 11 (MEPA), 310 CMR 40 (MCP/21E),
  310 CMR 7.12/7.71/4.03 (SR-GHG), 310 CMR 46 (wells), 314 CMR 16 (CSO), 310 CMR 22 (drinking water).

## Discovery layers (not data sources)
- **`data.mass.gov`** = "Massachusetts Data Hub", a Next.js **catalog** (not Socrata/CKAN) indexing
  mass.gov + EEA portal pages. Browse JSON: `GET /_next/data/<buildId>/browse/<topic>.json`
  (`<buildId>` from homepage HTML, changes on redeploy). No dictionary content of its own.
- **`gis.data.mass.gov`** = MassGIS ArcGIS Hub — source of the FGDC field dictionaries.

## Status by endpoint
● full column defs · ◐ partial · ○ none (regulation/federal only)

| Endpoint | | Column defs from |
|---|:--:|---|
| ePlace `search-permits` / DataLake `permit` | ● | FAQ p.7 + permit/program-type table pp.46–57 |
| DataLake `facility` | ● | FAQ p.10 + FGDC Major Facilities |
| DataLake `inspection` | ● | FAQ p.12 |
| DataLake `enforcement` | ● | FAQ p.13 (type-code list → ICIS-FE&C) |
| DataLake `drinkingWater` | ● | FAQ p.14 |
| DataLake `leadandcopper` | ● | FAQ "Lead and Copper in Schools/Childcare" |
| DataLake `asbestos` | ● | FAQ pp.16–17 (search + detail) |
| DataLake `lsp` | ● | FAQ "LSP Lookup" (search + detail) |
| DataLake `wire` (wetland NOI) | ● | FAQ "Wetlands NOI" (search + detail) |
| DataLake `welldrilling` | ● | Well Completion Report Codes page |
| DataLake `npdes` (PFAS) | ● | PFAS Field-Defs XLSX ×2 |
| `searchablesite` / `search-wastesite` | ● | Waste-Site Look-Up PDF + FGDC C21E |
| `sr-ghg` | ● | SR-GHG xlsx ReadMe + Current Class Description |
| `search-mepa` | ○ | 301 CMR 11.02/11.03 (no field dict) |
| `search-cso` | ○ | 314 CMR 16.00 (no field dict) |

---

# A. ePLACE / DataLake "Data Search" family
Source: EEA Data Portal FAQ (bundled). Verbatim definitions.

## A.1 Permits — `search-permits`, DataLake `permit` (FAQ p.7)
1. **Facility/Individual** — Name of organization/individual who has applied for a permit,
   authorization, license, or certification.
2. **Program** — The EEA program associated with the regulatory category for permits.
3. **Street Address** — The street name of the facility's address.
4. **Decision Date** — Date when the final decision of a permit application has been determined.
5. **Permit Number** — An identification number associated with the permit, issued to a
   facility/individual upon permit approval.
6. **Permit Type** — EEA agency authorizations, permits, licenses or certifications (defined in the
   MassDEP Fees Regulations, https://www.mass.gov/files/documents/2017/01/qw/permitfees.pdf).
7. **Town** — City/town where the facility/individual is located. Cities/towns shown only for MA;
   out-of-state render blank (details screen shows out-of-town ZIPs).

*NPDES note (FAQ):* in MA, EPA is the NPDES permitting authority; permits are typically co-issued by
EPA + MassDEP. MassDEP tracks **individual** permits but not all **general** permits → the portal is
not a comprehensive NPDES list (use EPA ECHO). Municipal NPDES are filed under **Watershed
Management**, industrial NPDES under **Industrial Wastewater**. Portal carries NPDES permitting only,
not compliance/enforcement.

### Permit/Program-type code list (FAQ pp.46–57 — `Program` & `Permit Type` values)
**Program controlled vocabulary** (12 groups; `Permit` code prefix → group → issuing agency):

| Program group | Code prefix | Agency |
|---|---|---|
| AIR QUALITY CONTROL | `AQ01–AQ34` | MassDEP |
| ASBESTOS | `AQ04/ANF001`, `AQ06` | MassDEP |
| HAZARDOUS WASTE | `HW…` | MassDEP |
| INDUSTRIAL WASTEWATER | `IW…`, `DEP01B` | MassDEP |
| PESTICIDES | `AL,CB,CC,DL,PC` | MDAR |
| SOLID WASTE MGMT | `SW…` | MassDEP |
| TOXIC USE REDUCTION | `TU01–TU04` | MassDEP |
| WASTE SITE CLEANUP | `BWS…` | MassDEP |
| WATER POLLUTION CONTROL | `WP…`, `DEP01A` | MassDEP |
| WATER SUPPLY/DRINKING WATER | `WS…` | MassDEP |
| WATERSHED MANAGEMENT | `WM…` (incl. NPDES `WM05/06/07`) | MassDEP |
| WETLANDS & WATERWAYS | `WW…` | MassDEP |

**Air Quality codes in full** (the skill's core use case — AQ = on-site combustion / plan approvals):

| Code | Description |
|---|---|
| AQ01 | Plan Approval Limited |
| AQ02 | Plan Approval Non-Major Comprehensive |
| AQ03 | Plan Approval Major Comprehensive |
| AQ08A | Emission Control Plan NOx/VOC State Only Review |
| AQ08B | Emission Control Plan NOx/VOC State & EPA Review |
| AQ09 | Restricted Emissions Status Plan |
| AQ10 | Operating Permit Minor Modification |
| AQ11 | Operating Permit Administrative Amendment |
| AQ11A | Operating Permit Enrollment |
| AQ12 | Operating Permit Renewal |
| AQ13 | Operating Permit Significant Modification |
| AQ14 | Operating Permit Initial |
| AQ15 | Group A Operating Permit |
| AQ16 | Group B Operating Permit |
| AQ17 | Group C Operating Permit |
| AQ18 | Emission Reduction Banking & Trading Credit Certification |
| AQ19 | Certify ECP / NOx Cap w/o Public Comment |
| AQ20 | Certify ECP / NOx Cap with Public Comment |
| AQ21 | Certify ECP / NOx Cap with Significant Physical Changes |
| AQ22 | Emission Control Plan - Municipal Waste Combustor |
| AQ23 | Prescribed or Alternative NOx Emission Control Plan |
| AQ25 | Emission Control Plan - Power Plant |
| AQ27 | Certification of Greenhouse Gas Credits |
| AQ29 | Emission Control Plan - Clean Air Interstate Rule (CAIR) |
| AQ30 | Emission Control Plan - Carbon Dioxide Budget |
| AQ33 | Plan Approval Limited/Comprehensive Consolidation |
| AQ34 | Plan Approval Limited/Comprehensive Admin Amendment |

**Complete enumeration:** all **274** permit/program-type rows (every code across AQ, HW, IW,
PESTICIDES, SW, TU, BWS, WP, WS, WM, WW with its official description and agency) are transcribed in
`../data/dictionaries/permit_program_types.csv` (columns `program,code,description,agency`), keyed
from the FAQ PDF pp.46–57 read as page images. Some codes legitimately recur with distinct
sub-descriptions (e.g. `WS06A`, `WP58B`, `WW01C`) — preserved as separate rows.

## A.2 Facilities — DataLake `facility` (FAQ p.10)
1. **Facility/Individual** — Name of organization/individual where a permit has been applied for.
2. **Program** — MassDEP program associated with the regulatory category for facilities/individuals.
3. **Facility Type** — Category of organizations/individuals regulated by MassDEP.
4. **City/Town** — City/town where the facility is located (out-of-state render blank).
5. **Permit Type** — The permit of interest to the associated facility/individual.
6. **Active** — If Yes: the facility/individual holds active permit(s) from MassDEP.

> A "Release" facility-type under the "Waste Site Clean-up" program is an address/location on a waste
> site permit, not necessarily a regulated facility.

### MassGIS Major Facilities FGDC (`BWPMAJOR_PT`) — attribute dictionary
| Field | Definition / domain |
|---|---|
| FAC_ID | Facility ID |
| FAC_NAME | Facility name |
| ADDRESS | Facility address |
| TOWN | Town where facility located (351 official town names) |
| REGION | DEP administrative region |
| AIR | Has air operating permit (domain: `Y`=has air operating permit) |
| HWR | Hazardous-waste recycler (`Y`=recycler of HW) |
| TSDF | Treatment/Storage/Disposal of HW (`Y`) |
| LQG_MA | Large Quantity Generator of MA-regulated HW |
| LQG_RCRA | Large Quantity Generator of EPA-regulated HW |
| LQTU | Large Quantity Toxics User (`Y`) |
| HW_ID | **EPA HW generator ID from RCRIS (now RCRAInfo)** — cross-link to federal |
| SSEIS_ID | Stationary (Air) Source Emission Inventory System ID — cross-link to NEI/AQ ID |

## A.3 Inspections — DataLake `inspection` (FAQ p.12)
1. **Facility/Individual** — Name of facility/individual where an inspection took place.
2. **Program** — MassDEP program associated with the regulatory category.
3. **Inspection Date** — The date the inspection took place.
4. **City/Town** — City/town where the facility is located and the inspection took place.

> Inspections attach to the **facility** record, not a single permit.

## A.4 Enforcements — DataLake `enforcement` (FAQ p.13)
1. **Facility/Individual** — Name of party against which the enforcement is levied.
2. **Program** — MassDEP program associated with the regulatory category.
3. **Street Address** — Street name where the facility/individual is located.
4. **Issued Date** — Date the enforcement document/action is signed/executed.
5. **City/Town** — City/town where the facility is located and enforcement issued.
6. **Type of Enforcement** — Type of legal action taken to obtain compliance or penalties. *(The
   enumerated type list is in a "Terms and Definitions" doc in the Portal Help tab — not a fetchable
   file; use EPA ICIS-FE&C as the authoritative enforcement-type vocabulary.)*

> Penalties optional per type; documents only for actions issued **on/after 2017-01-01**; records
> posted 10 days after issuance.

## A.5 Drinking Water — DataLake `drinkingWater` (FAQ p.14)
1. **PWS ID** — ID issued to a Public Water System serving ≥25 people ≥60 days/yr.
2. **City/Town** — Where the PWS is located.
3. **Contaminant Group** — Constructed groups of contaminants based on Safe Drinking Water Act testing
   rules.
4. **Raw or Finished** — Raw = natural state pre-treatment; Finished = treated, ready for delivery.
5. **Collected Date** — Date(s) sample(s) collected from the PWS.
6. **PWS Name** — List of MA Public Water Systems.
7. **Class** — `NTNC` Non-Transient Non-Community (serves ≥25 of the same people ≥6 mo/yr at
   non-residences: schools, factories, offices, hospitals); `NC` Non-Community (gas station,
   campground — transient); `COM` Community (≥25 same people year-round at residences).
8. **Chemical Name** — Substance tested, a member of one of the Contaminant Groups.

> Non-detects reported as `ND` (< Method Detection Limit / Minimum Reporting Level). No MCL shown ⇒
> none exists / proposed-not-adopted / not yet promulgated. Authoritative chemistry: EPA SDWIS.

## A.6 Lead & Copper in Schools/Childcare — DataLake `leadandcopper` (FAQ)
1. **Facility Type** — `SCH` Schools (public/private incl. vocational-technical, collaborative,
   special education, charter); `EECF` Childcare (licensed programs incl. after-school).
2. **City/Town** — Based on selected Facility Type.
3. **School/EECF Name** — Based on selected City/Town and Facility Type.
4. **Chemical Name** — Substance tested.
5. **Collected Date** — Date(s) sample(s) collected at the school/childcare facility.
6. **Level** — Whether the chemical was detected or not detected.
7. **Location Description** — Description of the sample location (e.g. "Bubbler next to classroom #1A").
8. **Location Code** — School/childcare-specific unique location identifier; naming convention `###P`
   or `###F` — **`P` = first-draw sample, `F` = flush sample**.
9. **1st Draw sample** — Tap sample after water stood motionless 8–18 hours.
10. **Flush Sample** — Tap sample after standing 8–18 hours then run 30 seconds (tests lead in
    plumbing behind the wall).
11. **Remediation Actions Taken** — Actions in response to an elevated result (shut off fixture,
    replace/repair, install filter, notify parents).

## A.7 Asbestos — DataLake `asbestos` (FAQ pp.16–17)
**Search:** 1. **Project ID** — unique number assigned at notification (older = Sticker/Decal #).
2. **City/Town** — 351 MA cities/towns. 3. **Form Type** — `AQ 04 (ANF-001)` Asbestos Removal
Notification · `AQ 06` Construction/Demolition Notification. 4. **Location Name** — descriptive name
(often company name, or for residential the address). 5. **Location Address** — usually a street
address. 6. **Project Start Date** / 7. **Project End Date** — range allowed.
**Detail:** Project ID; **Owner Name**/**Owner Address**; **Project Type** (brief description);
**DLS Contractor / DLS Site Supervisor / DLS Project Monitor / DLS Analytical Services Lab** —
Dept. of Labor Standards asbestos licensure roles (453 CMR 6.00). DB covers records from **2002**.

## A.8 Licensed Site Professionals — DataLake `lsp` (FAQ "LSP Lookup")
**Search:** 1. **State** — LSP location state (not all in MA). 2. **City/Town**. 3. **License
Number** — assigned on passing the licensing exam. 4. **License Status**:
- **Active** — active license in good standing.
- **Inactive** — up to two years; may not practice/advertise as an LSP while inactive.
- **Lapsed** — formerly an LSP, no longer, due to nonrenewal.
- **Revoked** — license terminated by the Board via disciplinary action.
- **Surrendered** — surrendered per written agreement to resolve a disciplinary complaint.
- **Suspended** — suspended by the Board via disciplinary action.
- **Suspended – Fees** — suspended for failure to pay the Annual Fee.

**Detail:** Name; LSP Number; Company; License Status; Phone; Email; **Date Licensed** (original);
**Expiration Date**; **Disciplinary History** (table of actions). (LSP Board = 309 CMR + G.L. c.21A §19.)

## A.9 Wetlands Notice of Intent — DataLake `wire` (FAQ "Wetlands NOI")
**Search:** 1. **NOI Number** — file number assigned on submission. 2. **City/Town** — 351 MA
cities/towns. 3. **Filing Date** — most NOI data back to the 1980s (some sporadic earlier,
back-entered).
**Detail:** NOI Number; **Applicant Information** (company or individual); Filing Date; **Filing Type**
— `Buffer Zone` (Buffer Zone Impacts Only) · `NOI` (Notice of Intent) · `ANRAD` (Abbreviated Notice of
Resource Area Delineation); **Project Type** — 9 types: Single Family Home, Commercial/Industrial,
Utilities, Transportation, Agriculture, Residential Subdivision, Dock & Pier, Coastal Engineering,
Other; **Project Address**; **Comments**; **Technical Comments**; **Tables** (resource areas altered —
proposed alteration & replacement units, *proposed* not final permitted amounts).

> `*` next to a project address = submitted electronically via eDEP.

---

# B. Well Drilling — DataLake `welldrilling`
Source: **Well Completion Report Codes** page (310 CMR 46.00). Codes used on Well Driller forms.

**Work Performed:** `DP` Deepen · `HF` Hydrofracture · `NW` New Well · `RP` Repair · `RE` Replacement.
**Well Type:** `CTPR` Cathodic Protection · `DMST` Domestic · `DSGT` Domestic/Geothermal · `GCON`
Geoconstruction · `GTOL` Geothermal Open Loop · `INDS` Industrial · `INJC` Injection · `IRRG`
Irrigation · `PBWS` Public Water Supply · `RCVR` Recover · `TSTW` Test Wells.
**Drilling Method:** `AH` Air Hammer · `AR` Air Rotary · `AG` Auger · `CT` Cable Tool · `CA` Casing
Advancement · `CR` Core · `DP` Direct Push · `DW` Drive and Wash · `DG` Dug · `MR` Mud Rotary · `RR`
Reverse Rotary · `SN` Sonic.
**Overburden Lithology:** `B` Boulders · `CL` Clay · `CF` Clean Fill · `CS` Coarse Sand · `C` Cobbles
· `FS` Fine Sand · `FCS` Fine to Coarse Sand · `G` Gravel · `MS` Medium Sand · `O` Organics · `SG`
Sand & Gravel · `SI` Silt · `SICL` Silty Clay · `SIS` Silty Sand · `SISG` Silty Sand & Gravel · `T` Till.
**Bedrock Lithology:** `AM` Amphibolite · `BS` Basalt · `CG/BR` Conglomerate/Breccia · `DI` Diorite ·
`GB` Gabbro · `GN` Gneiss · `GR` Granite · `LS` Limestone · `MA` Marble · `QZ` Quartzite · `RH`
Rhyolite · `SS` Sandstone · `SH` Schist/Shale · `SL/PH` Slate/Phyllite.
**Color:** `BL` Black · `BG` Bluish Gray · `BR` Brown · `DG` Dark Gray · `OG` Greenish Gray · `LG`
Light Gray · `RB` Reddish Brown · `YB` Yellowish Brown.

---

# C. NPDES / PFAS — DataLake `npdes`
Source: **PFAS Field-Definitions-for-Labs** XLSX (bundled). Two report types share most fields.

## C.1 PFAS Wastewater (ReportType = "PFAS Wastewater"; NPDES/Surface-Water Discharge)
| Field | Req | Type | Definition / valid values |
|---|---|---|---|
| ReportType | R | text | Must be "PFAS Wastewater" |
| FacilityID | R | alphanum | NPDES permit number (one file per Facility ID); see FacilityID tab |
| LabID | R | number | Testing lab (one LabID per upload); see Labs tab |
| SecondaryLaboratory | O | text | Contracted lab if different |
| IndustrialName | cond | text | Company name for indirect (upstream) dischargers to a POTW; blank for samples at the NPDES facility. Required when SampleSubLocation = Industry |
| LabSampleIdentifier | R | text | Unique sample ID from the lab |
| DateSampleCollected | R | date | mm/dd/yyyy |
| TimeSampleCollected | O | time | h:mm |
| ResubmissionIndicator | R | text | `O` Original · `R` Resubmission · `C` Confirmation |
| ResubmissionReason | cond | text | `RES` Resample · `REA` Reanalysis · `REC` Report Correction (when Indicator=R) |
| DateOfOriginalSample | cond | date | When Indicator=R; ≤ DateSampleCollected |
| SampleType | R | text | `Primary` · `Duplicate` · `Other` (Other = blanks) |
| SampleTypeOtherDescription | cond | text | Blank type (field/equipment blank) when SampleType=Other |
| SampleSubLocation | R | text | `Influent` · `Effluent` · `Sludge` (from WWTF) · `Industry` (upstream POTW discharger) |
| LabSampleIDOfOriginalSample | O | text | Resubmissions only |
| SampleComment | O | text | Notes (e.g. industry type for Industry samples) |
| PFASWasteWaterCompounds | R | text | One row per required PFAS compound; see tab (PFAS6 or all 40 in Method 1633) |
| CASNumberOfPFASRequired | O | text | CAS number |
| PercentSolids | cond | decimal | When Unit=ng/g; percentage points ("25" not "0.25") |
| Qualifier1–3 (+ Description) | O/cond | text | Lab qualifier(s); description ≤255 chars when qualifier present |
| Value | R | alphanum | Result: number or `Less Than LOD` · `Less Than RL` · `ND` · `Not Tested` |
| Unit | R | text | `ng/g` · `ng/L` |
| MethodReportingLimitPFAS | R | decimal | Method reporting limit |
| MethodDetectionLimitPFAS | R | decimal | Method detection limit |
| AnalysisStartDate | R | date | ≥ Collection Date, ≤ today |
| AnalysisStartTime | O | time | h:mm |
| AnalysisComments | O | text | — |
| AnalyticalMethod | R | text | Lab method, free text (e.g. "EPA Method 1633") |

## C.2 PFAS Residuals (ReportType = "PFAS Residuals"; Approvals of Suitability)
Same structure with these differences: **ResidualsFacilityID** (number; see ResidualsFacilityID tab)
replaces FacilityID; **ResidualsPFASRequiredCompounds** replaces PFASWasteWaterCompounds (from
2025-04-25, all 40 compounds via Method 1633); **ResidualsOtherPFASCompounds** /
**CASNumberOfPFASOther** must be **left blank**; **SampleSubLocation** is Optional; **LabID** may be
any lab for Method 1633, else only labs with a MassDEP-approved SOP; **ResidualsPercentSolids**.
All Value/Unit/limit/qualifier/analysis fields identical to C.1.

---

# D. Waste Site Cleanup / 21E — `search-wastesite`, DataLake `searchablesite`
Source: **"Understanding the Waste Site/Release Look Up"** PDF + FGDC `C21E_PT`. Legal: 310 CMR 40
(MCP) under M.G.L. c.21E.

**Search fields (FAQ):** Search Type (`All Sites` / `Only Sites with Activity & Limited Use`);
City/Town (Boston & Barnstable by neighborhood/village); **RTN**; Address; **Compliance Status**; LSP;
Site Name. Results: RAO Class & Detail; Related Links (documents); Export to Excel.

**Core fields (Look-Up PDF):**
- **RTN (Release Tracking Number)** — unique site ID; region prefix `1`=Western, `2`=Central,
  `3`=Northeast, `4`=Southeast.
- **Reporting Category** — how soon the release must be reported: `2 hours` · `72 hours` · `120 days`
  · `None` (release predated the 1993 categories).
- **Chemical Type** — Oil / Hazardous Material / **Both (OHM)**.
- **Phase** — cleanup phase: No Phase, Phase I–V.
- **Compliance Status Date** — date listed as the current status.

**Compliance Status codes** (verbatim):
| Code | Meaning |
|---|---|
| ADEQUATE REG | Adequately Regulated — response under another state/federal program (310 CMR 40.0110) |
| DEPMOU | DEP has an MOU/written agreement with a responsible party |
| DEPNDS | (pre-1993) DEP determined not a disposal site |
| DEPNFA | (pre-1993) DEP determined no further action needed |
| DPS | Downgradient Property Status — contamination from up-gradient property (310 CMR 40.0180) |
| DPSTRM | Downgradient Property Status terminated |
| INVSUB | Invalid Submittal (e.g. RAO/PSNC found invalid by DEP) |
| LSPNFA | (pre-1993) LSP determined no further action |
| PENNDS | (pre-1993) pending "not a disposal site" submittal awaiting DEP audit |
| PENNFA | (pre-1993) pending "no further action" submittal awaiting DEP audit |
| PSNC | (post-2014) Permanent Solution with No Conditions |
| PSC | (post-2014) Permanent Solution with Conditions (may require an AUL deed restriction) |
| RAO | (pre-2014) Response Action Outcome — Permanent/Temporary Solution Statement submitted |
| RAORCD | (pre-2014) RAO Statement received (status eliminated) |
| REMOPS | Remedy Operation Status — active O&M remedial system operating |
| ROSTRM | Remedy Operation Status terminated |
| RTN Closed | Release folded into a "primary" RTN |
| SPECPR | Special Project — modified timelines for complex projects |
| STMRET | Statement Retracted |
| TCEXT | Tier Classification Extension received |
| TCLASS | Tier Classification submittal received, type not yet confirmed |
| TIER 1 | Classified Tier 1 (subcategories 1A/1B/1C discontinued 2014) |
| TIER 2 | Classified Tier 2 |
| TIER 1D | Responsible party missed a required-submittal deadline (formerly Default Tier 1B) |
| UNCLASSIFIED | Not yet classified |

**RAO Class (closure type):** post-2014 = `PA`, `PC`, `PN`, `TF`, `TN`; pre-2014 still-applicable =
`A1`, `A2`, `A3`, `A4` (A3/A4 = AUL implemented), `B1`, `B2`, `B3` (B2/B3 = AUL), `C` (temporary,
5-year review). AUL = Activity & Use Limitation.

**FGDC `C21E_PT` attributes:** RTN; NAME (site name describing location/use/type, assigned by BWSC);
ADDRESS; TOWN (1–351 standard municipality); STATUS (Chapter 21E compliance status); SITE_INFO (link
to site web page); REGION (MassDEP region code). Companion tables: `C21E_PT_LDT` (location
documentation), `C21E_PT_USL` (unlocated sites).

> The bulk `.dbf` download (`…/doc/downloadable-data-waste-site-cleanup-notifications-status/download`)
> ships RELEASE/ACTION/CHEMICAL/LOCATION/SOURCE files **without** a README — decode with this section.

---

# E. SR-GHG filers — `sr-ghg`
Source: bundled `../data/sr-ghg-filers-list.xlsx` (`ReadMe` tab + `Current Class Description` column).
Legal: 310 CMR 7.12 (Source Registration), 7.71 (GHG), 4.03 (fee classes).

**Data-tab columns:** `SR Status, AQ ID#, Facility Name, Town, MassDEP Region, Current Class, What to
File, File By, SR Schedule, GHG Schedule, Current Class Since, Current Class Description, Facility
Type, Site Account #, Street Address, Street Address 2, Town2, State, Zip Code, AQ Emissions Contact:
First Name, AQ Emissions Contact: Last Name`.

**SR Status codes (ReadMe tab):**
- `YOR` — year of record (calendar year of the report's data).
- `ACP` — reports annually due to a permit condition.
- `Formerly OP For Prior CY` — had an Operating Permit during part of the reporting year; must report.
- `Closed OP` / `Closed GHG` / `Closed-GHG` — facility closed during the year; must report SRGHG/GHG.
- `GHG` — greenhouse-gas emissions reporter.
- `NES (NESHAP)` — emits an air contaminant subject to a NESHAP → reports annually.
- `NO2` — emitted ≥25 tons NO2.
- `OP` — has an Operating Permit → reports annually.
- `PB` — emitted ≥0.5 tons Pb.
- `RES` — has a Restricted Emissions Status permit → reports annually.
- `VOC` — emitted ≥25 tons VOC.

**Current Class codes (`Current Class Description`, verbatim):**
- **Operating Permit** — `OP2…OP38` = "AQ OPERATING PERMIT FEE $<n>000" (suffix = annual compliance
  fee in $thousands; e.g. OP3 = $3,000, OP38 = $38,000; fractional OP5.5/OP7.5 exist) — fee per 310 CMR 4.03.
- **Synthetic Minor** (restricted PTE): `SM25` = 7.00 Restr PTE ≤25% OP (Grp 3); `SM50` = ≤50% & >25%
  OP (Grp 2); `SM79-7` = 7.00 Restr PTE <80% & >50% OP (Grp 1); `SM80-7` = 7.00 Restr PTE <OP & ≥80%
  OP (Grp 1); `SM79-R` / `SM80-R` = same bands but **RES**-restricted PTE.
- **Natural Minor:** `NM25` = PTE/Restr PTE ≤25% OP (Grp 3); `NM50` = ≤50% & >25% OP (Grp 2); `NM99` =
  PTE <OP & >50% OP (Grp 1); `NMNOSR` = Source Registration Not Required.
- `BLW-AQ` = Below AQ Regulated Thresholds.

("OP" = the major-source / Operating-Permit threshold the % bands reference; PTE = Potential To Emit.)

---

# F. MEPA — `search-mepa` (no official field dictionary)
The eMonitor API has no published schema. Authoritative definitions are in **301 CMR 11.00**:
- **§ 11.02 Definitions** — glossary (Threshold, Agency Action, etc.).
- **§ 11.03 Review Thresholds** — the threshold catalog by category, split (a) mandatory EIR vs (b)
  ENF + discretionary review. Maps to the API's `thresholds[]`.
- **Submittal types** (API `submittalType`): `ENF`, `EENF`, `EIR`/`DEIR`/`FEIR`, `NPC`, Secretary's
  Certificate, Emergency ENF — enumerated in the MEPA e-Filing Portal User's Guide; defined
  procedurally in §§ 11.05–11.10.
- **eeaNo** — project file number, assigned at ENF stage; all later submittals attach to it.
Full text: `https://www.sec.state.ma.us/reg_pub/pdf/300/301011.pdf`.

# G. CSO / SSO — `search-cso` (no official field dictionary)
No published column dictionary. Authoritative definitions in **314 CMR 16.00** (M.G.L. c.21 §27 / 2021
Sewage Notification Act): § 16.02 definitions (CSO, SSO, blended/partially-treated wastewater); § 16.04
events requiring notification (= the `EventType` universe); § 16.07 the electronic Data System.
Practical field meaning: the *Sewage Notification Data System Instructions* PDFs +
*Reportable Events Flowchart* on `https://www.mass.gov/how-to/sewage-notification-system`.

---

# Federal fallback dictionaries (authoritative where MA reports upward)
EPA ECHO downloads — each has a Data Element Dictionary at `https://echo.epa.gov/tools/data-downloads/`:
**FRS** (facilities/cross-IDs), **SDWA** + EPA **SDWIS** (drinking water), **ICIS-NPDES** (NPDES),
**ICIS-Air** (compliance evaluations/inspections), **ICIS-FE&C** (enforcement-action types).

# Bundled files (`../data/dictionaries/`)
`eea-data-portal-general-query-search-faqs.pdf` · `understanding-waste-site-release-lookup.pdf` ·
`pfas-npdes-wastewater-field-definitions.xlsx` · `pfas-residuals-field-definitions.xlsx` ·
`fgdc-massdep-major-facilities.xml` · `fgdc-massdep-tier-classified-21e-C21E_PT.shp.xml` (+ `_LDT`,
`_USL`). SR-GHG dictionary is inside `../data/sr-ghg-filers-list.xlsx`. See `README.md` for source URLs.

# Gaps
No machine schema for any of the 6 REST APIs. **MEPA** & **CSO** have no field-level dict (regulation
only). **Enforcement-type** code list isn't a fetchable file → ICIS-FE&C. **PFAS Groundwater
Discharge** report type has no field-def file. Waste-site bulk `.dbf` ships without its README.
