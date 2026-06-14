# Bundled official data-dictionary artifacts

Offline copies of the authoritative MA-state (and one set of GIS) data-dictionary documents, pulled
2026-06-13. See `../../references/DATA_DICTIONARIES.md` for the full per-endpoint inventory, the
regulation cites for each code list, and the federal (EPA ECHO/SDWIS/ICIS/FRS) fallbacks.

All source URLs are Akamai-protected → refresh with **`wget`** + a generic UA, never curl/requests.

| File | Documents | Source URL |
|------|-----------|------------|
| `eea-data-portal-general-query-search-faqs.pdf` | DataLake permit/facility/inspection/enforcement/asbestos field defs + the master MassDEP Program/Permit-type code list (≈pp.46–57) | `https://eeaonline.eea.state.ma.us/Portal/documents/General%20Query%20Search%20FAQs.pdf` |
| `understanding-waste-site-release-lookup.pdf` | WasteSite/21E: RTN, Reporting Category, Phase, Chemical Type, full Compliance-Status & RAO-Class code lists | `https://www.mass.gov/doc/understanding-the-waste-siterelease-look-up-search-results/download` |
| `pfas-npdes-wastewater-field-definitions.xlsx` | DataLake `npdes` PFAS Wastewater — per-field Description / Required / Type / Valid Values + ref tabs | `https://www.mass.gov/doc/pfas-npdes-wastewater-field-definitions-for-labs/download` |
| `pfas-residuals-field-definitions.xlsx` | DataLake `npdes` PFAS Residuals — same structure | `https://www.mass.gov/doc/pfas-residuals-field-definitions-for-labs/download` |
| `fgdc-massdep-major-facilities.xml` | MassGIS `BWPMAJOR_PT` FGDC: FAC_ID/NAME/ADDRESS/TOWN/REGION + EPA cross-IDs HW_ID, SSEIS_ID | AGOL `…/MassDEP_BAW_Major_Facilities__2023_update/FeatureServer/0/metadata?format=fgdc&f=xml` |
| `fgdc-massdep-tier-classified-21e-C21E_PT.shp.xml` | MassGIS `C21E_PT` FGDC: 21E tier-classified sites (RTN/NAME/ADDRESS/TOWN/REGION/STATUS/SITE_INFO) | `download.massgis.digital.mass.gov/shapefiles/state/c21e_pt.zip` → `C21E_PT.shp.xml` |
| `fgdc-massdep-tier-classified-21e-C21E_PT_LDT.dbf.xml` | C21E location-documentation table FGDC | (same zip) |
| `fgdc-massdep-tier-classified-21e-C21E_PT_USL.dbf.xml` | C21E unlocated-sites table FGDC | (same zip) |
| `permit_program_types.csv` | All 274 MassDEP/MDAR permit/program-type codes (`program,code,description,agency`) — the `Program`/`Permit Type` controlled vocabulary; keyed from the FAQ PDF pp.46–57 | (derived from the FAQ PDF above) |

The **SR-GHG** dictionary is not duplicated here — it lives inside `../sr-ghg-filers-list.xlsx`
(`ReadMe` tab + `Current Class Description` column).
