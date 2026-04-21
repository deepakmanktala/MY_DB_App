"""
Free API / Feed sources:
  • Greenhouse  — public JSON boards API (no key needed)
  • Workable    — public XML job feed + HTML search
  • Naukri      — enhanced HTML scraper with alert-style keyword matching
"""

from __future__ import annotations

import asyncio
import logging
import re
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Callable, List, Optional

import aiohttp
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

# ── Greenhouse company slugs (public boards, no auth required) ────────────────
# Add / remove slugs freely — each maps to boards-api.greenhouse.io/v1/boards/{slug}/jobs
GREENHOUSE_COMPANIES = [
    "airbnb", "stripe", "coinbase", "dropbox", "lyft", "pinterest",
    "robinhood", "brex", "figma", "notion", "airtable", "asana",
    "hubspot", "zendesk", "twilio", "datadog", "mongodb", "elastic",
    "hashicorp", "confluent", "snowflake", "databricks", "scale-ai",
    "anthropic", "openai", "cohere", "deepmind", "inflection",
    "plaid", "chime", "affirm", "klarna", "marqeta", "adyen",
    "checkout", "paysafe", "worldpay", "nuvei", "paytm",
    "visa", "mastercard", "americanexpress", "paypal", "square",
    "toast", "shopify", "woocommerce", "bolt", "recurly",
    "verifone", "ingenico", "fiserv", "fisglobal", "ncr",
    "nvidia", "amd", "qualcomm", "arm", "apple", "google",
    "meta", "amazon", "microsoft", "netflix", "spotify", "uber",
    "doordash", "instacart", "grubhub", "postmates", "gopuff",
    "palantir", "c3ai", "samsara", "cloudflare", "fastly",
    "gitlab", "github", "atlassian", "jfrog", "sonarqube",
    "salesforce", "servicenow", "workday", "sap", "oracle",
]

# ── Workable public XML feeds ─────────────────────────────────────────────────
# Global public feed (all Workable-hosted jobs, keyword-filtered client-side)
WORKABLE_XML_FEED = "https://www.workable.com/boards/workable.xml"

# Workable public job search page
WORKABLE_SEARCH   = "https://jobs.workable.com/?query={query}"


# ── Helpers ───────────────────────────────────────────────────────────────────
def _keywords(role: str) -> List[str]:
    """Split a role into lowercase keyword tokens for matching."""
    return [w.lower() for w in re.split(r"[\s/,]+", role) if len(w) > 1]


def _role_matches(text: str, role: str) -> bool:
    tokens = _keywords(role)
    t = text.lower()
    return any(tok in t for tok in tokens)


async def _fetch_json(session: aiohttp.ClientSession, url: str,
                      semaphore: asyncio.Semaphore,
                      log_cb: Optional[Callable] = None,
                      debug: bool = False) -> Optional[dict]:
    hdrs = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
    if debug and log_cb:
        log_cb(f"[DBG] ▶ REQUEST (JSON)  {url}", "warn")
        log_cb(f"[DBG]   Headers: {hdrs}", "warn")
    async with semaphore:
        await asyncio.sleep(0.3)
        try:
            async with session.get(
                url, headers=hdrs,
                timeout=aiohttp.ClientTimeout(total=15), ssl=True,
            ) as resp:
                body = await resp.json(content_type=None)
                if debug and log_cb:
                    import json as _json
                    preview = _json.dumps(body)[:500]
                    log_cb(f"[DBG] ◀ RESPONSE (JSON)  {url}", "warn")
                    log_cb(f"[DBG]   Status: {resp.status}  Body: {preview}…", "warn")
                if resp.status == 200:
                    return body
                log.debug("Greenhouse HTTP %d  %s", resp.status, url)
        except Exception as exc:
            if debug and log_cb:
                log_cb(f"[DBG] ✗ ERROR  {url}  — {exc}", "error")
            log.debug("Greenhouse error %s — %s", url, exc)
    return None


