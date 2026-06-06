#!/usr/bin/env python3
"""
mass_env.py — Massachusetts environmental-permitting public-data client + CLI.

Queries two public, no-login MassDEP/EEA portals (whose REST/JSON APIs are hidden
behind JavaScript SPAs) plus the MassDEP Source Registration / Greenhouse Gas
filers spreadsheet:

  1. MassDEP "ePlace"  — air-quality plan approvals & all DEP/DCR/MDAR permit
     records.  Base: https://eplace.eea.mass.gov/EEAPublicAppAPI  (no auth).
  2. MEPA eMonitor     — environmental review filings (ENF / EIR / NPC /
     Secretary's Certificates).  AWS API Gateway with a *public* x-api-key that
     the client re-discovers from the SPA's runtime config each run.
  3. SR-GHG filers     — annual Source Registration / GHG filer roster (xlsx,
     bundled snapshot; refresh via wget because mass.gov bot-blocks curl/requests).

Read-only: search + detail + document download only.  Polite by default:
generic (non-identifying) User-Agent, <=1 request/second throttle, retries with
exponential backoff.  No API keys/bundle hashes are hard-coded — base URLs and
the MEPA key are re-scraped from the live config at runtime.

Usage examples:
    python mass_env.py search-permits --city Worcester --permit-types AQ
    python mass_env.py permit-detail 26CAP-00000-002QR --checkbox-code TR_CPA_FUEL
    python mass_env.py massdep-download 1719226 -o plan_approval.pdf
    python mass_env.py search-mepa --eea-no 3247
    python mass_env.py search-mepa --project-name "Wastewater" --town Worcester
    python mass_env.py mepa-attachments <submittal-id>
    python mass_env.py mepa-download <file-service-id> -o filing.pdf
    python mass_env.py sr-ghg --town WORCESTER
    python mass_env.py info
"""

import argparse
import csv
import io
import json
import os
import subprocess
import sys
import time

import requests

# ─── Constants ────────────────────────────────────────────────────────────────

# Generic, non-identifying User-Agent (see ~/.claude/CLAUDE.md: never put the
# user's email/name in outbound headers without permission).
USER_AGENT = "Mozilla/5.0 (compatible; research-client/1.0)"

# MassDEP ePlace
EPLACE_APP = "https://eplace.eea.mass.gov/EEAPublicApp"
EPLACE_CONFIG_URL = f"{EPLACE_APP}/js/appConfig.json"
EPLACE_TOOLTIPS_URL = f"{EPLACE_APP}/js/tooltips.json"
EPLACE_REFERER = f"{EPLACE_APP}/"

# MEPA eMonitor SPA runtime config (holds API base + public api keys)
MEPA_APP = "https://eeaonline.eea.state.ma.us/EEA/MEPA-eMonitor"
MEPA_CONFIG_URL = f"{MEPA_APP}/assets/config/config.json"
MEPA_STATE_ID_MA = 22  # Massachusetts StateId for the postal town lookup

# SR-GHG filers spreadsheet
SR_GHG_URL = "https://www.mass.gov/doc/sr-ghg-filers-list/download"
SR_GHG_BUNDLED = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "data", "sr-ghg-filers-list.xlsx")

# MassDEP authorization groups: AccelaType -> AccelaGroup (the search needs both).
PERMIT_GROUPS = {
    # DEP — Department of Environmental Protection
    "AQ": "DEP",   # Air quality (plan approvals, incl. on-site combustion)
    "DW": "DEP",   # Drinking water
    "HW": "DEP",   # Hazardous waste
    "SW": "DEP",   # Solid waste
    "TUR": "DEP",  # Toxics use reduction planners
    "WM": "DEP",   # Watershed Management & NPDES
    "WW": "DEP",   # Wetlands & Waterways
    "WP": "DEP",   # Water Pollution
    "LES": "DEP",  # Laboratory Certification
    # DCR — Department of Conservation and Recreation
    "SUP": "DCR",  # Special Use Permits
    "CAP": "DCR",  # Construction and Vehicle Access Permits
    # MDAR — Department of Agricultural Resources
    "Pesticide": "MDAR",
    "Plant Industries": "MDAR",
}

