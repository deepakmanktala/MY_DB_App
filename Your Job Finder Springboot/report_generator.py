"""
HTML Report Generator — produces a polished, self-contained single-file report
from a list of JobListing objects.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List

from crawler_core import JobListing

# ── CSS + JS embedded template ────────────────────────────────────────────────
_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Your Job Finder — by Deepak Manktala — {generated_at}</title>
<style>
/* ── Reset & base ─────────────────────────────────────────────────────── */
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0f0f1a;--surface:#1a1a2e;--card:#22223a;--border:#2e2e4e;
  --acc:#7c6af7;--acc2:#a78bfa;--green:#4ade80;--yellow:#fbbf24;
  --red:#f87171;--muted:#64748b;--text:#e2e8f0;--text2:#94a3b8;
  --radius:12px;--shadow:0 4px 24px rgba(0,0,0,.4);
  font-family:"Segoe UI",system-ui,sans-serif;
}}
html{{scroll-behavior:smooth}}
body{{background:var(--bg);color:var(--text);min-height:100vh;line-height:1.6}}

/* ── Layout ───────────────────────────────────────────────────────────── */
.wrap{{max-width:1400px;margin:0 auto;padding:0 24px 60px}}
header{{
  background:linear-gradient(135deg,#1a1a2e 0%,#16213e 60%,#0f3460 100%);
  border-bottom:1px solid var(--border);padding:32px 40px;
  display:flex;align-items:center;gap:20px;flex-wrap:wrap
}}
header .logo{{font-size:2rem;font-weight:800;letter-spacing:-1px;
  background:linear-gradient(90deg,var(--acc),var(--acc2));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}}
header .meta{{color:var(--text2);font-size:.9rem;line-height:1.8}}
header .meta strong{{color:var(--text)}}

/* ── Stats bar ────────────────────────────────────────────────────────── */
.stats-bar{{display:flex;gap:16px;flex-wrap:wrap;margin:28px 0 20px}}
.stat-card{{
  background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
  padding:18px 24px;flex:1;min-width:140px;text-align:center;
  transition:transform .2s,box-shadow .2s
}}
.stat-card:hover{{transform:translateY(-2px);box-shadow:var(--shadow)}}
.stat-card .num{{font-size:2rem;font-weight:700;color:var(--acc2)}}
.stat-card .lbl{{color:var(--text2);font-size:.82rem;margin-top:2px}}

/* ── Charts ───────────────────────────────────────────────────────────── */
.charts-row{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px}}
@media(max-width:780px){{.charts-row{{grid-template-columns:1fr}}}}
.chart-card{{background:var(--card);border:1px solid var(--border);
  border-radius:var(--radius);padding:20px}}
.chart-card h3{{font-size:.95rem;color:var(--text2);margin-bottom:16px;
  text-transform:uppercase;letter-spacing:.05em}}
.bar-row{{display:flex;align-items:center;gap:10px;margin-bottom:8px;font-size:.85rem}}
.bar-row .name{{width:180px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
  color:var(--text2)}}
.bar-track{{flex:1;background:var(--border);border-radius:4px;height:8px;overflow:hidden}}
.bar-fill{{height:100%;border-radius:4px;
  background:linear-gradient(90deg,var(--acc),var(--acc2));transition:width .6s ease}}
.bar-row .cnt{{width:40px;text-align:right;color:var(--text);font-weight:600}}

/* ── Controls ─────────────────────────────────────────────────────────── */
.controls{{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:16px 20px;
  display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:20px
}}
.controls label{{color:var(--text2);font-size:.85rem;margin-right:4px}}
select,input[type=text]{{
  background:var(--card);color:var(--text);border:1px solid var(--border);
  border-radius:8px;padding:7px 12px;font-size:.88rem;outline:none;
  transition:border-color .2s
}}
select:focus,input[type=text]:focus{{border-color:var(--acc)}}
.btn{{
  background:var(--acc);color:#fff;border:none;border-radius:8px;
  padding:8px 16px;font-size:.88rem;cursor:pointer;font-weight:600;
  transition:background .2s
}}
.btn:hover{{background:var(--acc2)}}
.btn.secondary{{background:var(--card);color:var(--text2);border:1px solid var(--border)}}
.btn.secondary:hover{{border-color:var(--acc);color:var(--text)}}
#result-count{{color:var(--text2);font-size:.85rem;margin-left:auto}}

/* ── Table ────────────────────────────────────────────────────────────── */
.table-wrap{{overflow-x:auto;border-radius:var(--radius);
  border:1px solid var(--border);background:var(--card)}}
table{{width:100%;border-collapse:collapse;font-size:.88rem}}
thead th{{
  background:var(--surface);color:var(--text2);font-weight:600;
  padding:12px 16px;text-align:left;white-space:nowrap;
  border-bottom:1px solid var(--border);cursor:pointer;user-select:none;
  position:sticky;top:0;z-index:2
}}
thead th:hover{{color:var(--acc2)}}
thead th .sort-icon{{margin-left:4px;opacity:.4}}
thead th.asc .sort-icon::after{{content:"↑";opacity:1}}
thead th.desc .sort-icon::after{{content:"↓";opacity:1}}
tbody tr{{border-bottom:1px solid var(--border);transition:background .15s}}
tbody tr:hover{{background:rgba(124,106,247,.08)}}
tbody td{{padding:11px 16px;vertical-align:middle}}
.job-title{{font-weight:600;color:var(--text)}}
.job-title a{{color:var(--acc2);text-decoration:none}}
.job-title a:hover{{text-decoration:underline}}
.company{{color:var(--text);font-weight:500}}
.location{{color:var(--text2);font-size:.83rem}}
.portal-badge{{
  display:inline-block;padding:2px 8px;border-radius:20px;font-size:.75rem;
  font-weight:600;background:rgba(124,106,247,.15);color:var(--acc2);
  border:1px solid rgba(124,106,247,.3)
}}
.posted{{color:var(--muted);font-size:.8rem;white-space:nowrap}}
.role-badge{{
  display:inline-block;padding:2px 8px;border-radius:20px;font-size:.75rem;
  background:rgba(74,222,128,.1);color:var(--green);
  border:1px solid rgba(74,222,128,.25)
}}
.no-results{{text-align:center;padding:60px;color:var(--muted)}}

/* ── Pagination ───────────────────────────────────────────────────────── */
.pagination{{display:flex;gap:6px;justify-content:center;margin-top:20px;flex-wrap:wrap}}
.page-btn{{
  background:var(--card);color:var(--text2);border:1px solid var(--border);
  border-radius:8px;padding:6px 12px;cursor:pointer;font-size:.85rem;
  transition:all .15s
}}
.page-btn:hover,.page-btn.active{{
  background:var(--acc);color:#fff;border-color:var(--acc)
}}

/* ── Footer ───────────────────────────────────────────────────────────── */
footer{{margin-top:48px;text-align:center;color:var(--muted);font-size:.8rem;
  border-top:1px solid var(--border);padding-top:20px}}
</style>
</head>
<body>

<header>
  <div>
    <div class="logo">⚡ Your Job Finder</div>
    <div class="meta">
      <strong>{total}</strong> listings &nbsp;·&nbsp;
      Region: <strong>{region}</strong> &nbsp;·&nbsp;
      Date range: <strong>{date_label}</strong> &nbsp;·&nbsp;
      Generated: <strong>{generated_at}</strong>
    </div>
  </div>
</header>

<div class="wrap">

  <!-- Stats -->
  <div class="stats-bar">
    <div class="stat-card"><div class="num">{total}</div><div class="lbl">Total Listings</div></div>
    <div class="stat-card"><div class="num">{unique_companies}</div><div class="lbl">Companies</div></div>
    <div class="stat-card"><div class="num">{portals_hit}</div><div class="lbl">Portals</div></div>
    <div class="stat-card"><div class="num">{roles_count}</div><div class="lbl">Roles Searched</div></div>
  </div>

  <!-- Charts -->
  <div class="charts-row">
    <div class="chart-card">
      <h3>Top Portals</h3>
      {portal_bars}
    </div>
    <div class="chart-card">
      <h3>By Role</h3>
      {role_bars}
    </div>
  </div>

  <!-- Controls -->
  <div class="controls">
    <label>Search</label>
    <input type="text" id="search-box" placeholder="title, company, location…" oninput="applyFilters()" style="width:220px">

    <label>Role</label>
    <select id="filter-role" onchange="applyFilters()">
      <option value="">All roles</option>
      {role_options}
    </select>

    <label>Portal</label>
    <select id="filter-portal" onchange="applyFilters()">
      <option value="">All portals</option>
      {portal_options}
    </select>

    <button class="btn secondary" onclick="resetFilters()">Reset</button>
    <button class="btn" onclick="exportVisible()">⬇ Export CSV</button>
    <span id="result-count"></span>
  </div>

  <!-- Table -->
  <div class="table-wrap">
    <table id="jobs-table">
      <thead>
        <tr>
          <th onclick="sortBy('title')" data-col="title">Title<span class="sort-icon"></span></th>
          <th onclick="sortBy('company')" data-col="company">Company<span class="sort-icon"></span></th>
          <th onclick="sortBy('location')" data-col="location">Location<span class="sort-icon"></span></th>
          <th onclick="sortBy('portal')" data-col="portal">Portal<span class="sort-icon"></span></th>
          <th onclick="sortBy('role_query')" data-col="role_query">Role Query<span class="sort-icon"></span></th>
          <th onclick="sortBy('posted')" data-col="posted">Posted<span class="sort-icon"></span></th>
        </tr>
      </thead>
      <tbody id="jobs-body"></tbody>
    </table>
    <div class="no-results" id="no-results" style="display:none">No listings match your filters.</div>
  </div>

  <div class="pagination" id="pagination"></div>
</div>

<footer>
  <strong>Your Job Finder</strong> &nbsp;·&nbsp; Powered by <strong>CL Electronics Pvt. Ltd. Sri Muktsar Sahib</strong> &nbsp;·&nbsp; By <strong>Deepak Manktala</strong> &nbsp;·&nbsp; {generated_at}
</footer>

<script>
const DATA = {data_json};

const PAGE_SIZE = 50;
let filtered = [...DATA];
let currentPage = 1;
let sortCol = "";
let sortDir = 1;

function applyFilters() {{
  const q       = document.getElementById("search-box").value.toLowerCase();
  const role    = document.getElementById("filter-role").value;
  const portal  = document.getElementById("filter-portal").value;
  filtered = DATA.filter(j => {{
    if (role   && j.role_query !== role)   return false;
    if (portal && j.portal     !== portal) return false;
    if (q) {{
      const hay = (j.title + j.company + j.location).toLowerCase();
      if (!hay.includes(q)) return false;
    }}
    return true;
  }});
  currentPage = 1;
  render();
}}

function resetFilters() {{
  document.getElementById("search-box").value = "";
  document.getElementById("filter-role").value = "";
  document.getElementById("filter-portal").value = "";
  filtered = [...DATA];
  currentPage = 1;
  render();
}}

function sortBy(col) {{
  if (sortCol === col) sortDir *= -1;
  else {{ sortCol = col; sortDir = 1; }}
  document.querySelectorAll("thead th").forEach(th => {{
    th.classList.remove("asc","desc");
    if (th.dataset.col === col) th.classList.add(sortDir===1?"asc":"desc");
  }});
  filtered.sort((a,b) => {{
    const av = (a[col]||"").toLowerCase();
    const bv = (b[col]||"").toLowerCase();
    return av < bv ? -sortDir : av > bv ? sortDir : 0;
  }});
  render();
}}

function render() {{
  const tbody  = document.getElementById("jobs-body");
  const noRes  = document.getElementById("no-results");
  const count  = document.getElementById("result-count");
  const total  = filtered.length;
  count.textContent = total + " result" + (total===1?"":"s");

  if (total === 0) {{
    tbody.innerHTML = "";
    noRes.style.display = "block";
    document.getElementById("pagination").innerHTML = "";
    return;
  }}
  noRes.style.display = "none";

  const start = (currentPage-1)*PAGE_SIZE;
  const page  = filtered.slice(start, start+PAGE_SIZE);

  tbody.innerHTML = page.map(j => `
    <tr>
      <td class="job-title">
        ${{j.url ? `<a href="${{j.url}}" target="_blank" rel="noopener">${{esc(j.title)}}</a>` : esc(j.title)}}
      </td>
      <td class="company">${{esc(j.company||"—")}}</td>
      <td class="location">${{esc(j.location||"—")}}</td>
      <td><span class="portal-badge">${{esc(j.portal)}}</span></td>
      <td><span class="role-badge">${{esc(j.role_query)}}</span></td>
      <td class="posted">${{esc(j.posted||"—")}}</td>
    </tr>`).join("");

  renderPagination(total);
}}

function renderPagination(total) {{
  const pages = Math.ceil(total/PAGE_SIZE);
  const el    = document.getElementById("pagination");
  if (pages <= 1) {{ el.innerHTML = ""; return; }}
  let html = "";
  for (let i=1; i<=pages; i++) {{
    html += `<button class="page-btn${{i===currentPage?" active":""}}"
      onclick="goPage(${{i}})">${{i}}</button>`;
  }}
  el.innerHTML = html;
}}

function goPage(n) {{ currentPage=n; render(); window.scrollTo({{top:0,behavior:"smooth"}}); }}

function esc(s) {{
  return String(s||"")
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;");
}}

function exportVisible() {{
  const fields = ["title","company","location","portal","role_query","posted","url","scraped_at"];
  const rows   = [fields.join(",")];
  filtered.forEach(j => {{
    rows.push(fields.map(f => `"${{(j[f]||"").replace(/"/g,'""')}}"`).join(","));
  }});
  const blob = new Blob([rows.join("\\n")], {{type:"text/csv"}});
  const a    = document.createElement("a");
  a.href     = URL.createObjectURL(blob);
  a.download = "jobs_filtered.csv";
  a.click();
}}

// Init
applyFilters();
</script>
</body>
</html>"""