async def _fetch_text(session: aiohttp.ClientSession, url: str,
                      semaphore: asyncio.Semaphore,
                      log_cb: Optional[Callable] = None,
                      debug: bool = False) -> Optional[str]:
    hdrs = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    }
    if debug and log_cb:
        log_cb(f"[DBG] ▶ REQUEST (HTML)  {url}", "warn")
        log_cb(f"[DBG]   Headers: {hdrs}", "warn")
    async with semaphore:
        await asyncio.sleep(0.3)
        try:
            async with session.get(
                url, headers=hdrs,
                timeout=aiohttp.ClientTimeout(total=15), ssl=True,
            ) as resp:
                body = await resp.text(errors="replace")
                if debug and log_cb:
                    preview = body[:500].replace("\n", " ")
                    log_cb(f"[DBG] ◀ RESPONSE (HTML)  {url}", "warn")
                    log_cb(f"[DBG]   Status: {resp.status}  Body: {preview}…", "warn")
                if resp.status == 200:
                    return body
                log.debug("HTTP %d  %s", resp.status, url)
        except Exception as exc:
            if debug and log_cb:
                log_cb(f"[DBG] ✗ ERROR  {url}  — {exc}", "error")
            log.debug("Fetch error %s — %s", url, exc)
    return None


# ── Greenhouse ─────────────────────────────────────────────────────────────────
async def crawl_greenhouse(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    roles: List[str],
    log_cb: Optional[Callable] = None,
    debug: bool = False,
) -> list:
    from crawler_core import JobListing

    async def _fetch_company(slug: str) -> list:
        url  = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=false"
        data = await _fetch_json(session, url, semaphore, log_cb, debug)
        if not data:
            return []
        found = []
        for job in data.get("jobs", []):
            title    = job.get("title", "")
            location = job.get("location", {}).get("name", "")
            job_url  = job.get("absolute_url", f"https://boards.greenhouse.io/{slug}")
            for role in roles:
                if _role_matches(title, role):
                    found.append(JobListing(
                        portal="Greenhouse",
                        role_query=role,
                        title=title,
                        company=slug.replace("-", " ").title(),
                        location=location,
                        url=job_url,
                        posted="",
                    ))
        return found

    tasks   = [_fetch_company(slug) for slug in GREENHOUSE_COMPANIES]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    jobs    = []
    for r in results:
        if isinstance(r, list):
            jobs.extend(r)

    msg = f"  ✓ {'Greenhouse':<25s} [all roles]  → {len(jobs)} listings"
    log.info(msg)
    if log_cb:
        log_cb(msg, "info")
    return jobs


# ── Workable ──────────────────────────────────────────────────────────────────
async def crawl_workable_xml(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    roles: List[str],
    log_cb: Optional[Callable] = None,
    debug: bool = False,
) -> list:
    from crawler_core import JobListing

    xml_text = await _fetch_text(session, WORKABLE_XML_FEED, semaphore, log_cb, debug)
    if not xml_text:
        if log_cb:
            log_cb("  ⚠ Workable XML feed unavailable", "warn")
        return []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        log.warning("Workable XML parse error: %s", exc)
        return []

    jobs  = []
    items = root.findall(".//job") or root.findall(".//item") or root.findall(".//{*}job")

    for item in items:
        def _text(tag):
            el = item.find(tag)
            return (el.text or "").strip() if el is not None else ""

        title    = _text("title") or _text("name")
        company  = _text("company") or _text("account")
        location = _text("location") or _text("city")
        job_url  = _text("url") or _text("link")
        posted   = _text("created_at") or _text("pubDate") or ""

        for role in roles:
            if _role_matches(title, role):
                jobs.append(JobListing(
                    portal="Workable",
                    role_query=role,
                    title=title, company=company,
                    location=location, url=job_url, posted=posted,
                ))
                break

    msg = f"  ✓ {'Workable XML':<25s} [all roles]  → {len(jobs)} listings"
    log.info(msg)
    if log_cb:
        log_cb(msg, "info")
    return jobs