# Valid MassDEP authorization-status values (accelaText).
MASSDEP_STATUSES = [
    "In Review", "Public Comment Pending",  # IN PROGRESS
    "Approved", "Denied", "Withdrawn",      # DECISION RENDERED
]

MAX_RETRIES = 3
TIMEOUT = 90
MIN_INTERVAL = 1.0  # seconds between requests (politeness throttle)


# ─── HTTP client ──────────────────────────────────────────────────────────────


class HttpClient:
    """requests.Session wrapper with throttle + retry/backoff + generic UA."""

    def __init__(self, min_interval=MIN_INTERVAL, verbose=False):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.min_interval = min_interval
        self.verbose = verbose
        self._last = 0.0

    def _throttle(self):
        elapsed = time.time() - self._last
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last = time.time()

    def request(self, method, url, *, headers=None, json_body=None, params=None,
                stream=False, allow_redirects=True):
        for attempt in range(MAX_RETRIES):
            self._throttle()
            try:
                if self.verbose:
                    print(f"  {method} {url}", file=sys.stderr)
                resp = self.session.request(
                    method, url, headers=headers, json=json_body, params=params,
                    timeout=TIMEOUT, stream=stream, allow_redirects=allow_redirects,
                )
                if resp.status_code in (429, 500, 502, 503, 504) and attempt < MAX_RETRIES - 1:
                    wait = 2 ** (attempt + 1)
                    print(f"  Retrying in {wait}s (HTTP {resp.status_code})...", file=sys.stderr)
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp
            except requests.exceptions.RequestException as e:
                if attempt < MAX_RETRIES - 1:
                    wait = 2 ** (attempt + 1)
                    print(f"  Retrying in {wait}s ({e})...", file=sys.stderr)
                    time.sleep(wait)
                    continue
                raise

    def get_json(self, url, **kw):
        return self.request("GET", url, **kw).json()

    def post_json(self, url, json_body, **kw):
        return self.request("POST", url, json_body=json_body, **kw).json()


# ─── Main client ──────────────────────────────────────────────────────────────


