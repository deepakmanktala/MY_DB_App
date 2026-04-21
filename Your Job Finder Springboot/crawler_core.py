"""
Async crawl engine — used by both crawler.py (CLI) and crawler_gui.py (GUI).
Exposes run_all_gui() with callbacks for live progress + log streaming.
"""

import asyncio
import csv
import json
import logging
import random
import re
import time
import urllib.parse
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

import aiohttp
from bs4 import BeautifulSoup

from job_portals import JOB_PORTALS

REQUEST_DELAY_S   = 0.5
REQUEST_TIMEOUT_S = 15
OUTPUT_CSV        = "jobs_output.csv"
OUTPUT_JSON       = "jobs_output.json"
LOG_FILE          = "crawler.log"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# These portals are always included regardless of region selection
GLOBAL_PORTAL_NAMES = {
    "indeed", "linkedin", "monster", "glassdoor", "ziprecruiter",
    "simplyhired", "careerbuilder", "jooble", "adzuna",
}

# Region → portal name substrings (lowercase match) — global portals added on top
REGION_PORTAL_TAGS = {
    "USA": ["usajobs", "dice", "clearance", "collegerecruiter",
            "hirehive", "aftercollege", "ladders", "jobcase",
            "craigslist", "snagajob", "lensa"],
    "Canada": ["workopolis", "jobbank", "indeed ca", "eluta"],
    "UK / Europe": ["reed", "totaljobs", "cwjobs", "jobsite", "cv-library",
                    "guardian", "stepstone", "eurojob", "eurengineer"],
    "Australia / NZ": ["seek au", "seek nz", "careerone"],
    "Asia / India / Singapore": ["indeed india", "mycareersfuture", "jobsdb", "naukri",
                                  "timesjobs", "shine", "foundit"],
    "Remote only": ["remote ok", "we work remotely", "remote.co", "remotive",
                    "working nomads", "jobspresso", "justremote",
                    "virtual vocations", "pangian"],
}


@dataclass
class JobListing:
    portal:     str
    role_query: str
    title:      str
    company:    str
    location:   str
    url:        str
    posted:     str
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ── URL builder ───────────────────────────────────────────────────────────────
def build_url(template: str, query: str) -> str:
    encoded = urllib.parse.quote_plus(query)
    return template.replace("{query}", encoded)


def random_headers() -> dict:
    return {
        "User-Agent":      random.choice(USER_AGENTS),
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection":      "keep-alive",
        "DNT":             "1",
    }


# ── Portal filter by region ───────────────────────────────────────────────────
def _is_global(portal: dict) -> bool:
    name = portal["name"].lower()
    return any(g in name for g in GLOBAL_PORTAL_NAMES)

def filter_portals(region: str) -> list:
    if region == "Worldwide (all portals)":
        return JOB_PORTALS
    tags = REGION_PORTAL_TAGS.get(region, [])
    seen = set()
    result = []
    for p in JOB_PORTALS:
        name = p["name"].lower()
        if name in seen:
            continue
        if _is_global(p) or any(t in name for t in tags):
            seen.add(name)
            result.append(p)
    return result


# ── Parsers ───────────────────────────────────────────────────────────────────
def _extract_text(card, selectors: list) -> str:
    for sel in selectors:
        el = card.select_one(sel)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)
    return ""


