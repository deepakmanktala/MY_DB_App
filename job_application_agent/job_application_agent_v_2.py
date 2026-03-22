"""
Job Application Agent V2

What this app does
- Lets you define a payments/EMV/POS-focused profile
- Ingests jobs from JSON/CSV files and optional RSS/API connectors
- Normalizes and scores jobs for your profile
- Tracks jobs in SQLite
- Generates outreach/apply notes and tailored resume bullets
- Runs a Streamlit UI for search, shortlist, pipeline tracking, and exports

Important
- This is intentionally HUMAN-IN-THE-LOOP.
- It does NOT mass-apply, bypass CAPTCHAs, evade MFA, or auto-submit on job platforms.
- For sites without public APIs or where automation is restricted, use exports/manual imports/browser bookmarks.

Run
    pip install streamlit pandas requests feedparser python-dateutil
    streamlit run job_application_agent_v2.py

Optional env vars
    JOB_AGENT_DB=job_agent_v2.db
    REMOTIVE_API=https://remotive.com/api/remote-jobs
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sqlite3
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote_plus

import pandas as pd
import requests
import streamlit as st
from dateutil import parser as dt_parser

try:
    import feedparser
except Exception:  # pragma: no cover
    feedparser = None


APP_TITLE = "Job Application Agent V2"
DB_PATH = Path(os.getenv("JOB_AGENT_DB", "job_agent_v2.db"))
DATA_DIR = Path("job_agent_data")
DATA_DIR.mkdir(exist_ok=True)
PROFILE_FILE = DATA_DIR / "profile_v2.json"
EXPORT_DIR = DATA_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)

SUPPORTED_SOURCES = [
    "LinkedIn",
    "Glassdoor",
    "HackerRank Jobs",
    "Indeed",
    "Naukri",
    "Monster",
    "Shine",
    "Naukri Gulf",
    "Remote / API / RSS",
    "Manual Import",
]

PAYMENTS_KEYWORDS = [
    "emv",
    "payment terminal",
    "payment terminals",
    "payment gateway",
    "payment gateways",
    "point of interaction",
    "poi",
    "pos",
    "point of sale",
    "softpos",
    "tap to phone",
    "contactless",
    "visa",
    "mastercard",
    "rupay",
    "amex",
    "discover",
    "iso 8583",
    "pci",
    "pci dss",
    "sred",
    "dukpt",
    "acquirer",
    "issuer",
    "card present",
    "card not present",
    "cp",
    "cnp",
    "merchant acquiring",
    "payment orchestration",
    "switching",
    "authorization",
    "settlement",
    "host integration",
    "terminal management",
    "verifone",
    "ingenico",
    "pax",
    "worldpay",
    "fiserv",
    "adyen",
    "checkout",
    "cybersource",
    "gateway",
    "tokenization",
    "fraud",
    "chargeback",
]

TARGET_TITLES_DEFAULT = [
    "Engineering Manager",
    "QA Manager",
    "Automation Manager",
    "Technical Program Manager",
    "Technical Manager",
    "Solution Architect",
    "Principal QA",
    "Senior Engineering Manager",
    "Payments Architect",
    "POS Architect",
]

DEFAULT_LOCATIONS = [
    "India",
    "Bengaluru",
    "Bangalore",
    "Dubai",
    "Singapore",
    "United States",
    "USA",
    "United Kingdom",
    "UK",
    "Netherlands",
    "Europe",
    "Canada",
    "Australia",
    "Middle East",
    "Remote",
]

REMOTE_SITES = {
    "Remotive": os.getenv("REMOTIVE_API", "https://remotive.com/api/remote-jobs"),
}


@dataclass
class CandidateProfile:
    name: str = "Deepak Manktala"
    email: str = ""
    phone: str = ""
    years_experience: int = 15
    notice_period: str = "Available with LWD / notice-period context as applicable"
    current_location: str = "India"
    target_titles: List[str] = field(default_factory=lambda: TARGET_TITLES_DEFAULT.copy())
    preferred_locations: List[str] = field(default_factory=lambda: DEFAULT_LOCATIONS.copy())
    core_keywords: List[str] = field(default_factory=lambda: PAYMENTS_KEYWORDS.copy())
    must_have_keywords: List[str] = field(
        default_factory=lambda: [
            "emv",
            "pos",
            "payment",
            "terminal",
            "gateway",
            "qa",
            "automation",
            "architecture",
            "program management",
        ]
    )
    nice_to_have_keywords: List[str] = field(
        default_factory=lambda: [
            "android",
            "microservices",
            "spring boot",
            "rag",
            "llm",
            "pci dss",
            "iso 8583",
            "contactless",
            "tokenization",
            "fraud",
        ]
    )
    exclude_keywords: List[str] = field(
        default_factory=lambda: [
            "intern",
            "trainee",
            "freshers",
            "unpaid",
            "commission only",
            "door to door",
        ]
    )
    resume_summary: str = (
        "Engineering leader with deep experience in payments, EMV, POS terminals, automation QA, "
        "solution architecture, and large-scale product delivery across payment-terminal ecosystems."
    )
    profile_notes: str = (
        "Prefer senior individual-contributor or people-manager roles in payments, EMV, POS, POI, "
        "payment gateways, card-present/card-not-present, and payment-terminal platforms."
    )


@dataclass
class JobPosting:
    id: str
    title: str
    company: str
    location: str
    url: str
    description: str
    source: str
    posted_at: Optional[str] = None
    salary: Optional[str] = None
    employment_type: Optional[str] = None
    remote: Optional[bool] = None
    raw_payload: Optional[Dict[str, Any]] = None


@dataclass
class ScoreResult:
    score: float
    decision: str
    reasons: List[str]
    title_hits: int
    location_hits: int
    must_hits: int
    keyword_hits: int
    exclude_hits: int


class Database:
    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                source TEXT,
                title TEXT,
                company TEXT,
                location TEXT,
                url TEXT,
                description TEXT,
                posted_at TEXT,
                salary TEXT,
                employment_type TEXT,
                remote INTEGER,
                score REAL,
                decision TEXT,
                reasons TEXT,
                status TEXT DEFAULT 'new',
                applied_note TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS job_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT,
                event_type TEXT,
                event_value TEXT,
                created_at TEXT
            )
            """
        )
        self.conn.commit()

    def upsert_job(self, job: JobPosting, score: ScoreResult) -> None:
        now = utc_now_iso()
        self.conn.execute(
            """
            INSERT INTO jobs (
                id, source, title, company, location, url, description, posted_at, salary,
                employment_type, remote, score, decision, reasons, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                source=excluded.source,
                title=excluded.title,
                company=excluded.company,
                location=excluded.location,
                url=excluded.url,
                description=excluded.description,
                posted_at=excluded.posted_at,
                salary=excluded.salary,
                employment_type=excluded.employment_type,
                remote=excluded.remote,
                score=excluded.score,
                decision=excluded.decision,
                reasons=excluded.reasons,
                updated_at=excluded.updated_at
            """,
            (
                job.id,
                job.source,
                job.title,
                job.company,
                job.location,
                job.url,
                job.description,
                job.posted_at,
                job.salary,
                job.employment_type,
                int(bool(job.remote)) if job.remote is not None else None,
                score.score,
                score.decision,
                json.dumps(score.reasons),
                now,
                now,
            ),
        )
        self.conn.commit()

    def add_event(self, job_id: str, event_type: str, event_value: str) -> None:
        self.conn.execute(
            "INSERT INTO job_events(job_id, event_type, event_value, created_at) VALUES (?, ?, ?, ?)",
            (job_id, event_type, event_value, utc_now_iso()),
        )
        self.conn.commit()

    def update_status(self, job_id: str, status: str, note: str = "") -> None:
        self.conn.execute(
            "UPDATE jobs SET status=?, applied_note=?, updated_at=? WHERE id=?",
            (status, note, utc_now_iso(), job_id),
        )
        self.conn.commit()
        self.add_event(job_id, "status", status)

    def fetch_jobs(self) -> pd.DataFrame:
        return pd.read_sql_query("SELECT * FROM jobs ORDER BY score DESC, updated_at DESC", self.conn)

    def stats(self) -> Dict[str, int]:
        cur = self.conn.cursor()
        result = {}
        for label in ["new", "saved", "applied", "interview", "rejected", "offer"]:
            row = cur.execute("SELECT COUNT(*) AS c FROM jobs WHERE status=?", (label,)).fetchone()
            result[label] = int(row[0])
        return result