class MassEnvClient:
    """Client for MassDEP ePlace + MEPA eMonitor + SR-GHG filers list."""

    def __init__(self, verbose=False):
        self.http = HttpClient(verbose=verbose)
        self._eplace_cfg = None
        self._mepa_cfg = None
        self._mepa_towns = None
        self._tooltips = None

    # ---- config discovery (re-scraped at runtime, never hard-coded) ----

    def eplace_config(self):
        if self._eplace_cfg is None:
            # appConfig.json is served with a UTF-8 BOM; requests .json() handles it.
            txt = self.http.request("GET", EPLACE_CONFIG_URL).content.decode("utf-8-sig")
            self._eplace_cfg = json.loads(txt)
        return self._eplace_cfg

    def eplace_api(self):
        return self.eplace_config()["SEARCH_API_URL"].rstrip("/")

    def mepa_config(self):
        if self._mepa_cfg is None:
            txt = self.http.request("GET", MEPA_CONFIG_URL).content.decode("utf-8-sig")
            self._mepa_cfg = json.loads(txt)["ApiConfig"]
        return self._mepa_cfg

    def _mepa_get(self, endpoint_key, path, **kw):
        cfg = self.mepa_config()
        base = cfg[endpoint_key].rstrip("/") + "/"
        key = {"API_ENDPOINT": "Api_Key",
               "POSTAL_API_ENDPOINT": "POSTAL_API_KEY"}[endpoint_key]
        headers = {"x-api-key": cfg[key], "Referer": f"{MEPA_APP}/search"}
        headers.update(kw.pop("headers", None) or {})
        return self.http.get_json(base + path, headers=headers, **kw)

    # ============================== MassDEP ePlace =============================

    def search_massdep_permits(self, *, city=None, address=None, zip_code=None,
                               applicant=None, facility=None, application_id=None,
                               permit_types=None, statuses=None,
                               from_date=None, to_date=None):
        """Search MassDEP ePlace permit applications/authorizations.

        permit_types: list of AccelaType codes (e.g. ["AQ"]) or full dicts
                      {"AccelaGroup","AccelaType"[,"AccelaSubType"]}.
        statuses:     subset of MASSDEP_STATUSES.
        from_date/to_date: "YYYY-MM-DD" (or None).
        Returns the list of record dicts (the response "List").
        """
        auth_types = []
        for pt in (permit_types or []):
            if isinstance(pt, dict):
                auth_types.append(pt)
            else:
                grp = PERMIT_GROUPS.get(pt)
                if not grp:
                    raise ValueError(f"Unknown permit type {pt!r}; "
                                     f"known: {sorted(PERMIT_GROUPS)}")
                auth_types.append({"AccelaGroup": grp, "AccelaType": pt,
                                   "AccelaSubType": None})
        criteria = {
            "FacilityName": facility or "",
            "ApplicantName": applicant or "",
            "ApplicationId": application_id or "",
            "AuthorizationStatuses": statuses or [],
            "AuthorizationTypes": auth_types,
            "AddressDetails": {
                "AddressLine1": address or "",
                "State": "MA",
                "City": city or "",
                "Country": "US",
                "ZipCode": zip_code or "",
            },
            "FromDate": _iso(from_date),
            "ToDate": _iso(to_date),
            "OperationType": 0,
            "MaxRecords": False,
        }
        url = self.eplace_api() + "/api/Search/Applications"
        data = self.http.post_json(url, criteria, headers={"Referer": EPLACE_REFERER})
        return data.get("List") or []

    def get_massdep_record(self, record_id, contact_id="", check_box_code=""):
        """Fetch full detail for a MassDEP record, including ApplicationDocuments.

        record_id / contact_id / check_box_code come from a search result row
        (RecordId / ContactId / CheckBoxCode)."""
        url = self.eplace_api() + "/api/Application/Detail"
        body = {"RecordId": record_id, "ContactId": contact_id,
                "CheckBoxCode": check_box_code}
        return self.http.post_json(url, body, headers={"Referer": EPLACE_REFERER})

    def download_massdep_document(self, doc_id, dest):
        """Download a MassDEP document by DocId (from ApplicationDocuments)."""
        url = self.eplace_api() + "/api/Application/GetS3Document"
        resp = self.http.request("GET", url, params={"docID": doc_id},
                                 headers={"Referer": EPLACE_REFERER}, stream=True)
        return _write_stream(resp, dest)

    def massdep_permit_types(self):
        """Return permit-code groups (from tooltips.json), e.g. {'AQ': [...]}."""
        if self._tooltips is None:
            self._tooltips = self.http.get_json(EPLACE_TOOLTIPS_URL)
        out = {}
        for k, v in self._tooltips.items():
            if k.startswith("searchcriteria-cateogry-"):
                out[k.replace("searchcriteria-cateogry-", "")] = \
                    [c.strip() for c in v.split(",")]
        return out

    # ============================== MEPA eMonitor =============================

    def search_mepa(self, *, proponent=None, project_name=None, project_number=None,
                    eea_no=None, project_id=None, submittal_type=None, town=None,
                    from_date=None, to_date=None, page=1):
        """Search MEPA projects. `project_name` (free text), `town`, `eea_no`/
        `project_number` and date range are reliable filters. `town` may be a name
        (resolved to TownId) or a numeric TownId. Dates are "M/D/YYYY".
        Returns {totalRecords, currentPage, pageSize, list}.

        NOTE: the public API's `ProponentName` filter is non-functional — proponent/
        developer names live in a separate contacts system, so a proponent search
        returns the global total with an empty list. Prefer project_name/town/eea_no.
        The CLI flags this (totalRecords>0 but empty list = an ignored filter).
        """
        params = {
            "isExactAgency": "false", "isExactAction": "false",
            "isExactThresholdCat": "false", "currentPage": page,
        }
        if proponent:
            params["ProponentName"] = proponent
        if project_name:
            params["ProjectName"] = project_name
        if project_number:
            params["ProjectNumber"] = project_number
        if eea_no:
            params["ProjectNumber"] = eea_no  # eeaNo is the public file number
        if project_id:
            params["ProjectId"] = project_id
        if submittal_type:
            params["SubmittalType"] = submittal_type
        if town is not None:
            params["City"] = town if str(town).isdigit() else self.mepa_town_id(town)
        if from_date:
            params["SubmittalDateFrom"] = _usdate(from_date)
        if to_date:
            params["SubmittalDateTo"] = _usdate(to_date)
        return self._mepa_get("API_ENDPOINT", "Project/search", params=params)

    def get_mepa_project(self, project_id):
        """Fetch full MEPA project detail by projectId (GUID)."""
        return self._mepa_get("API_ENDPOINT", f"Project/{project_id}")

    def mepa_submittal_attachments(self, submittal_id):
        """List attachments for a MEPA submittal (returns fileServiceId etc.)."""
        return self._mepa_get("API_ENDPOINT",
                              f"Attachment/ListBySubmitalId/{submittal_id}")

    def download_mepa_attachment(self, file_service_id, dest):
        """Download a MEPA attachment by its fileServiceId.

        Flow: GetEncryptedTokens -> FileService file/MEPA/{id} (302 to a presigned
        S3 URL) -> fetch S3 plainly (the S3 leg must NOT carry the auth headers,
        or S3 rejects 'two auth mechanisms')."""
        cfg = self.mepa_config()
        tokens = self._mepa_get("API_ENDPOINT", "Attachment/GetEncryptedTokens")
        fs_url = cfg["ATTACHMENT_API_ENDPOINT"].rstrip("/") + "/file/MEPA/" + file_service_id
        headers = {
            "x-api-key": cfg["ATTACHMENT_API_KEY"],
            "Authorization": cfg["Authorization"],
            "appToken": tokens["encryptedAppToken"],
            "dataToken": tokens["appDataReadToken"],
            "authToken": tokens["encryptedAuthToken"],
            "Referer": f"{MEPA_APP}/search",
        }
        resp = self.http.request("GET", fs_url, headers=headers,
                                 allow_redirects=False)
        if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
            s3_url = resp.headers["Location"]
            resp = self.http.request("GET", s3_url, stream=True)  # plain, no auth
        return _write_stream(resp, dest)

    def mepa_towns(self):
        """All MA towns: list of {TownId, TownName, CountyId, CountyName}."""
        if self._mepa_towns is None:
            self._mepa_towns = self._mepa_get(
                "POSTAL_API_ENDPOINT", f"Lookup/towns/byState/{MEPA_STATE_ID_MA}")
        return self._mepa_towns

    def mepa_town_id(self, name):
        """Resolve a town name (case-insensitive) to its numeric TownId."""
        name = name.strip().upper()
        for t in self.mepa_towns():
            if (t.get("TownName") or "").upper() == name:
                return t["TownId"]
        raise ValueError(f"Town {name!r} not found in MA town list")

    def mepa_project_types(self):
        """MEPA project-type lookup list."""
        return self._mepa_get("API_ENDPOINT", "ProjectType")

    # ================================ SR-GHG =================================

    def load_sr_ghg_filers(self, path=None, refresh=False, town=None, facility=None):
        """Load the SR-GHG filers roster (xlsx) as a list of row dicts.

        path:    explicit xlsx path (default: bundled snapshot).
        refresh: re-download a fresh copy via wget (mass.gov Akamai-blocks
                 curl/requests; wget works) before reading.
        town/facility: optional case-insensitive substring filters.
        """
        import openpyxl
        path = path or SR_GHG_BUNDLED
        if refresh:
            path = _wget_download(SR_GHG_URL, path)
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = next(s for s in wb.worksheets if s.title.lower().startswith("srghg"))
        rows = ws.iter_rows(values_only=True)
        header = [str(h).strip() if h is not None else "" for h in next(rows)]
        out = []
        for r in rows:
            if not any(c not in (None, "") for c in r):
                continue
            rec = {header[i]: r[i] for i in range(min(len(header), len(r)))}
            out.append(rec)
        if town:
            out = [r for r in out if town.upper() in str(r.get("Town", "")).upper()]
        if facility:
            out = [r for r in out
                   if facility.upper() in str(r.get("Facility Name", "")).upper()]
        return out