def parse_jobs_generic(html: str, portal_name: str, role_query: str, page_url: str) -> List[JobListing]:
    soup = BeautifulSoup(html, "html.parser")
    jobs: List[JobListing] = []
    card_selectors = [
        "div.job_seen_beacon", "div.jobsearch-SerpJobCard",
        "li.jobs-search-results__list-item", "div.base-card",
        "div.mux-job-card", "article.SerpJob", "article.job-result",
        "article[data-automation='normalJob']", "div[data-automation='jobCard']",
        "div.search-card", "div.job-card", "div.jobCard",
        "li.job-listing", "article.job",
        "div[class*='job-result']", "div[class*='jobResult']",
        "div[class*='job_card']", "div[class*='jobCard']",
        "div[class*='JobCard']", "section[class*='job']",
    ]
    cards = []
    for sel in card_selectors:
        cards = soup.select(sel)
        if cards:
            break
    for card in cards[:30]:
        title    = _extract_text(card, ["h2", "h3", "h4", "[class*='title']", "[class*='Title']"])
        company  = _extract_text(card, ["[class*='company']", "[class*='Company']", "[class*='employer']"])
        location = _extract_text(card, ["[class*='location']", "[class*='Location']", "[class*='city']"])
        posted   = _extract_text(card, ["[class*='date']", "[class*='Date']", "time"])
        link_tag = card.find("a", href=True)
        job_url  = ""
        if link_tag:
            href = link_tag["href"]
            job_url = href if href.startswith("http") else page_url.rstrip("/") + "/" + href.lstrip("/")
        if title and len(title) > 3:
            jobs.append(JobListing(portal_name, role_query, title.strip(),
                                   company.strip() if company else "",
                                   location.strip() if location else "",
                                   job_url, posted.strip() if posted else ""))
    return jobs


def parse_indeed(html, portal, role, url):
    soup  = BeautifulSoup(html, "html.parser")
    jobs  = []
    cards = soup.select("div.job_seen_beacon, td.resultContent")
    for card in cards[:30]:
        title   = _extract_text(card, ["h2.jobTitle span[title]", "h2.jobTitle", "h2"])
        company = _extract_text(card, ["span.companyName", "[data-testid='company-name']"])
        loc     = _extract_text(card, ["div.companyLocation", "[data-testid='text-location']"])
        posted  = _extract_text(card, ["span.date", "span[class*='date']"])
        link    = card.select_one("a[id^='job_']") or card.select_one("a[href*='/rc/clk']")
        job_url = ("https://www.indeed.com" + link["href"]) if link else url
        if title:
            jobs.append(JobListing(portal, role, title, company, loc, job_url, posted))
    return jobs


def parse_linkedin(html, portal, role, url):
    soup  = BeautifulSoup(html, "html.parser")
    jobs  = []
    cards = soup.select("div.base-card, li.jobs-search-results__list-item")
    for card in cards[:30]:
        title   = _extract_text(card, ["h3.base-search-card__title", "span.screen-reader-text"])
        company = _extract_text(card, ["h4.base-search-card__subtitle", "a.hidden-nested-link"])
        loc     = _extract_text(card, ["span.job-search-card__location"])
        posted  = _extract_text(card, ["time", "span.job-search-card__listdate"])
        link    = card.select_one("a.base-card__full-link") or card.select_one("a[href*='/jobs/view/']")
        job_url = link["href"] if link else url
        if title:
            jobs.append(JobListing(portal, role, title, company, loc, job_url, posted))
    return jobs


def parse_dice(html, portal, role, url):
    soup  = BeautifulSoup(html, "html.parser")
    jobs  = []
    cards = soup.select("div.search-card, dhi-search-card")
    for card in cards[:30]:
        title   = _extract_text(card, ["a.card-title-link", "h5"])
        company = _extract_text(card, ["a.employer-name", "span[class*='employer']"])
        loc     = _extract_text(card, ["span.location", "span[class*='location']"])
        posted  = _extract_text(card, ["span.posted-date", "span[class*='date']"])
        link    = card.select_one("a.card-title-link")
        job_url = link["href"] if link else url
        if title:
            jobs.append(JobListing(portal, role, title, company, loc, job_url, posted))
    return jobs