class JobScorer:
    def __init__(self, profile: CandidateProfile):
        self.profile = profile

    def score(self, job: JobPosting) -> ScoreResult:
        hay = normalize_text(
            " ".join(
                filter(
                    None,
                    [
                        job.title,
                        job.company,
                        job.location,
                        job.description,
                        job.salary or "",
                        job.employment_type or "",
                    ],
                )
            )
        )
        reasons: List[str] = []
        score = 0.0

        title_hits = keyword_hits(hay, self.profile.target_titles)
        location_hits = keyword_hits(hay, self.profile.preferred_locations)
        must_hits = keyword_hits(hay, self.profile.must_have_keywords)
        core_hits = keyword_hits(hay, self.profile.core_keywords)
        exclude_hits = keyword_hits(hay, self.profile.exclude_keywords)

        score += title_hits * 16
        if title_hits:
            reasons.append(f"title match x{title_hits}")

        score += location_hits * 8
        if location_hits:
            reasons.append(f"location match x{location_hits}")

        score += must_hits * 10
        if must_hits:
            reasons.append(f"must-have hits x{must_hits}")

        score += min(core_hits, 12) * 4
        if core_hits:
            reasons.append(f"payments/domain hits x{core_hits}")

        seniority_bonus = min(self.profile.years_experience, 20)
        score += seniority_bonus
        reasons.append(f"experience bonus +{seniority_bonus}")

        if bool(job.remote):
            score += 8
            reasons.append("remote-friendly")

        if exclude_hits:
            penalty = exclude_hits * 25
            score -= penalty
            reasons.append(f"exclude penalty -{penalty}")

        decision = "reject"
        if score >= 90:
            decision = "priority"
        elif score >= 60:
            decision = "shortlist"
        elif score >= 40:
            decision = "review"

        return ScoreResult(
            score=round(score, 2),
            decision=decision,
            reasons=reasons,
            title_hits=title_hits,
            location_hits=location_hits,
            must_hits=must_hits,
            keyword_hits=core_hits,
            exclude_hits=exclude_hits,
        )

    def outreach_message(self, job: JobPosting) -> str:
        return (
            f"Hello Hiring Team,\n\n"
            f"I am interested in the {job.title} role at {job.company}. I bring {self.profile.years_experience}+ years "
            f"of experience in payments, EMV, POS terminals, automation QA, technical leadership, and solution architecture. "
            f"My background aligns strongly with card-present/card-not-present systems, payment gateways, POI/POS ecosystems, "
            f"terminal integrations, and production-grade payment workflows.\n\n"
            f"Highlights:\n"
            f"- Leadership across engineering, QA, and automation delivery\n"
            f"- Hands-on experience across payments/EMV/POS-terminal ecosystems\n"
            f"- Strong fit for architecture, program execution, and customer-facing technical delivery\n\n"
            f"I would value the opportunity to discuss how I can contribute to {job.company}.\n\n"
            f"Best regards,\n{self.profile.name}"
        )

    def resume_fit_bullets(self, job: JobPosting) -> List[str]:
        bullets = [
            "Led engineering and QA delivery for payment-terminal and POS ecosystems with strong EMV domain depth.",
            "Worked across card-present and card-not-present workflows, payment gateways, terminal integrations, and production issue resolution.",
            "Built scalable automation and release-quality processes for payments products in customer-facing environments.",
        ]
        desc = normalize_text(job.description)
        if "android" in desc:
            bullets.append("Delivered Android-platform and device-oriented features for POS / payment-terminal environments.")
        if "microservices" in desc or "spring" in desc:
            bullets.append("Designed service-oriented architectures and backend integrations for enterprise payment workflows.")
        if "manager" in normalize_text(job.title):
            bullets.append("Led cross-functional teams and execution across engineering, QA, product, and customer delivery stakeholders.")
        return bullets[:5]