async def crawl_workable_search(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    roles: List[str],
    log_cb: Optional[Callable] = None,
    debug: bool = False,
) -> list:
    from crawler_core import JobListing

    jobs = []
    for role in roles:
        url  = WORKABLE_SEARCH.replace("{query}", urllib.parse.quote_plus(role))
        html = await _fetch_text(session, url, semaphore, log_cb, debug)
        if not html:
            continue
        soup  = BeautifulSoup(html, "html.parser")
        cards = (soup.select("li[data-ui='job-item']") or
                 soup.select("div[class*='JobCard']") or
                 soup.select("article") or
                 soup.select("li.styles--2zMkH"))
        for card in cards[:30]:
            title   = card.select_one("h3,h2,[class*='title'],[class*='Title']")
            company = card.select_one("[class*='company'],[class*='Company']")
            loc     = card.select_one("[class*='location'],[class*='Location']")
            link    = card.select_one("a[href]")
            t = title.get_text(strip=True)   if title   else ""
            c = company.get_text(strip=True) if company else ""
            l = loc.get_text(strip=True)     if loc     else ""
            u = link["href"]                 if link    else url
            if not u.startswith("http"):
                u = "https://jobs.workable.com" + u
            if t:
                jobs.append(JobListing(
                    portal="Workable Search",
                    role_query=role,
                    title=t, company=c, location=l, url=u, posted="",
                ))

    msg = f"  ✓ {'Workable Search':<25s} [all roles]  → {len(jobs)} listings"
    log.info(msg)
    if log_cb:
        log_cb(msg, "info")
    return jobs


# ── Naukri enhanced ───────────────────────────────────────────────────────────
NAUKRI_SEARCH = "https://www.naukri.com/jobs-in-india?keyWord={query}&experience=0"

async def crawl_naukri(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    roles: List[str],
    log_cb: Optional[Callable] = None,
    debug: bool = False,
) -> list:
    from crawler_core import JobListing

    jobs = []
    for role in roles:
        url  = NAUKRI_SEARCH.replace("{query}", urllib.parse.quote_plus(role))
        html = await _fetch_text(session, url, semaphore, log_cb, debug)
        if not html:
            continue
        soup  = BeautifulSoup(html, "html.parser")
        cards = (soup.select("article.jobTuple") or
                 soup.select("div.jobTuple") or
                 soup.select("div[class*='jobTupleHeader']") or
                 soup.select("div.cust-job-tuple"))
        for card in cards[:30]:
            title   = card.select_one("a.title, a[class*='title'], h2 a")
            company = card.select_one("a.subTitle, a[class*='company'], span[class*='comp']")
            loc     = card.select_one("li.location, span.location, span[class*='loc']")
            posted  = card.select_one("span.date, time, span[class*='date']")
            link    = title or card.select_one("a[href*='naukri.com']")
            t = title.get_text(strip=True)   if title   else ""
            c = company.get_text(strip=True) if company else ""
            l = loc.get_text(strip=True)     if loc     else ""
            p = posted.get_text(strip=True)  if posted  else ""
            u = link.get("href", url)        if link    else url
            if t:
                jobs.append(JobListing(
                    portal="Naukri",
                    role_query=role,
                    title=t, company=c, location=l, url=u, posted=p,
                ))

    msg = f"  ✓ {'Naukri Enhanced':<25s} [all roles]  → {len(jobs)} listings"
    log.info(msg)
    if log_cb:
        log_cb(msg, "info")
    return jobs


# ── Public entry point ────────────────────────────────────────────────────────
async def run_api_sources(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    roles: List[str],
    log_cb: Optional[Callable] = None,
    debug: bool = False,
) -> list:
    """Run all free API/feed sources and return combined JobListing list."""
    if log_cb:
        log_cb("── API Sources: Greenhouse · Workable · Naukri ──", "done")

    results = await asyncio.gather(
        crawl_greenhouse(session, semaphore, roles, log_cb, debug),
        crawl_workable_xml(session, semaphore, roles, log_cb),
        crawl_workable_search(session, semaphore, roles, log_cb),
        crawl_workable_xml(session, semaphore, roles, log_cb, debug),
        crawl_workable_search(session, semaphore, roles, log_cb, debug),
        crawl_naukri(session, semaphore, roles, log_cb, debug),
        return_exceptions=True,
    )
    jobs = []
    for r in results:
        if isinstance(r, list):
            jobs.extend(r)
    return jobs