def parse_remoteok(html, portal, role, url):
    soup  = BeautifulSoup(html, "html.parser")
    jobs  = []
    rows  = soup.select("tr.job")
    for row in rows[:30]:
        title   = _extract_text(row, ["td.company h2", "span[itemprop='title']"])
        company = _extract_text(row, ["span[itemprop='name']", "td.company h3"])
        loc     = _extract_text(row, ["div.location", "span.location"])
        posted  = _extract_text(row, ["td.time time"])
        link    = row.get("data-url") or ""
        job_url = ("https://remoteok.com" + link) if link.startswith("/") else link or url
        if title:
            jobs.append(JobListing(portal, role, title, company, loc, job_url, posted))
    return jobs


def parse_weworkremotely(html, portal, role, url):
    soup  = BeautifulSoup(html, "html.parser")
    jobs  = []
    items = soup.select("li[class*='feature']") or soup.select("article")
    for item in items[:30]:
        title   = _extract_text(item, ["span.title", "h4", "h3"])
        company = _extract_text(item, ["span.company", "span[class*='company']"])
        loc     = _extract_text(item, ["span.region", "span[class*='region']"])
        posted  = _extract_text(item, ["span[class*='date']", "time"])
        link    = item.select_one("a[href*='/remote-jobs/']")
        job_url = ("https://weworkremotely.com" + link["href"]) if link else url
        if title:
            jobs.append(JobListing(portal, role, title, company, loc, job_url, posted))
    return jobs


PARSER_MAP = {
    "Indeed":           parse_indeed,
    "Indeed CA":        parse_indeed,
    "LinkedIn":         parse_linkedin,
    "Dice":             parse_dice,
    "Remote OK":        parse_remoteok,
    "We Work Remotely": parse_weworkremotely,
}


def parse_page(html, portal_name, role, url):
    parser = PARSER_MAP.get(portal_name, parse_jobs_generic)
    return parser(html, portal_name, role, url)


# ── Async fetch ───────────────────────────────────────────────────────────────
async def fetch(session: aiohttp.ClientSession, url: str,
                semaphore: asyncio.Semaphore,
                log_cb: Optional[Callable] = None,
                debug: bool = False) -> Optional[str]:
    hdrs = random_headers()
    if debug and log_cb:
        log_cb(f"[DBG] ▶ REQUEST  {url}", "warn")
        log_cb(f"[DBG]   Headers: {hdrs}", "warn")
    async with semaphore:
        await asyncio.sleep(REQUEST_DELAY_S)
        try:
            async with session.get(
                url, headers=hdrs,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_S),
                ssl=True, allow_redirects=True,
            ) as resp:
                body = await resp.text(errors="replace")
                if debug and log_cb:
                    preview = body[:500].replace("\n", " ")
                    log_cb(f"[DBG] ◀ RESPONSE {url}", "warn")
                    log_cb(f"[DBG]   Status : {resp.status}", "warn")
                    log_cb(f"[DBG]   Headers: {dict(resp.headers)}", "warn")
                    log_cb(f"[DBG]   Body   : {preview}…", "warn")
                if resp.status == 200:
                    return body
                msg = f"HTTP {resp.status}  {url}"
                log.warning(msg)
                if log_cb:
                    log_cb(msg, "warn")
                return None
        except asyncio.TimeoutError:
            msg = f"Timeout  {url}"
            log.warning(msg)
            if log_cb: log_cb(msg, "warn")
        except aiohttp.ClientSSLError:
            msg = f"SSL error  {url}"
            log.warning(msg)
            if log_cb: log_cb(msg, "warn")
        except aiohttp.ClientError as exc:
            msg = f"Client error  {url}  — {exc}"
            log.warning(msg)
            if log_cb: log_cb(msg, "warn")
        except Exception as exc:
            msg = f"Unexpected error  {url}  — {exc}"
            log.error(msg)
            if log_cb: log_cb(msg, "error")
        return None