class BaseConnector:
    source_name = "Base"

    def fetch(self) -> List[JobPosting]:
        raise NotImplementedError


class ManualFileConnector(BaseConnector):
    source_name = "Manual Import"

    def __init__(self, uploads: List[Any]):
        self.uploads = uploads

    def fetch(self) -> List[JobPosting]:
        jobs: List[JobPosting] = []
        for upload in self.uploads:
            suffix = Path(upload.name).suffix.lower()
            if suffix == ".json":
                data = json.load(upload)
                for item in data:
                    jobs.append(normalize_job(item, source=item.get("source", self.source_name)))
            elif suffix == ".csv":
                text = upload.read().decode("utf-8", errors="ignore").splitlines()
                reader = csv.DictReader(text)
                for row in reader:
                    jobs.append(normalize_job(row, source=row.get("source", self.source_name)))
        return jobs


class RemotiveConnector(BaseConnector):
    source_name = "Remote / API / RSS"

    def fetch(self) -> List[JobPosting]:
        jobs: List[JobPosting] = []
        try:
            resp = requests.get(REMOTE_SITES["Remotive"], timeout=20)
            resp.raise_for_status()
            payload = resp.json()
            for item in payload.get("jobs", []):
                jobs.append(
                    JobPosting(
                        id=stable_id(self.source_name, item.get("url") or item.get("id")),
                        title=item.get("title", ""),
                        company=item.get("company_name", ""),
                        location=item.get("candidate_required_location", "Remote"),
                        url=item.get("url", ""),
                        description=strip_html(item.get("description", "")),
                        source=self.source_name,
                        posted_at=item.get("publication_date"),
                        salary=item.get("salary"),
                        employment_type=item.get("job_type"),
                        remote=True,
                        raw_payload=item,
                    )
                )
        except Exception:
            return jobs
        return jobs


