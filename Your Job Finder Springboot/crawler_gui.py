"""
Job Crawler GUI — Tkinter front-end
Lets the user configure roles, region, date-range, then runs the async crawler
and streams live progress into the log pane. Generates an HTML report on finish.
"""

import asyncio
import json
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from datetime import datetime, timedelta, timezone
from pathlib import Path

PREFS_FILE = Path(__file__).parent / "prefs.json"

DEFAULT_PREFS = {
    "roles":       ["TPM", "Technical Program Manager", "AI Engineer",
                    "Payments Engineer", "EMV Engineer", "Engineering Manager"],
    "region":      "Worldwide (all portals)",
    "date_label":  "Last 1 week",
    "concurrency": 5,
    "dedup":       True,
    "html":        True,
    "csv":         True,
    "debug":       False,
    "outdir":      str(Path(__file__).parent),
    "geometry":    "1000x780",
}

def load_prefs() -> dict:
    try:
        data = json.loads(PREFS_FILE.read_text(encoding="utf-8"))
        # fill in any keys added after the user's prefs were saved
        return {**DEFAULT_PREFS, **data}
    except Exception:
        return dict(DEFAULT_PREFS)

def save_prefs(prefs: dict) -> None:
    try:
        PREFS_FILE.write_text(json.dumps(prefs, indent=2, ensure_ascii=False),
                              encoding="utf-8")
    except Exception:
        pass

# ── Constants ─────────────────────────────────────────────────────────────────
SUGGESTED_ROLES = [
    "TPM",
    "Technical Program Manager",
    "AI Engineer",
    "Payments Engineer",
    "EMV Engineer",
    "Engineering Manager",
    "Software Engineer",
    "Product Manager",
    "Data Scientist",
    "DevOps Engineer",
    "Machine Learning Engineer",
    "Backend Engineer",
    "Frontend Engineer",
    "Full Stack Engineer",
    "Site Reliability Engineer",
]

REGIONS = [
    "Worldwide (all portals)",
    "USA",
    "Canada",
    "UK / Europe",
    "Australia / NZ",
    "Asia / India / Singapore",
    "Remote only",
]

DATE_RANGES = {
    "Last 24 hours":  1,
    "Last 3 days":    3,
    "Last 1 week":    7,
    "Last 1 month":   30,
    "Last 1 year":    365,
}

REGION_PORTAL_TAGS = {
    "USA":                    ["usajobs", "dice", "clearance", "collegerecruiter",
                               "hirehive", "aftercollege", "ladders", "jobcase",
                               "craigslist", "snagajob", "lensa"],
    "Canada":                 ["workopolis", "jobbank", "indeed ca", "eluta"],
    "UK / Europe":            ["reed", "totaljobs", "cwjobs", "jobsite", "cv-library",
                               "guardian", "stepstone", "eurojob", "eurengineer"],
    "Australia / NZ":         ["seek au", "seek nz", "careerone"],
    "Asia / India / Singapore":["mycareersfuture", "jobsdb", "naukri", "timesjobs",
                                "shine", "foundit"],
    "Remote only":            ["remote ok", "we work remotely", "remote.co",
                               "remotive", "working nomads", "jobspresso",
                               "justremote", "virtual vocations", "pangian"],
}