# ─── helpers ──────────────────────────────────────────────────────────────────


def _iso(d):
    """'YYYY-MM-DD' -> 'YYYY-MM-DDT00:00:00' for the ePlace date fields, else None."""
    if not d:
        return None
    return d if "T" in d else d + "T00:00:00"


def _usdate(d):
    """'YYYY-MM-DD' -> 'M/D/YYYY' for the MEPA date params; pass through otherwise."""
    if not d:
        return d
    try:
        y, m, day = d.split("-")
        return f"{int(m)}/{int(day)}/{int(y)}"
    except ValueError:
        return d


def _write_stream(resp, dest):
    """Stream a response body to dest; return (path, bytes_written)."""
    total = 0
    with open(dest, "wb") as fh:
        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                fh.write(chunk)
                total += len(chunk)
    return dest, total


def _wget_download(url, dest):
    """Download `url` to `dest` via wget (follows redirects; bypasses Akamai)."""
    tmp = dest + ".new"
    cmd = ["wget", "-q", "--timeout=120", "-U", USER_AGENT, "-O", tmp, url]
    subprocess.run(cmd, check=True)
    os.replace(tmp, dest)
    return dest


# ─── output formatting ─────────────────────────────────────────────────────────


def _emit(rows, fmt, columns, output=None):
    """Render a list of dicts as table/csv/json (or vertical for a single dict)."""
    if isinstance(rows, dict):
        rows = [rows]
    if fmt == "json":
        text = json.dumps(rows, indent=2, default=str)
    elif fmt == "csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(columns)
        for r in rows:
            w.writerow([_flat(r.get(c, "")) for c in columns])
        text = buf.getvalue()
    else:  # table
        widths = {c: max(len(c), *(len(_flat(r.get(c, ""))) for r in rows)) if rows else len(c)
                  for c in columns}
        lines = [" | ".join(c.ljust(widths[c]) for c in columns),
                 "-+-".join("-" * widths[c] for c in columns)]
        for r in rows:
            lines.append(" | ".join(_flat(r.get(c, "")).ljust(widths[c]) for c in columns))
        text = "\n".join(lines)
    if output:
        with open(output, "w") as fh:
            fh.write(text)
        print(f"Wrote {len(rows)} row(s) -> {output}", file=sys.stderr)
    else:
        print(text)