# ── Bar chart helper ───────────────────────────────────────────────────────────
def _bar_rows(counter: Counter, top_n: int = 10) -> str:
    items = counter.most_common(top_n)
    if not items:
        return "<p style='color:var(--muted)'>No data</p>"
    max_val = items[0][1]
    html = ""
    for name, cnt in items:
        pct = cnt / max_val * 100
        html += (
            f'<div class="bar-row">'
            f'<span class="name" title="{name}">{name}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{pct:.1f}%"></div></div>'
            f'<span class="cnt">{cnt}</span>'
            f'</div>'
        )
    return html


def _options(values) -> str:
    return "".join(f'<option value="{v}">{v}</option>' for v in sorted(values))


# ── Public API ────────────────────────────────────────────────────────────────
def generate_html(jobs: List[JobListing], output_path: str, cfg: dict) -> str:
    data = [asdict(j) for j in jobs]

    portal_counter  = Counter(j.portal for j in jobs)
    role_counter    = Counter(j.role_query for j in jobs)
    unique_companies = len({j.company.strip().lower() for j in jobs if j.company})
    portals_hit      = len(portal_counter)

    html = _HTML_TEMPLATE.format(
        total           = len(jobs),
        unique_companies= unique_companies,
        portals_hit     = portals_hit,
        roles_count     = len(role_counter),
        region          = cfg.get("region", "Worldwide"),
        date_label      = cfg.get("date_label", "All time"),
        generated_at    = datetime.now().strftime("%Y-%m-%d %H:%M"),
        portal_bars     = _bar_rows(portal_counter, top_n=10),
        role_bars       = _bar_rows(role_counter, top_n=15),
        role_options    = _options(role_counter.keys()),
        portal_options  = _options(portal_counter.keys()),
        data_json       = json.dumps(data, ensure_ascii=False),
    )

    Path(output_path).write_text(html, encoding="utf-8")
    return output_path


# ── CLI usage ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, csv as _csv
    from crawler_core import JobListing

    csv_path = sys.argv[1] if len(sys.argv) > 1 else "jobs_output.csv"
    jobs: List[JobListing] = []
    with open(csv_path, encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            jobs.append(JobListing(**{k: row.get(k, "") for k in
                ["portal","role_query","title","company","location","url","posted","scraped_at"]}))

    out = csv_path.replace(".csv", "_report.html")
    cfg = {"region": "Worldwide (all portals)", "date_label": "All time"}
    generate_html(jobs, out, cfg)
    print(f"Report saved → {out}")