class RSSConnector(BaseConnector):
    source_name = "Remote / API / RSS"

    def __init__(self, rss_urls: List[str]):
        self.rss_urls = [u.strip() for u in rss_urls if u.strip()]

    def fetch(self) -> List[JobPosting]:
        jobs: List[JobPosting] = []
        if not feedparser:
            return jobs
        for rss_url in self.rss_urls:
            try:
                parsed = feedparser.parse(rss_url)
                for entry in parsed.entries:
                    jobs.append(
                        JobPosting(
                            id=stable_id(self.source_name, getattr(entry, "link", "") or getattr(entry, "id", "")),
                            title=getattr(entry, "title", "Untitled"),
                            company="",
                            location="Remote/Unknown",
                            url=getattr(entry, "link", ""),
                            description=strip_html(getattr(entry, "summary", "")),
                            source=self.source_name,
                            posted_at=getattr(entry, "published", None),
                            remote=True,
                            raw_payload=dict(entry),
                        )
                    )
            except Exception:
                continue
        return jobs


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def keyword_hits(text: str, candidates: Iterable[str]) -> int:
    hits = 0
    for c in candidates:
        c_norm = normalize_text(c)
        if c_norm and c_norm in text:
            hits += 1
    return hits


def stable_id(source: str, key: str) -> str:
    raw = f"{source}::{key}".encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()[:24]