def _dump(obj, output=None):
    """Write a single object as raw, indented JSON."""
    text = json.dumps(obj, indent=2, default=str)
    if output:
        with open(output, "w") as fh:
            fh.write(text)
        print(f"Wrote -> {output}", file=sys.stderr)
    else:
        print(text)


def _flat(v):
    if v is None:
        return ""
    if isinstance(v, (dict, list)):
        return json.dumps(v, default=str)
    return str(v)


def _addr(rec):
    a = rec.get("ApplicantAddress") or {}
    return ", ".join(p for p in [a.get("AddressLine1"), a.get("City"),
                                 a.get("ZipCode")] if p)


# ─── CLI ────────────────────────────────────────────────────────────────────────


def cmd_search_permits(c, args):
    rows = c.search_massdep_permits(
        city=args.city, address=args.address, zip_code=args.zip,
        applicant=args.applicant, facility=args.facility,
        application_id=args.application_id,
        permit_types=args.permit_types.split(",") if args.permit_types else None,
        statuses=args.statuses.split(",") if args.statuses else None,
        from_date=getattr(args, "from"), to_date=args.to)
    print(f"{len(rows)} record(s)", file=sys.stderr)
    for r in rows:
        r["Address"] = _addr(r)
    _emit(rows, args.format,
          ["ApplicationId", "RecordId", "ApplicantName", "RecordType",
           "RecordTypeAlias", "Status", "FiledDate", "Address", "CheckBoxCode"],
          args.output)


