"""
Job Portal Web Crawler
Searches 100+ English-language HTTPS job portals for target roles.
- 500 ms delay between each request to avoid rate-limit / DDoS flagging.
- No login required; only public listing pages are accessed.
- Results saved to jobs_output.csv and jobs_output.json
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
from typing import List, Optional

import aiohttp
from bs4 import BeautifulSoup

from job_portals import JOB_PORTALS, TARGET_ROLES

# ── Config ───────────────────────────────────────────────────────────────────
REQUEST_DELAY_S   = 0.5          # 500 ms between every single request
REQUEST_TIMEOUT_S = 15           # hard timeout per request
MAX_CONCURRENT    = 5            # max simultaneous in-flight requests
OUTPUT_CSV        = None   # set at runtime with timestamp
OUTPUT_JSON       = None
LOG_FILE          = "crawler.log"

# Rotate user-agents to look like a normal browser
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
]

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ── Data model ────────────────────────────────────────────────────────────────
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


# ── Helpers ───────────────────────────────────────────────────────────────────
def build_url(template: str, query: str) -> str:
    encoded = urllib.parse.quote_plus(query)
    return template.replace("{query}", encoded)


def random_headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection":      "keep-alive",
        "DNT":             "1",
    }


# ── Generic HTML parser (best-effort, works for many portals) ─────────────────
def parse_jobs_generic(html: str, portal_name: str, role_query: str, page_url: str) -> List[JobListing]:
    """
    Heuristic parser that looks for common job-listing HTML patterns.
    Covers Indeed, LinkedIn, Monster, SimplyHired, Reed, Seek, Naukri, Dice, etc.
    Portal-specific parsers below override this for known structures.
    """
    soup = BeautifulSoup(html, "html.parser")
    jobs: List[JobListing] = []

    # Common container selectors (ordered by specificity)
    card_selectors = [
        # Indeed
        "div.job_seen_beacon",
        "div.jobsearch-SerpJobCard",
        # LinkedIn
        "li.jobs-search-results__list-item",
        "div.base-card",
        # Monster / SimplyHired
        "div.mux-job-card",
        "article.SerpJob",
        # Reed
        "article.job-result",
        # Seek
        "article[data-automation='normalJob']",
        "div[data-automation='jobCard']",
        # Dice
        "div.search-card",
        # Generic fallbacks
        "div.job-card",
        "div.jobCard",
        "li.job-listing",
        "article.job",
        "div[class*='job-result']",
        "div[class*='jobResult']",
        "div[class*='job_card']",
        "div[class*='jobCard']",
        "div[class*='JobCard']",
        "section[class*='job']",
    ]

    cards = []
    for sel in card_selectors:
        cards = soup.select(sel)
        if cards:
            break

    for card in cards[:30]:  # cap at 30 per page / role
        title    = _extract_text(card, ["h2", "h3", "h4", "[class*='title']", "[class*='Title']"])
        company  = _extract_text(card, ["[class*='company']", "[class*='Company']", "[class*='employer']"])
        location = _extract_text(card, ["[class*='location']", "[class*='Location']", "[class*='city']"])
        posted   = _extract_text(card, ["[class*='date']", "[class*='Date']", "time"])

        # Try to get a direct link to the job
        link_tag = card.find("a", href=True)
        job_url  = ""
        if link_tag:
            href = link_tag["href"]
            job_url = href if href.startswith("http") else page_url.rstrip("/") + "/" + href.lstrip("/")

        # Only keep results that look like a real job title
        if title and len(title) > 3:
            jobs.append(JobListing(
                portal     = portal_name,
                role_query = role_query,
                title      = title.strip(),
                company    = company.strip() if company else "",
                location   = location.strip() if location else "",
                url        = job_url,
                posted     = posted.strip() if posted else "",
            ))

    return jobs


def _extract_text(card, selectors: list) -> str:
    for sel in selectors:
        el = card.select_one(sel)
        if el and el.get_text(strip=True):
            return el.get_text(strip=True)
    return ""


# ── Portal-specific parsers ───────────────────────────────────────────────────
def parse_indeed(html: str, portal: str, role: str, url: str) -> List[JobListing]:
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


def parse_linkedin(html: str, portal: str, role: str, url: str) -> List[JobListing]:
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


def parse_dice(html: str, portal: str, role: str, url: str) -> List[JobListing]:
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


def parse_remoteok(html: str, portal: str, role: str, url: str) -> List[JobListing]:
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


def parse_weworkremotely(html: str, portal: str, role: str, url: str) -> List[JobListing]:
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


# Router: pick the best parser for a portal
PARSER_MAP = {
    "Indeed":          parse_indeed,
    "Indeed CA":       parse_indeed,
    "LinkedIn":        parse_linkedin,
    "Dice":            parse_dice,
    "Remote OK":       parse_remoteok,
    "We Work Remotely": parse_weworkremotely,
}


def parse_page(html: str, portal_name: str, role: str, url: str) -> List[JobListing]:
    parser = PARSER_MAP.get(portal_name, parse_jobs_generic)
    return parser(html, portal_name, role, url)


# ── Async fetcher ─────────────────────────────────────────────────────────────
semaphore: Optional[asyncio.Semaphore] = None


async def fetch(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    """Fetch a URL and return HTML, or None on error."""
    async with semaphore:
        await asyncio.sleep(REQUEST_DELAY_S)   # 500 ms delay — polite crawling
        try:
            async with session.get(
                url,
                headers=random_headers(),
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_S),
                ssl=True,                       # enforce HTTPS
                allow_redirects=True,
            ) as resp:
                if resp.status == 200:
                    return await resp.text(errors="replace")
                log.warning("HTTP %d  %s", resp.status, url)
                return None
        except asyncio.TimeoutError:
            log.warning("Timeout  %s", url)
        except aiohttp.ClientSSLError:
            log.warning("SSL error  %s", url)
        except aiohttp.ClientError as exc:
            log.warning("Client error  %s  — %s", url, exc)
        except Exception as exc:
            log.error("Unexpected error  %s  — %s", url, exc)
        return None


async def crawl_portal(session: aiohttp.ClientSession, portal: dict, role: str) -> List[JobListing]:
    search_tpl = portal.get("search", "")
    if not search_tpl or "{query}" not in search_tpl:
        log.debug("Skipping %s — no search template", portal["name"])
        return []

    url  = build_url(search_tpl, role)
    log.info("Crawling  %-25s  query=%-30s  url=%s", portal["name"], role, url)
    html = await fetch(session, url)
    if not html:
        return []

    jobs = parse_page(html, portal["name"], role, url)
    log.info("  → found %d listings", len(jobs))
    return jobs


async def run_all() -> List[JobListing]:
    global semaphore
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            crawl_portal(session, portal, role)
            for portal in JOB_PORTALS
            for role   in TARGET_ROLES
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs: List[JobListing] = []
    for r in results:
        if isinstance(r, list):
            all_jobs.extend(r)
        elif isinstance(r, Exception):
            log.error("Task exception: %s", r)

    return all_jobs


# ── Output writers ────────────────────────────────────────────────────────────
def save_csv(jobs: List[JobListing], path: str) -> None:
    if not jobs:
        log.warning("No jobs to write to CSV.")
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


def print_summary(jobs: List[JobListing]) -> None:
    print("\n" + "=" * 70)
    print(f"  CRAWL COMPLETE  |  {len(jobs)} total listings found")
    print("=" * 70)
    by_role: dict = {}
    for j in jobs:
        by_role.setdefault(j.role_query, []).append(j)
    for role, items in sorted(by_role.items(), key=lambda x: -len(x[1])):
        print(f"  {role:<40s}  {len(items):>4d} listings")
    print("=" * 70)
    by_portal: dict = {}
    for j in jobs:
        by_portal.setdefault(j.portal, 0)
        by_portal[j.portal] += 1
    top10 = sorted(by_portal.items(), key=lambda x: -x[1])[:10]
    print("\n  Top 10 portals by listing count:")
    for name, cnt in top10:
        print(f"    {name:<35s}  {cnt:>4d}")
    print()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    start = time.time()
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_CSV  = f"jobs_{ts}.csv"
    OUTPUT_JSON = f"jobs_{ts}.json"

    log.info("Starting job crawl — %d portals × %d roles = %d requests",
             len(JOB_PORTALS), len(TARGET_ROLES), len(JOB_PORTALS) * len(TARGET_ROLES))

    jobs = asyncio.run(run_all())

    save_csv(jobs,  OUTPUT_CSV)
    save_json(jobs, OUTPUT_JSON)

    from report_generator import generate_html
    from crawler_core import purge_old_outputs
    html_path = f"jobs_report_{ts}.html"
    generate_html(jobs, html_path, {"region": "Worldwide (all portals)", "date_label": "All time"})
    log.info("HTML report → %s", html_path)

    purge_old_outputs(directory=".", keep=50)
    print_summary(jobs)

    elapsed = time.time() - start
    log.info("Done in %.1f s  |  results: %s  %s  %s", elapsed, OUTPUT_CSV, OUTPUT_JSON, html_path)