def strip_html(text: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", no_tags).strip()


def parse_bool(value: Any) -> Optional[bool]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in {"true", "1", "yes", "y", "remote"}:
        return True
    if s in {"false", "0", "no", "n"}:
        return False
    return None


def normalize_job(raw: Dict[str, Any], source: str = "Manual Import") -> JobPosting:
    title = raw.get("title") or raw.get("job_title") or ""
    company = raw.get("company") or raw.get("company_name") or ""
    location = raw.get("location") or raw.get("job_location") or "Unknown"
    url = raw.get("url") or raw.get("link") or raw.get("job_url") or ""
    description = raw.get("description") or raw.get("summary") or raw.get("job_description") or ""
    posted_at = raw.get("posted_at") or raw.get("date") or raw.get("published") or raw.get("publication_date")
    salary = raw.get("salary") or raw.get("compensation")
    employment_type = raw.get("employment_type") or raw.get("job_type")
    remote = parse_bool(raw.get("remote"))

    key = url or f"{title}|{company}|{location}|{posted_at}"
    return JobPosting(
        id=stable_id(source, key),
        title=title,
        company=company,
        location=location,
        url=url,
        description=strip_html(description),
        source=source,
        posted_at=posted_at,
        salary=salary,
        employment_type=employment_type,
        remote=remote,
        raw_payload=raw,
    )


def save_profile(profile: CandidateProfile) -> None:
    PROFILE_FILE.write_text(json.dumps(asdict(profile), indent=2), encoding="utf-8")


def load_profile() -> CandidateProfile:
    if PROFILE_FILE.exists():
        data = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
        return CandidateProfile(**data)
    profile = CandidateProfile()
    save_profile(profile)
    return profile


def search_url_templates(profile: CandidateProfile) -> Dict[str, List[str]]:
    title_terms = [quote_plus(t) for t in profile.target_titles[:6]]
    domain_terms = quote_plus("EMV POS payments payment terminal gateway POI card present card not present")
    location_terms = [quote_plus(loc) for loc in profile.preferred_locations[:8]]
    remote_q = quote_plus("remote payments emv pos gateway architect manager")

    urls = {
        "LinkedIn": [
            f"https://www.linkedin.com/jobs/search/?keywords={t}%20{domain_terms}&location={loc}"
            for t in title_terms[:4]
            for loc in location_terms[:4]
        ],
        "Indeed": [
            f"https://www.indeed.com/jobs?q={t}%20{domain_terms}&l={loc}"
            for t in title_terms[:3]
            for loc in location_terms[:3]
        ],
        "Naukri": [
            f"https://www.naukri.com/{quote_plus('payments emv pos ' + title.replace('+', ' '))}-jobs-in-{loc}"
            for title in title_terms[:3]
            for loc in [quote_plus('india'), quote_plus('bangalore')]
        ],
        "Glassdoor": [
            f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={t}%20{domain_terms}"
            for t in title_terms[:3]
        ],
        "Monster": [
            f"https://www.monster.com/jobs/search?q={t}%20{domain_terms}&where={loc}"
            for t in title_terms[:3]
            for loc in location_terms[:2]
        ],
        "Shine": [
            f"https://www.shine.com/job-search/{t}-{quote_plus('payments emv pos')}-jobs"
            for t in title_terms[:3]
        ],
        "Naukri Gulf": [
            f"https://www.naukrigulf.com/{quote_plus('payments emv pos ' + title.replace('+', ' '))}-jobs"
            for title in title_terms[:3]
        ],
        "Remote": [
            f"https://remotive.com/remote-jobs/search?query={remote_q}",
            f"https://weworkremotely.com/remote-jobs/search?term={remote_q}",
        ],
    }
    return urls


def export_dataframe(df: pd.DataFrame, file_name: str) -> Path:
    out = EXPORT_DIR / file_name
    if file_name.endswith(".csv"):
        df.to_csv(out, index=False)
    else:
        df.to_json(out, orient="records", indent=2)
    return out


def ingest_jobs(db: Database, profile: CandidateProfile, jobs: List[JobPosting]) -> Tuple[int, int]:
    scorer = JobScorer(profile)
    added = 0
    priority = 0
    for job in jobs:
        score = scorer.score(job)
        db.upsert_job(job, score)
        added += 1
        if score.decision == "priority":
            priority += 1
    return added, priority


def render_profile_editor(profile: CandidateProfile) -> CandidateProfile:
    st.subheader("Profile")
    c1, c2 = st.columns(2)
    with c1:
        profile.name = st.text_input("Name", profile.name)
        profile.email = st.text_input("Email", profile.email)
        profile.phone = st.text_input("Phone", profile.phone)
        profile.current_location = st.text_input("Current location", profile.current_location)
        profile.years_experience = st.number_input("Years of experience", 0, 40, profile.years_experience)
        profile.notice_period = st.text_input("Notice period", profile.notice_period)
    with c2:
        profile.resume_summary = st.text_area("Resume summary", profile.resume_summary, height=150)
        profile.profile_notes = st.text_area("Profile notes", profile.profile_notes, height=150)

    profile.target_titles = [x.strip() for x in st.text_area(
        "Target titles (one per line)",
        "\n".join(profile.target_titles),
        height=180,
    ).splitlines() if x.strip()]

    profile.preferred_locations = [x.strip() for x in st.text_area(
        "Preferred locations (one per line)",
        "\n".join(profile.preferred_locations),
        height=180,
    ).splitlines() if x.strip()]

    profile.must_have_keywords = [x.strip() for x in st.text_area(
        "Must-have keywords (one per line)",
        "\n".join(profile.must_have_keywords),
        height=180,
    ).splitlines() if x.strip()]

    profile.nice_to_have_keywords = [x.strip() for x in st.text_area(
        "Nice-to-have keywords (one per line)",
        "\n".join(profile.nice_to_have_keywords),
        height=180,
    ).splitlines() if x.strip()]

    profile.exclude_keywords = [x.strip() for x in st.text_area(
        "Exclude keywords (one per line)",
        "\n".join(profile.exclude_keywords),
        height=120,
    ).splitlines() if x.strip()]

    if st.button("Save profile"):
        save_profile(profile)
        st.success("Profile saved.")
    return profile


def render_ingestion_tab(db: Database, profile: CandidateProfile) -> None:
    st.subheader("Ingest jobs")
    st.caption("Use manual CSV/JSON exports, remote APIs/RSS where available, and platform search URLs for manual review.")

    uploaded_files = st.file_uploader(
        "Upload CSV/JSON job exports",
        type=["csv", "json"],
        accept_multiple_files=True,
    )

    rss_text = st.text_area(
        "Optional RSS feeds (one URL per line)",
        value="",
        height=120,
        placeholder="Paste RSS feed URLs here if you have them.",
    )

    enable_remotive = st.checkbox("Fetch remote jobs from Remotive API", value=True)

    if st.button("Run ingestion"):
        jobs: List[JobPosting] = []
        if uploaded_files:
            jobs.extend(ManualFileConnector(uploaded_files).fetch())
        if enable_remotive:
            jobs.extend(RemotiveConnector().fetch())
        rss_urls = [line.strip() for line in rss_text.splitlines() if line.strip()]
        if rss_urls:
            jobs.extend(RSSConnector(rss_urls).fetch())

        if not jobs:
            st.warning("No jobs found. Upload CSV/JSON exports or enable a connector.")
            return

        added, priority = ingest_jobs(db, profile, dedupe_jobs(jobs))
        st.success(f"Ingested {added} jobs. Priority matches: {priority}.")

    st.markdown("### Search URLs for manual sourcing")
    urls = search_url_templates(profile)
    for source, links in urls.items():
        with st.expander(source, expanded=False):
            for link in links[:12]:
                st.markdown(f"- [{link}]({link})")

    st.markdown("### Recommended import schema")
    st.code(
        "title,company,location,url,description,posted_at,salary,employment_type,remote,source\n"
        "Engineering Manager,Acme,Remote,https://example.com/job1,Payments EMV POS role,2026-03-10,$120k,Full-time,true,LinkedIn",
        language="csv",
    )


def dedupe_jobs(jobs: List[JobPosting]) -> List[JobPosting]:
    seen = set()
    out = []
    for job in jobs:
        key = (job.id, job.url, job.title, job.company)
        if key in seen:
            continue
        seen.add(key)
        out.append(job)
    return out


def render_pipeline_tab(db: Database, profile: CandidateProfile) -> None:
    st.subheader("Pipeline")
    df = db.fetch_jobs()
    if df.empty:
        st.info("No jobs in the tracker yet.")
        return

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        min_score = st.slider("Minimum score", 0, 150, 40)
    with c2:
        decision_filter = st.multiselect("Decision", ["priority", "shortlist", "review", "reject"], default=["priority", "shortlist", "review"])
    with c3:
        status_filter = st.multiselect("Status", ["new", "saved", "applied", "interview", "rejected", "offer"], default=["new", "saved", "applied", "interview", "offer"])
    with c4:
        source_filter = st.multiselect("Source", sorted(df["source"].dropna().unique().tolist()), default=sorted(df["source"].dropna().unique().tolist()))

    filtered = df[
        (df["score"] >= min_score)
        & (df["decision"].isin(decision_filter))
        & (df["status"].isin(status_filter))
        & (df["source"].isin(source_filter))
    ].copy()

    st.dataframe(
        filtered[["score", "decision", "status", "title", "company", "location", "source", "posted_at", "url"]],
        use_container_width=True,
        height=450,
    )

    if filtered.empty:
        return

    selected_job = st.selectbox(
        "Select a job",
        filtered["id"].tolist(),
        format_func=lambda x: _job_label(filtered, x),
    )

    row = filtered[filtered["id"] == selected_job].iloc[0]
    scorer = JobScorer(profile)
    job = JobPosting(
        id=row["id"],
        title=row["title"],
        company=row["company"],
        location=row["location"],
        url=row["url"],
        description=row["description"],
        source=row["source"],
        posted_at=row.get("posted_at"),
        salary=row.get("salary"),
        employment_type=row.get("employment_type"),
        remote=bool(row.get("remote")) if pd.notna(row.get("remote")) else None,
    )

    st.markdown(f"### {job.title} — {job.company}")
    st.markdown(f"**Location:** {job.location}  ")
    st.markdown(f"**Source:** {job.source}  ")
    st.markdown(f"**Decision:** {row['decision']}  ")
    st.markdown(f"**Score:** {row['score']}  ")
    st.markdown(f"**URL:** [Open job]({job.url})")
    if pd.notna(row.get("reasons")):
        try:
            reasons = json.loads(row["reasons"])
            st.markdown("**Why matched:**")
            for reason in reasons:
                st.markdown(f"- {reason}")
        except Exception:
            pass

    with st.expander("Description", expanded=False):
        st.write(job.description)

    st.markdown("### Tailored outreach note")
    outreach = scorer.outreach_message(job)
    st.text_area("Copy/paste note", outreach, height=220)

    st.markdown("### Tailored resume bullets")
    bullets = scorer.resume_fit_bullets(job)
    st.text_area("Copy/paste bullets", "\n".join(f"- {b}" for b in bullets), height=180)

    status = st.selectbox("Update status", ["new", "saved", "applied", "interview", "rejected", "offer"], index=["new", "saved", "applied", "interview", "rejected", "offer"].index(row["status"]))
    note = st.text_area("Note", row.get("applied_note") or "", height=120)
    if st.button("Save status update"):
        db.update_status(job.id, status, note)
        st.success("Status updated.")

    export_df = filtered[["score", "decision", "status", "title", "company", "location", "source", "posted_at", "url"]]
    if st.button("Export filtered CSV"):
        out = export_dataframe(export_df, "filtered_jobs.csv")
        st.success(f"Exported to {out}")


def _job_label(df: pd.DataFrame, job_id: str) -> str:
    row = df[df["id"] == job_id].iloc[0]
    return f"{row['score']} | {row['title']} | {row['company']} | {row['location']}"


def render_dashboard_tab(db: Database) -> None:
    st.subheader("Dashboard")
    stats = db.stats()
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    cards = [c1, c2, c3, c4, c5, c6]
    labels = ["new", "saved", "applied", "interview", "rejected", "offer"]
    for card, label in zip(cards, labels):
        card.metric(label.title(), stats.get(label, 0))

    df = db.fetch_jobs()
    if df.empty:
        st.info("Ingest jobs to see analytics.")
        return

    st.markdown("### Top matches")
    top = df.sort_values(["score", "updated_at"], ascending=[False, False]).head(20)
    st.dataframe(top[["score", "decision", "status", "title", "company", "location", "source"]], use_container_width=True)

    st.markdown("### Source distribution")
    source_counts = df.groupby("source").size().reset_index(name="count").sort_values("count", ascending=False)
    st.bar_chart(source_counts.set_index("source"))


def render_help_tab(profile: CandidateProfile) -> None:
    st.subheader("How to use this safely and effectively")
    st.markdown(
        """
1. Use platform searches to find matching jobs.
2. Export or copy jobs into CSV/JSON, or connect supported feeds/APIs.
3. Ingest jobs here.
4. Review priority and shortlist matches.
5. Use the tailored outreach note and bullets.
6. Apply manually on LinkedIn, Naukri, Indeed, Glassdoor, Monster, Shine, Naukri Gulf, or company careers pages.
        """
    )

    st.markdown("### Suggested target queries")
    queries = [
        "Engineering Manager payments EMV POS terminal gateway",
        "QA Manager payment terminals EMV POS automation",
        "Solution Architect payments card present card not present",
        "Technical Program Manager payment gateway POS POI",
        "Technical Manager payment terminal Android POS",
    ]
    for q in queries:
        st.code(q)

    st.markdown("### Best-fit domains for your profile")
    for item in [
        "Payment terminals / POS / POI platforms",
        "EMV kernel / device integrations / card-present stacks",
        "Payment gateways / orchestration / switching / authorization",
        "Acquiring, merchant platforms, fintech infrastructure",
        "Card-present / card-not-present risk, fraud, tokenization",
        "Retail payments, petroleum payments, hospitality POS integrations",
    ]:
        st.markdown(f"- {item}")

    st.markdown("### Search URLs generated from your current profile")
    for source, links in search_url_templates(profile).items():
        with st.expander(source, expanded=False):
            for link in links[:10]:
                st.markdown(f"- [{link}]({link})")


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)
    st.caption("Payments / EMV / POS / Gateway / POI-focused human-in-the-loop job search workspace")

    db = Database(DB_PATH)
    profile = load_profile()

    dashboard_tab, profile_tab, ingest_tab, pipeline_tab, help_tab = st.tabs(
        ["Dashboard", "Profile", "Ingest", "Pipeline", "Help"]
    )

    with dashboard_tab:
        render_dashboard_tab(db)
    with profile_tab:
        profile = render_profile_editor(profile)
    with ingest_tab:
        render_ingestion_tab(db, profile)
    with pipeline_tab:
        render_pipeline_tab(db, profile)
    with help_tab:
        render_help_tab(profile)


if __name__ == "__main__":
    main()