def cmd_permit_detail(c, args):
    d = c.get_massdep_record(args.record_id, args.contact_id or "",
                             args.checkbox_code or "")
    if args.format == "json":
        _dump(d, args.output)
        return
    docs = d.get("ApplicationDocuments") or []
    print(f"Record: {args.record_id}  Status: "
          f"{(d.get('RecordDetail') or {}).get('Status')}")
    print(f"Documents: {len(docs)}")
    _emit(docs, args.format, ["DocId", "Name", "Type", "Category", "DocDate"],
          args.output)


def cmd_massdep_download(c, args):
    dest, n = c.download_massdep_document(args.doc_id, args.output or f"{args.doc_id}.pdf")
    print(f"Downloaded {n} bytes -> {dest}")


def cmd_search_mepa(c, args):
    res = c.search_mepa(
        proponent=args.proponent, project_name=args.project_name,
        project_number=args.project_number, eea_no=args.eea_no,
        submittal_type=args.submittal_type, town=args.town,
        from_date=getattr(args, "from"), to_date=args.to, page=args.page)
    projects = res.get("list") or []
    total = res.get("totalRecords") or 0
    print(f"{total} project(s) total; page {res.get('currentPage')}", file=sys.stderr)
    if total > 0 and not projects:
        print("WARNING: totalRecords>0 but no rows returned — a filter was ignored "
              "server-side (the MEPA API's ProponentName filter is non-functional). "
              "Use --project-name / --town / --eea-no instead.", file=sys.stderr)
    flat = []
    for p in projects:
        subs = p.get("submittals") or []
        types = ",".join(sorted({s.get("submittalType") for s in subs
                                 if s.get("submittalType")}))
        flat.append({"eeaNo": p.get("eeaNo"), "projectName": p.get("projectName"),
                     "location": p.get("location"), "submittalTypes": types,
                     "projectId": p.get("projectId")})
    _emit(flat, args.format,
          ["eeaNo", "projectName", "location", "submittalTypes", "projectId"],
          args.output)


def cmd_mepa_project(c, args):
    _dump(c.get_mepa_project(args.project_id), args.output)


def cmd_mepa_attachments(c, args):
    atts = c.mepa_submittal_attachments(args.submittal_id)
    print(f"{len(atts)} attachment(s)", file=sys.stderr)
    _emit(atts, args.format,
          ["fileServiceId", "fileName", "size", "uploadedDate", "attachmentId"],
          args.output)


def cmd_mepa_download(c, args):
    dest, n = c.download_mepa_attachment(args.file_service_id,
                                         args.output or f"{args.file_service_id}")
    print(f"Downloaded {n} bytes -> {dest}")


def cmd_sr_ghg(c, args):
    rows = c.load_sr_ghg_filers(path=args.path, refresh=args.refresh,
                                town=args.town, facility=args.facility)
    print(f"{len(rows)} filer(s)", file=sys.stderr)
    _emit(rows, args.format,
          ["AQ ID#", "Facility Name", "Town", "MassDEP Region", "Current Class",
           "What to File", "File By", "Facility Type"], args.output)


def cmd_info(c, args):
    info = {
        "eplace_api": c.eplace_api(),
        "mepa_api": c.mepa_config().get("API_ENDPOINT"),
        "mepa_attachment_api": c.mepa_config().get("ATTACHMENT_API_ENDPOINT"),
        "mepa_postal_api": c.mepa_config().get("POSTAL_API_ENDPOINT"),
        "massdep_permit_groups": sorted(PERMIT_GROUPS),
        "massdep_statuses": MASSDEP_STATUSES,
        "sr_ghg_bundled": SR_GHG_BUNDLED,
    }
    print(json.dumps(info, indent=2))