async def crawl_portal(session, portal, role, semaphore, log_cb=None, debug=False):
    search_tpl = portal.get("search", "")
    if not search_tpl or "{query}" not in search_tpl:
        return []
    url  = build_url(search_tpl, role)
    html = await fetch(session, url, semaphore, log_cb, debug)
    if not html:
        return []
    jobs = parse_page(html, portal["name"], role, url)
    msg  = f"  ✓ {portal['name']:<25s} [{role}]  → {len(jobs)} listings"
    log.info(msg)
    if log_cb:
        log_cb(msg, "info")
    return jobs


# ── Main entry points ─────────────────────────────────────────────────────────
async def run_all_gui(
    roles: List[str],
    region: str = "Worldwide (all portals)",
    max_concurrent: int = 5,
    stop_event: Optional[object] = None,
    log_cb: Optional[Callable] = None,
    progress_cb: Optional[Callable] = None,
    debug: bool = False,
) -> List[JobListing]:
    from api_sources import run_api_sources

    if debug and log_cb:
        log_cb("[DBG] Debug mode ON — every request & response will be printed", "warn")

    portals   = filter_portals(region)
    semaphore = asyncio.Semaphore(max_concurrent)
    # +1 slot in progress for the API sources batch
    total     = len(portals) * len(roles) + 1
    done      = 0

    connector = aiohttp.TCPConnector(limit=max_concurrent, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:

        # ── HTML portal tasks
        portal_tasks = [
            crawl_portal(session, p, r, semaphore, log_cb, debug)
            for p in portals
            for r in roles
        ]
        # ── API/feed sources task (Greenhouse + Workable + Naukri enhanced)
        api_task = run_api_sources(session, semaphore, roles, log_cb, debug)

        all_jobs: List[JobListing] = []
        for coro in asyncio.as_completed(portal_tasks + [api_task]):
            if stop_event and stop_event.is_set():
                if log_cb:
                    log_cb("Crawl stopped by user.", "warn")
                break
            result = await coro
            if isinstance(result, list):
                all_jobs.extend(result)
            done += 1
            if progress_cb:
                progress_cb(done / total * 100)

    return all_jobs


async def run_all(roles: List[str], max_concurrent: int = 5) -> List[JobListing]:
    from job_portals import TARGET_ROLES
    return await run_all_gui(roles=roles or TARGET_ROLES,
                             max_concurrent=max_concurrent)


# ── File rotation ─────────────────────────────────────────────────────────────
def purge_old_outputs(directory: str = ".", keep: int = 50) -> None:
    """Delete oldest timestamped output files when total run-sets exceed `keep`."""
    from pathlib import Path
    import re

    base = Path(directory)
    # Collect all timestamped stems (one stem = one run)
    pattern = re.compile(r"^jobs_(\d{8}_\d{6})")
    stems: dict[str, list] = {}
    for f in base.glob("jobs_*"):
        m = pattern.match(f.name)
        if m:
            stems.setdefault(m.group(1), []).append(f)

    if len(stems) <= keep:
        return

    # Sort by timestamp string (lexicographic = chronological) and drop oldest
    oldest = sorted(stems.keys())[: len(stems) - keep]
    deleted = 0
    for ts in oldest:
        for f in stems[ts]:
            try:
                f.unlink()
                log.info("Purged old output: %s", f.name)
                deleted += 1
            except OSError as exc:
                log.warning("Could not delete %s: %s", f.name, exc)
    if deleted:
        log.info("Rotation: removed %d file(s) from %d old run(s)", deleted, len(oldest))


# ── Output writers ────────────────────────────────────────────────────────────
def save_csv(jobs: List[JobListing], path: str) -> None:
    if not jobs:
        return
    fields = list(asdict(jobs[0]).keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for j in jobs:
            writer.writerow(asdict(j))
    log.info("Saved %d jobs → %s", len(jobs), path)


def save_json(jobs: List[JobListing], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump([asdict(j) for j in jobs], f, indent=2, ensure_ascii=False)
    log.info("Saved %d jobs → %s", len(jobs), path)