# ── GUI ───────────────────────────────────────────────────────────────────────
class CrawlerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self._prefs = load_prefs()

        self.title("Your Job Finder — by Deepak Manktala")
        self.resizable(True, True)
        self.minsize(820, 680)
        self.geometry(self._prefs.get("geometry", "1000x780"))
        self.configure(bg="#1e1e2e")

        self._build_styles()
        self._build_ui()
        self._apply_prefs()
        self._crawl_thread = None

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Styles ────────────────────────────────────────────────────────────────
    def _build_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        bg   = "#1e1e2e"
        card = "#2a2a3e"
        acc  = "#7c6af7"
        fg   = "#cdd6f4"
        muted= "#6c7086"

        s.configure(".",          background=bg,   foreground=fg,   font=("Segoe UI", 10))
        s.configure("Card.TFrame",background=card, relief="flat")
        s.configure("Acc.TButton",background=acc,  foreground="#ffffff",
                    font=("Segoe UI", 10, "bold"), padding=(14, 6))
        s.map("Acc.TButton",
              background=[("active", "#6a58e0"), ("disabled", muted)])
        s.configure("TLabel",     background=bg,   foreground=fg)
        s.configure("Card.TLabel",background=card, foreground=fg)
        s.configure("Muted.TLabel",background=bg,  foreground=muted, font=("Segoe UI", 9))
        s.configure("Head.TLabel",background=bg,   foreground=acc,
                    font=("Segoe UI", 13, "bold"))
        s.configure("TCombobox",  fieldbackground=card, background=card,
                    foreground=fg, selectbackground=acc)
        s.configure("TCheckbutton", background=bg, foreground=fg)
        s.map("TCheckbutton", background=[("active", bg)])
        s.configure("TProgressbar", troughcolor=card, background=acc, thickness=6)

        self._bg = bg; self._card = card; self._acc = acc
        self._fg = fg; self._muted = muted

    # ── UI layout ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        root_pad = dict(padx=20, pady=10)

        # ── header
        hdr = tk.Frame(self, bg=self._bg)
        hdr.pack(fill="x", padx=20, pady=(16, 4))
        ttk.Label(hdr, text="Your Job Finder", style="Head.TLabel").pack(side="left")
        ttk.Label(hdr, text="  powered by CL Electronics Pvt. Ltd. Sri Muktsar Sahib  ·  by Deepak Manktala",
                  style="Muted.TLabel").pack(side="left", pady=(4,0))

        # ── two-column config area
        cfg = tk.Frame(self, bg=self._bg)
        cfg.pack(fill="x", **root_pad)
        cfg.columnconfigure(0, weight=1)
        cfg.columnconfigure(1, weight=1)

        self._build_roles_card(cfg)
        self._build_settings_card(cfg)

        self._progress_var = tk.DoubleVar(value=0)
        self._status_var   = tk.StringVar(value="Ready")

        # ── action buttons — packed BEFORE log so they anchor to bottom
        btn_row = tk.Frame(self, bg=self._bg)
        btn_row.pack(side="bottom", fill="x", padx=20, pady=(8, 16))

        self._run_btn = ttk.Button(btn_row, text="▶  Start Crawl",
                                   style="Acc.TButton", command=self._start_crawl)
        self._run_btn.pack(side="left", padx=(0, 8))

        self._stop_btn = ttk.Button(btn_row, text="■  Stop",
                                    command=self._stop_crawl, state="disabled")
        self._stop_btn.pack(side="left", padx=(0, 8))

        self._html_btn = ttk.Button(btn_row, text="🌐  Open HTML Report",
                                    command=self._open_report, state="disabled")
        self._html_btn.pack(side="left")

        ttk.Label(btn_row, textvariable=self._status_var,
                  style="Muted.TLabel").pack(side="right", pady=4)

        # ── progress bar — also anchored to bottom above buttons
        prog_frame = tk.Frame(self, bg=self._bg)
        prog_frame.pack(side="bottom", fill="x", padx=20, pady=(0, 4))
        ttk.Progressbar(prog_frame, variable=self._progress_var,
                        maximum=100, style="TProgressbar").pack(fill="x")
        ttk.Label(prog_frame, textvariable=self._status_var,
                  style="Muted.TLabel").pack(anchor="w", pady=(2, 0))

        # ── log pane — fills remaining space
        log_frame = ttk.Frame(self, style="Card.TFrame")
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        ttk.Label(log_frame, text="Live Log", style="Card.TLabel",
                  font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(6, 2))

        self._log = scrolledtext.ScrolledText(
            log_frame, bg="#12121c", fg="#a6e3a1",
            font=("Cascadia Code", 9), relief="flat",
            insertbackground="#cdd6f4", state="disabled",
            wrap="word",
        )
        self._log.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._log.tag_config("warn",  foreground="#f9e2af")
        self._log.tag_config("error", foreground="#f38ba8")
        self._log.tag_config("info",  foreground="#a6e3a1")
        self._log.tag_config("done",  foreground="#89dceb")

    # ── Roles card ────────────────────────────────────────────────────────────
    def _build_roles_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding=12)
        card.grid(row=0, column=0, sticky="nsew", padx=(0,8), pady=4)

        ttk.Label(card, text="Target Roles", style="Card.TLabel",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0,6))

        # custom role entry
        entry_row = tk.Frame(card, bg=self._card)
        entry_row.pack(fill="x", pady=(0,6))

        self._role_entry = tk.Entry(entry_row, bg="#1e1e2e", fg=self._fg,
                                    insertbackground=self._fg, relief="flat",
                                    font=("Segoe UI", 10))
        self._role_entry.pack(side="left", fill="x", expand=True, padx=(0,6))
        self._role_entry.bind("<Return>", lambda _: self._add_custom_role())

        ttk.Button(entry_row, text="+ Add", command=self._add_custom_role).pack(side="left")

        # suggestion chips
        chip_outer = tk.Frame(card, bg=self._card)
        chip_outer.pack(fill="x", pady=(0,4))
        ttk.Label(chip_outer, text="Quick-add:", style="Card.TLabel",
                  font=("Segoe UI", 8)).pack(anchor="w")

        chip_frame = tk.Frame(chip_outer, bg=self._card)
        chip_frame.pack(fill="x")
        for i, role in enumerate(SUGGESTED_ROLES[:8]):
            btn = tk.Button(chip_frame, text=role,
                            bg="#3a3a5c", fg=self._fg, relief="flat",
                            font=("Segoe UI", 8), cursor="hand2",
                            padx=6, pady=2,
                            command=lambda r=role: self._add_chip_role(r))
            btn.grid(row=i//4, column=i%4, padx=2, pady=2, sticky="w")

        # selected roles listbox
        ttk.Label(card, text="Selected roles:", style="Card.TLabel",
                  font=("Segoe UI", 9)).pack(anchor="w", pady=(6,2))

        list_frame = tk.Frame(card, bg=self._card)
        list_frame.pack(fill="both", expand=True)

        self._role_listbox = tk.Listbox(
            list_frame, bg="#12121c", fg=self._fg,
            selectbackground=self._acc, relief="flat",
            font=("Segoe UI", 9), height=6,
        )
        self._role_listbox.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(list_frame, orient="vertical",
                           command=self._role_listbox.yview)
        sb.pack(side="right", fill="y")
        self._role_listbox.config(yscrollcommand=sb.set)

        # roles are populated later by _apply_prefs()

        ttk.Button(card, text="✕ Remove selected",
                   command=self._remove_role).pack(anchor="w", pady=(4,0))

    def _add_custom_role(self):
        role = self._role_entry.get().strip()
        if role and role not in self._role_listbox.get(0, "end"):
            self._role_listbox.insert("end", role)
            self._role_entry.delete(0, "end")

    def _add_chip_role(self, role):
        if role not in self._role_listbox.get(0, "end"):
            self._role_listbox.insert("end", role)

    def _remove_role(self):
        for idx in reversed(self._role_listbox.curselection()):
            self._role_listbox.delete(idx)

    # ── Settings card ─────────────────────────────────────────────────────────
    def _build_settings_card(self, parent):
        card = ttk.Frame(parent, style="Card.TFrame", padding=12)
        card.grid(row=0, column=1, sticky="nsew", padx=(8,0), pady=4)

        ttk.Label(card, text="Crawl Settings", style="Card.TLabel",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0,10))

        # region
        ttk.Label(card, text="Region / Geography", style="Card.TLabel").pack(anchor="w")
        self._region_var = tk.StringVar(value=REGIONS[0])
        reg_cb = ttk.Combobox(card, textvariable=self._region_var,
                              values=REGIONS, state="readonly", width=28)
        reg_cb.pack(fill="x", pady=(2,10))

        # date range
        ttk.Label(card, text="Listing Age", style="Card.TLabel").pack(anchor="w")
        self._date_var = tk.StringVar(value="Last 1 week")
        date_cb = ttk.Combobox(card, textvariable=self._date_var,
                               values=list(DATE_RANGES.keys()), state="readonly", width=28)
        date_cb.pack(fill="x", pady=(2,10))

        # options
        ttk.Label(card, text="Options", style="Card.TLabel").pack(anchor="w", pady=(4,2))

        self._dedup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, text="Deduplicate listings",
                        variable=self._dedup_var).pack(anchor="w")

        self._html_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, text="Generate HTML report",
                        variable=self._html_var).pack(anchor="w")

        self._csv_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, text="Save CSV + JSON",
                        variable=self._csv_var).pack(anchor="w")

        self._debug_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card, text="Debug mode (print every request & response)",
                        variable=self._debug_var).pack(anchor="w")

        # concurrency
        ttk.Label(card, text="Concurrency (simultaneous requests)",
                  style="Card.TLabel").pack(anchor="w", pady=(10,2))
        self._concurrency_var = tk.IntVar(value=5)
        conc_frame = tk.Frame(card, bg=self._card)
        conc_frame.pack(fill="x")
        self._conc_scale = ttk.Scale(conc_frame, from_=1, to=15,
                                     variable=self._concurrency_var, orient="horizontal")
        self._conc_scale.pack(side="left", fill="x", expand=True)
        ttk.Label(conc_frame, textvariable=self._concurrency_var,
                  style="Card.TLabel", width=3).pack(side="left")

        # output path
        ttk.Label(card, text="Output directory", style="Card.TLabel").pack(anchor="w", pady=(10,2))
        self._outdir_var = tk.StringVar(value=str(Path(__file__).parent))
        tk.Entry(card, textvariable=self._outdir_var,
                 bg="#1e1e2e", fg=self._fg, insertbackground=self._fg,
                 relief="flat", font=("Segoe UI", 9)).pack(fill="x")

    # ── Crawl orchestration ───────────────────────────────────────────────────
    def _get_config(self):
        roles = list(self._role_listbox.get(0, "end"))
        if not roles:
            messagebox.showwarning("No roles", "Add at least one role before crawling.")
            return None
        return {
            "roles":       roles,
            "region":      self._region_var.get(),
            "days":        DATE_RANGES[self._date_var.get()],
            "date_label":  self._date_var.get(),
            "concurrency": int(self._concurrency_var.get()),
            "dedup":       self._dedup_var.get(),
            "html":        self._html_var.get(),
            "csv":         self._csv_var.get(),
            "debug":       self._debug_var.get(),
            "outdir":      self._outdir_var.get(),
        }

    # ── Prefs persistence ──────────────────────────────────────────────────────
    def _apply_prefs(self):
        p = self._prefs
        self._role_listbox.delete(0, "end")
        for r in p.get("roles", DEFAULT_PREFS["roles"]):
            self._role_listbox.insert("end", r)
        self._region_var.set(p.get("region", DEFAULT_PREFS["region"]))
        self._date_var.set(p.get("date_label", DEFAULT_PREFS["date_label"]))
        self._concurrency_var.set(p.get("concurrency", DEFAULT_PREFS["concurrency"]))
        self._dedup_var.set(p.get("dedup", DEFAULT_PREFS["dedup"]))
        self._html_var.set(p.get("html", DEFAULT_PREFS["html"]))
        self._csv_var.set(p.get("csv", DEFAULT_PREFS["csv"]))
        self._debug_var.set(p.get("debug", DEFAULT_PREFS["debug"]))
        self._outdir_var.set(p.get("outdir", DEFAULT_PREFS["outdir"]))

    def _collect_prefs(self) -> dict:
        return {
            "roles":       list(self._role_listbox.get(0, "end")),
            "region":      self._region_var.get(),
            "date_label":  self._date_var.get(),
            "concurrency": int(self._concurrency_var.get()),
            "dedup":       self._dedup_var.get(),
            "html":        self._html_var.get(),
            "csv":         self._csv_var.get(),
            "debug":       self._debug_var.get(),
            "outdir":      self._outdir_var.get(),
            "geometry":    self.geometry(),
        }

    def _on_close(self):
        save_prefs(self._collect_prefs())
        self.destroy()

    def _start_crawl(self):
        cfg = self._get_config()
        if not cfg:
            return
        save_prefs(self._collect_prefs())   # persist immediately on Start
        self._cfg = cfg
        self._run_btn.config(state="disabled")
        self._stop_btn.config(state="normal")
        self._html_btn.config(state="disabled")
        self._clear_log()
        self._log_line("Your Job Finder — by Deepak Manktala", "done")
        self._log_line(f"Starting crawl — {len(cfg['roles'])} roles × region: {cfg['region']} × {cfg['date_label']}", "done")
        self._progress_var.set(0)
        self._status_var.set("Crawling…")
        self._stop_event = threading.Event()
        self._crawl_thread = threading.Thread(target=self._run_crawl_thread,
                                              args=(cfg,), daemon=True)
        self._crawl_thread.start()

    def _stop_crawl(self):
        if self._stop_event:
            self._stop_event.set()
        self._status_var.set("Stopping…")

    def _run_crawl_thread(self, cfg):
        try:
            import crawler_core as cc
            jobs = asyncio.run(
                cc.run_all_gui(
                    roles=cfg["roles"],
                    region=cfg["region"],
                    max_concurrent=cfg["concurrency"],
                    stop_event=self._stop_event,
                    log_cb=self._log_line,
                    progress_cb=self._set_progress,
                    debug=cfg["debug"],
                )
            )

            # date filter
            cutoff = datetime.now(timezone.utc) - timedelta(days=cfg["days"])
            jobs = _filter_by_date(jobs, cutoff)

            if cfg["dedup"]:
                jobs = _deduplicate(jobs)

            outdir = Path(cfg["outdir"])
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

            if cfg["csv"]:
                cc.save_csv(jobs, str(outdir / f"jobs_{ts}.csv"))
                cc.save_json(jobs, str(outdir / f"jobs_{ts}.json"))

            cc.purge_old_outputs(directory=cfg["outdir"], keep=50)

            self._last_html = None
            if cfg["html"]:
                from report_generator import generate_html
                html_path = outdir / f"jobs_report_{ts}.html"
                generate_html(jobs, str(html_path), cfg)
                self._last_html = str(html_path)

            self.after(0, self._crawl_done, jobs, cfg)

        except Exception as exc:
            import traceback
            self.after(0, self._log_line, f"FATAL: {exc}\n{traceback.format_exc()}", "error")
            self.after(0, self._crawl_finished)

    def _crawl_done(self, jobs, cfg):
        self._log_line(f"\n✅  Done — {len(jobs)} listings collected.", "done")
        by_role = {}
        for j in jobs:
            by_role.setdefault(j.role_query, 0)
            by_role[j.role_query] += 1
        for role, cnt in sorted(by_role.items(), key=lambda x: -x[1]):
            self._log_line(f"   {role:<40s}  {cnt:>4d} listings", "done")
        self._status_var.set(f"Done — {len(jobs)} listings")
        self._progress_var.set(100)
        if self._last_html:
            self._html_btn.config(state="normal")
        self._crawl_finished()

    def _crawl_finished(self):
        self._run_btn.config(state="normal")
        self._stop_btn.config(state="disabled")

    def _open_report(self):
        if self._last_html:
            import webbrowser
            webbrowser.open(f"file:///{self._last_html.replace(chr(92), '/')}")

    # ── Log helpers ───────────────────────────────────────────────────────────
    def _clear_log(self):
        self._log.config(state="normal")
        self._log.delete("1.0", "end")
        self._log.config(state="disabled")

    def _log_line(self, text, tag="info"):
        def _append():
            self._log.config(state="normal")
            self._log.insert("end", text + "\n", tag)
            self._log.see("end")
            self._log.config(state="disabled")
        self.after(0, _append)

    def _set_progress(self, pct: float):
        self.after(0, self._progress_var.set, pct)


# ── Post-processing helpers ───────────────────────────────────────────────────
def _filter_by_date(jobs, cutoff):
    kept = []
    for j in jobs:
        if not j.posted:
            kept.append(j)
            continue
        parsed = _try_parse_date(j.posted)
        if parsed is None or parsed >= cutoff:
            kept.append(j)
    return kept


def _try_parse_date(text: str):
    import re
    text = text.lower().strip()
    now = datetime.now(timezone.utc)
    m = re.search(r"(\d+)\s*(hour|day|week|month|minute)", text)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        delta = {"minute": 60, "hour": 3600, "day": 86400,
                 "week": 604800, "month": 2592000}.get(unit, 0)
        return now - timedelta(seconds=n * delta)
    for fmt in ("%Y-%m-%d", "%b %d, %Y", "%d %b %Y", "%m/%d/%Y"):
        try:
            dt = datetime.strptime(text[:len(fmt)+2], fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def _deduplicate(jobs):
    seen = set()
    out  = []
    for j in jobs:
        key = (j.title.lower().strip(), j.company.lower().strip(),
               j.location.lower().strip())
        if key not in seen:
            seen.add(key)
            out.append(j)
    return out


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = CrawlerGUI()
    app.mainloop()