def build_parser():
    p = argparse.ArgumentParser(
        description="Massachusetts environmental-permitting public-data client "
                    "(MassDEP ePlace + MEPA eMonitor + SR-GHG filers).",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("-v", "--verbose", action="store_true", help="log requests to stderr")
    sub = p.add_subparsers(dest="command", required=True)

    def add_fmt(sp, default="table"):
        sp.add_argument("-f", "--format", choices=["table", "csv", "json"], default=default)
        sp.add_argument("-o", "--output", help="write to file instead of stdout")

    sp = sub.add_parser("search-permits", help="Search MassDEP permits/approvals")
    sp.add_argument("--city")
    sp.add_argument("--address")
    sp.add_argument("--zip")
    sp.add_argument("--applicant", help="individual applicant/licensee name")
    sp.add_argument("--facility", help="facility/site/park name")
    sp.add_argument("--application-id")
    sp.add_argument("--permit-types", help="comma list of AccelaType codes, e.g. AQ,WW")
    sp.add_argument("--statuses", help="comma list, e.g. 'In Review,Approved'")
    sp.add_argument("--from", help="filed-date from (YYYY-MM-DD)")
    sp.add_argument("--to", help="filed-date to (YYYY-MM-DD)")
    add_fmt(sp)
    sp.set_defaults(func=cmd_search_permits)

    sp = sub.add_parser("permit-detail", help="MassDEP record detail + documents")
    sp.add_argument("record_id", help="RecordId from a search result")
    sp.add_argument("--contact-id", default="")
    sp.add_argument("--checkbox-code", default="", help="CheckBoxCode from search result")
    add_fmt(sp)
    sp.set_defaults(func=cmd_permit_detail)

    sp = sub.add_parser("massdep-download", help="Download a MassDEP document by DocId")
    sp.add_argument("doc_id")
    sp.add_argument("-o", "--output")
    sp.set_defaults(func=cmd_massdep_download)

    sp = sub.add_parser("search-mepa", help="Search MEPA projects (ENF/EIR/NPC...)")
    sp.add_argument("--proponent", help="proponent/developer name (free text)")
    sp.add_argument("--project-name", help="project name (free text)")
    sp.add_argument("--project-number")
    sp.add_argument("--eea-no", help="EEA/MEPA file number")
    sp.add_argument("--submittal-type", help="submittal type id")
    sp.add_argument("--town", help="town name or numeric TownId")
    sp.add_argument("--from", help="submittal date from (YYYY-MM-DD)")
    sp.add_argument("--to", help="submittal date to (YYYY-MM-DD)")
    sp.add_argument("--page", type=int, default=1)
    add_fmt(sp)
    sp.set_defaults(func=cmd_search_mepa)

    sp = sub.add_parser("mepa-project", help="MEPA project detail by projectId (JSON)")
    sp.add_argument("project_id")
    sp.add_argument("-o", "--output")
    sp.set_defaults(func=cmd_mepa_project)

    sp = sub.add_parser("mepa-attachments", help="List a MEPA submittal's attachments")
    sp.add_argument("submittal_id")
    add_fmt(sp)
    sp.set_defaults(func=cmd_mepa_attachments)

    sp = sub.add_parser("mepa-download", help="Download a MEPA attachment by fileServiceId")
    sp.add_argument("file_service_id")
    sp.add_argument("-o", "--output")
    sp.set_defaults(func=cmd_mepa_download)

    sp = sub.add_parser("sr-ghg", help="Query the SR-GHG filers roster (xlsx)")
    sp.add_argument("--town", help="filter by town (substring)")
    sp.add_argument("--facility", help="filter by facility name (substring)")
    sp.add_argument("--path", help="explicit xlsx path (default: bundled snapshot)")
    sp.add_argument("--refresh", action="store_true", help="re-download via wget first")
    add_fmt(sp)
    sp.set_defaults(func=cmd_sr_ghg)

    sp = sub.add_parser("info", help="Show discovered API bases + reference lists")
    sp.set_defaults(func=cmd_info)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    client = MassEnvClient(verbose=args.verbose)
    try:
        args.func(client, args)
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}", file=sys.stderr)
        sys.exit(1)
    except (ValueError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
