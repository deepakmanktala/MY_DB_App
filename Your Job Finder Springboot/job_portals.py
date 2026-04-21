"""
Curated list of 100+ major English-language HTTPS job portals, organized by category.
All portals are publicly accessible without login for job listings.
"""

JOB_PORTALS = [
    # ── Global Aggregators ──────────────────────────────────────────────────────
    {"name": "Indeed",           "base": "https://www.indeed.com",          "search": "https://www.indeed.com/jobs?q={query}&l="},
    {"name": "LinkedIn",         "base": "https://www.linkedin.com",        "search": "https://www.linkedin.com/jobs/search/?keywords={query}"},
    {"name": "Glassdoor",        "base": "https://www.glassdoor.com",       "search": "https://www.glassdoor.com/Job/jobs.htm?suggestCount=0&suggestChosen=false&clickSource=searchBtn&typedKeyword={query}&sc.keyword={query}"},
    {"name": "Monster",          "base": "https://www.monster.com",         "search": "https://www.monster.com/jobs/search?q={query}"},
    {"name": "ZipRecruiter",     "base": "https://www.ziprecruiter.com",    "search": "https://www.ziprecruiter.com/jobs-search?search={query}"},
    {"name": "SimplyHired",      "base": "https://www.simplyhired.com",     "search": "https://www.simplyhired.com/search?q={query}"},
    {"name": "CareerBuilder",    "base": "https://www.careerbuilder.com",   "search": "https://www.careerbuilder.com/jobs?keywords={query}"},
    {"name": "Jooble",           "base": "https://jooble.org",              "search": "https://jooble.org/jobs-{query}"},
    {"name": "Adzuna",           "base": "https://www.adzuna.com",          "search": "https://www.adzuna.com/search?q={query}"},
    {"name": "Trovit Jobs",      "base": "https://jobs.trovit.com",         "search": "https://jobs.trovit.com/index.php/cod.search_jobs/what.{query}"},
    {"name": "JobisJob",         "base": "https://us.jobisjob.com",         "search": "https://us.jobisjob.com/jobs/search/{query}"},
    {"name": "Neuvoo",           "base": "https://neuvoo.com",              "search": "https://neuvoo.com/jobs/?q={query}"},
    {"name": "Jobrapido",        "base": "https://us.jobrapido.com",        "search": "https://us.jobrapido.com/jobpreview/search?w={query}"},
    {"name": "JobisJob US",      "base": "https://us.jobisjob.com",         "search": "https://us.jobisjob.com/jobs/search/{query}"},

    # ── USA-Specific ────────────────────────────────────────────────────────────
    {"name": "USAJobs",          "base": "https://www.usajobs.gov",         "search": "https://www.usajobs.gov/Search/Results?k={query}"},
    {"name": "Dice",             "base": "https://www.dice.com",            "search": "https://www.dice.com/jobs?q={query}&countryCode=US"},
    {"name": "ClearanceJobs",    "base": "https://www.clearancejobs.com",   "search": "https://www.clearancejobs.com/jobs?keyword={query}"},
    {"name": "CollegeRecruiter", "base": "https://www.collegerecruiter.com","search": "https://www.collegerecruiter.com/jobs/#!?keywords={query}"},
    {"name": "HireHive",         "base": "https://hirehive.com",            "search": "https://hirehive.com/jobs/?search={query}"},
    {"name": "AfterCollege",     "base": "https://www.aftercollege.com",    "search": "https://www.aftercollege.com/cf/search-results?keywords={query}"},
    {"name": "Ladders",          "base": "https://www.theladders.com",      "search": "https://www.theladders.com/jobs/search-jobs?title={query}"},
    {"name": "Jobcase",          "base": "https://www.jobcase.com",         "search": "https://www.jobcase.com/search?q={query}"},

    # ── UK / Europe ─────────────────────────────────────────────────────────────
    {"name": "Reed UK",          "base": "https://www.reed.co.uk",          "search": "https://www.reed.co.uk/jobs/{query}-jobs"},
    {"name": "Totaljobs",        "base": "https://www.totaljobs.com",       "search": "https://www.totaljobs.com/jobs/{query}"},
    {"name": "CWJobs",           "base": "https://www.cwjobs.co.uk",        "search": "https://www.cwjobs.co.uk/jobs/{query}"},
    {"name": "Jobsite UK",       "base": "https://www.jobsite.co.uk",       "search": "https://www.jobsite.co.uk/jobs/{query}"},
    {"name": "CV-Library",       "base": "https://www.cv-library.co.uk",    "search": "https://www.cv-library.co.uk/search-jobs?q={query}&us=1"},
    {"name": "Guardian Jobs",    "base": "https://jobs.theguardian.com",    "search": "https://jobs.theguardian.com/jobs/{query}/"},
    {"name": "EuroEngineerJobs", "base": "https://www.eurengineeringjobs.com","search":"https://www.eurengineeringjobs.com/search?query={query}"},
    {"name": "StepStone",        "base": "https://www.stepstone.co.uk",     "search": "https://www.stepstone.co.uk/jobs/{query}"},
    {"name": "Efinancialcareers","base": "https://www.efinancialcareers.com","search":"https://www.efinancialcareers.com/search?q={query}"},
    {"name": "EuroJobSites",     "base": "https://www.eurojobsites.com",    "search": "https://www.eurojobsites.com/jobs/?keywords={query}"},

    # ── Australia / NZ ──────────────────────────────────────────────────────────
    {"name": "Seek AU",          "base": "https://www.seek.com.au",         "search": "https://www.seek.com.au/{query}-jobs"},
    {"name": "Seek NZ",          "base": "https://www.seek.co.nz",          "search": "https://www.seek.co.nz/{query}-jobs"},
    {"name": "JobsDB HK",        "base": "https://hk.jobsdb.com",           "search": "https://hk.jobsdb.com/hk/search-jobs/{query}/1"},
    {"name": "CareerOne",        "base": "https://www.careerone.com.au",    "search": "https://www.careerone.com.au/jobs/?q={query}"},

    # ── Canada ──────────────────────────────────────────────────────────────────
    {"name": "Workopolis",       "base": "https://www.workopolis.com",      "search": "https://www.workopolis.com/jobsearch/find-jobs?ak={query}"},
    {"name": "JobBank Canada",   "base": "https://www.jobbank.gc.ca",       "search": "https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={query}"},
    {"name": "Indeed CA",        "base": "https://ca.indeed.com",           "search": "https://ca.indeed.com/jobs?q={query}"},
    {"name": "Eluta",            "base": "https://www.eluta.ca",            "search": "https://www.eluta.ca/search?q={query}"},

    # ── Asia / Singapore / India ────────────────────────────────────────────────
    {"name": "Indeed India",     "base": "https://www.indeed.co.in",        "search": "https://www.indeed.co.in/jobs?q={query}"},
    {"name": "MyCareersFuture",  "base": "https://www.mycareersfuture.gov.sg","search":"https://www.mycareersfuture.gov.sg/search?search={query}&sortBy=new_posting_date"},
    {"name": "JobsDB SG",        "base": "https://sg.jobsdb.com",           "search": "https://sg.jobsdb.com/sg/search-jobs/{query}/1"},
    {"name": "Naukri",           "base": "https://www.naukri.com",          "search": "https://www.naukri.com/{query}-jobs"},
    {"name": "TimesJobs",        "base": "https://www.timesjobs.com",       "search": "https://www.timesjobs.com/candidate/job-search.html?searchType=personalizedSearch&from=submit&txtKeywords={query}"},
    {"name": "Shine",            "base": "https://www.shine.com",           "search": "https://www.shine.com/job-search/{query}-jobs"},
    {"name": "Foundit",          "base": "https://www.foundit.in",          "search": "https://www.foundit.in/srp/results?query={query}"},

    # ── Tech-Focused ────────────────────────────────────────────────────────────
    {"name": "Hired",            "base": "https://hired.com",               "search": "https://hired.com/jobs?q={query}"},
    {"name": "Wellfound",        "base": "https://wellfound.com",           "search": "https://wellfound.com/role/r/{query}"},
    {"name": "Hackerrank Jobs",  "base": "https://www.hackerrank.com",      "search": "https://www.hackerrank.com/jobs/search?q={query}"},
    {"name": "TechCareers",      "base": "https://www.techcareers.com",     "search": "https://www.techcareers.com/search/?q={query}"},
    {"name": "CrunchBoard",      "base": "https://www.crunchboard.com",     "search": "https://www.crunchboard.com/jobs?query={query}"},
    {"name": "ITJobsWatch",      "base": "https://www.itjobswatch.co.uk",   "search": "https://www.itjobswatch.co.uk/jobs/uk/{query}.do"},
    {"name": "Stack Overflow",   "base": "https://stackoverflow.com",       "search": "https://stackoverflow.com/jobs?q={query}"},
    {"name": "GitHub Jobs",      "base": "https://jobs.github.com",         "search": "https://jobs.github.com/positions?description={query}"},
    {"name": "Hacker News Jobs", "base": "https://news.ycombinator.com",    "search": "https://news.ycombinator.com/jobs"},
    {"name": "Authentic Jobs",   "base": "https://authenticjobs.com",       "search": "https://authenticjobs.com/?search={query}"},
    {"name": "We Work Remotely", "base": "https://weworkremotely.com",      "search": "https://weworkremotely.com/remote-jobs/search?term={query}"},
    {"name": "Remote.co",        "base": "https://remote.co",               "search": "https://remote.co/remote-jobs/search/?search_keywords={query}"},
    {"name": "Remotive",         "base": "https://remotive.com",            "search": "https://remotive.com/remote-jobs?search={query}"},
    {"name": "Working Nomads",   "base": "https://www.workingnomads.com",   "search": "https://www.workingnomads.com/jobs?category={query}"},
    {"name": "Jobspresso",       "base": "https://jobspresso.co",           "search": "https://jobspresso.co/?s={query}"},
    {"name": "Remote OK",        "base": "https://remoteok.com",            "search": "https://remoteok.com/remote-{query}-jobs"},
    {"name": "Outsourcely",      "base": "https://www.outsourcely.com",     "search": "https://www.outsourcely.com/remote-workers/search/?q={query}"},
    {"name": "JustRemote",       "base": "https://justremote.co",           "search": "https://justremote.co/remote-jobs?search={query}"},
    {"name": "Virtual Vocations","base": "https://www.virtualvocations.com","search":"https://www.virtualvocations.com/jobs/search#search={query}"},
    {"name": "Pangian",          "base": "https://pangian.com",             "search": "https://pangian.com/job-travel-remote/?s={query}"},

    # ── Finance / Payments ──────────────────────────────────────────────────────
    {"name": "eFinancialCareers","base": "https://www.efinancialcareers.com","search":"https://www.efinancialcareers.com/search?q={query}"},
    {"name": "iiBanker",         "base": "https://www.iibanker.com",        "search": "https://www.iibanker.com/jobs?keywords={query}"},
    {"name": "BankingJobs",      "base": "https://www.bankingjobs.com",     "search": "https://www.bankingjobs.com/search-results.cfm?keywords={query}"},
    {"name": "FinancialJobBank", "base": "https://www.financialjobbank.com","search":"https://www.financialjobbank.com/search/?search_keywords={query}"},
    {"name": "PaymentsJobs",     "base": "https://www.paymentsjobs.com",    "search": "https://www.paymentsjobs.com/jobs?keywords={query}"},
    {"name": "Fintech Jobs",     "base": "https://fintechjobs.com",         "search": "https://fintechjobs.com/?s={query}"},

    # ── Executive / Management ──────────────────────────────────────────────────
    {"name": "ExecuNet",         "base": "https://www.execunet.com",        "search": "https://www.execunet.com/job-search?keywords={query}"},
    {"name": "BlueSteps",        "base": "https://www.bluesteps.com",       "search": "https://www.bluesteps.com/jobs/Search.aspx?keywords={query}"},
    {"name": "SpencerStuart",    "base": "https://www.spencerstuart.com",   "search": "https://www.spencerstuart.com/search#q={query}&t=Jobs"},
    {"name": "IvyExec",          "base": "https://www.ivyexec.com",         "search": "https://www.ivyexec.com/jobs?keyword={query}"},

    # ── Staffing / Recruiting Agencies ─────────────────────────────────────────
    {"name": "Hays",             "base": "https://www.hays.com",            "search": "https://www.hays.com/jobs/search/q-{query}"},
    {"name": "Robert Half",      "base": "https://www.roberthalf.com",      "search": "https://www.roberthalf.com/jobs/all-jobs?keywords={query}"},
    {"name": "Michael Page",     "base": "https://www.michaelpage.com",     "search": "https://www.michaelpage.com/jobs/{query}"},
    {"name": "Kforce",           "base": "https://www.kforce.com",          "search": "https://www.kforce.com/find-a-job/?keyword={query}"},
    {"name": "TEKsystems",       "base": "https://www.teksystems.com",      "search": "https://www.teksystems.com/en/careers/job-search?q={query}"},
    {"name": "Adecco",           "base": "https://www.adeccousa.com",       "search": "https://www.adeccousa.com/jobs/search-results/?keyword={query}"},
    {"name": "Randstad",         "base": "https://www.randstad.com",        "search": "https://www.randstad.com/jobs/q-{query}/"},
    {"name": "Manpower",         "base": "https://www.manpower.com",        "search": "https://www.manpower.com/ManpowerUSA/jobs/search?q={query}"},
    {"name": "Insight Global",   "base": "https://insightglobal.com",       "search": "https://insightglobal.com/jobs/?s={query}"},
    {"name": "Apex Systems",     "base": "https://www.apexsystems.com",     "search": "https://www.apexsystems.com/jobs/search#q={query}"},

    # ── ATS / Company Career Boards (public Greenhouse/Lever feeds) ─────────────
    {"name": "Greenhouse Board", "base": "https://boards.greenhouse.io",    "search": "https://boards.greenhouse.io/"},
    {"name": "Lever Postings",   "base": "https://jobs.lever.co",           "search": "https://jobs.lever.co/"},
    {"name": "Workday Jobs",     "base": "https://www.myworkdayjobs.com",   "search": "https://www.myworkdayjobs.com/en-US/External/jobs"},
    {"name": "SmartRecruiters",  "base": "https://jobs.smartrecruiters.com","search":"https://jobs.smartrecruiters.com/?keyword={query}"},
    {"name": "Ashby HQ",         "base": "https://jobs.ashbyhq.com",        "search": "https://jobs.ashbyhq.com/"},
    {"name": "Rippling Jobs",    "base": "https://www.rippling.com",        "search": "https://www.rippling.com/jobs"},
    {"name": "Jobvite",          "base": "https://jobs.jobvite.com",        "search": "https://jobs.jobvite.com/"},

    # ── Niche / Specialized ─────────────────────────────────────────────────────
    {"name": "PM Jobs",          "base": "https://www.pmjobs.net",          "search": "https://www.pmjobs.net/search/?q={query}"},
    {"name": "Product Hired",    "base": "https://www.producthired.com",    "search": "https://www.producthired.com/jobs/?search={query}"},
    {"name": "Idealist",         "base": "https://www.idealist.org",        "search": "https://www.idealist.org/en/jobs?q={query}"},
    {"name": "Mediabistro",      "base": "https://www.mediabistro.com",     "search": "https://www.mediabistro.com/jobs/search/?q={query}"},
    {"name": "Mashable Jobs",    "base": "https://jobs.mashable.com",       "search": "https://jobs.mashable.com/jobs/search?q={query}"},
    {"name": "Built In",         "base": "https://builtin.com",             "search": "https://builtin.com/jobs?search={query}"},
    {"name": "Built In NYC",     "base": "https://www.builtinnyc.com",      "search": "https://www.builtinnyc.com/jobs?search={query}"},
    {"name": "Built In Chicago", "base": "https://www.builtinchicago.org",  "search": "https://www.builtinchicago.org/jobs?search={query}"},
    {"name": "Built In Austin",  "base": "https://www.builtinaustin.com",   "search": "https://www.builtinaustin.com/jobs?search={query}"},
    {"name": "Built In SF",      "base": "https://www.builtinsf.com",       "search": "https://www.builtinsf.com/jobs?search={query}"},
    {"name": "Built In Seattle", "base": "https://www.builtinseattle.com",  "search": "https://www.builtinseattle.com/jobs?search={query}"},
    {"name": "Built In Boston",  "base": "https://www.builtinboston.com",   "search": "https://www.builtinboston.com/jobs?search={query}"},
    {"name": "Built In Colorado","base": "https://www.builtincolorado.com", "search": "https://www.builtincolorado.com/jobs?search={query}"},
    {"name": "AngelList",        "base": "https://angel.co",                "search": "https://angel.co/jobs#find/f!%7B%22keywords%22%3A%5B%22{query}%22%5D%7D"},
    {"name": "Y Combinator",     "base": "https://www.ycombinator.com",     "search": "https://www.ycombinator.com/jobs/role/{query}"},
    {"name": "Craigslist Jobs",  "base": "https://www.craigslist.org",      "search": "https://www.craigslist.org/search/jjj?query={query}"},
    {"name": "Jobble",           "base": "https://www.jobble.com",          "search": "https://www.jobble.com/jobs?q={query}"},
    {"name": "Snagajob",         "base": "https://www.snagajob.com",        "search": "https://www.snagajob.com/jobs?keyword={query}"},
    {"name": "Lensa",            "base": "https://lensa.com",               "search": "https://lensa.com/jobs-near-me/search?q={query}"},
    {"name": "Talent.com",       "base": "https://www.talent.com",          "search": "https://www.talent.com/jobs?k={query}"},
    {"name": "Jobted",           "base": "https://www.jobted.com",          "search": "https://www.jobted.com/search?q={query}"},
    {"name": "Jobbatical",       "base": "https://jobbatical.com",          "search": "https://jobbatical.com/explore?keyword={query}"},
    {"name": "Relocate.me",      "base": "https://relocate.me",             "search": "https://relocate.me/search?query={query}"},
    {"name": "F6S Jobs",         "base": "https://www.f6s.com",             "search": "https://www.f6s.com/jobs?search={query}"},
    {"name": "Startup Jobs",     "base": "https://startup.jobs",            "search": "https://startup.jobs/?remote=true&q={query}"},
    {"name": "Underdog.io",      "base": "https://underdog.io",             "search": "https://underdog.io/candidate/jobs?search={query}"},
    {"name": "Cord",             "base": "https://cord.co",                 "search": "https://cord.co/jobs?q={query}"},
    {"name": "Pallet Jobs",      "base": "https://pallet.xyz",              "search": "https://pallet.xyz/list"},
    {"name": "Contra",           "base": "https://contra.com",              "search": "https://contra.com/opportunity?q={query}"},
    {"name": "Toptal",           "base": "https://www.toptal.com",          "search": "https://www.toptal.com/talent/apply"},
]

# Search roles (used as query terms)
TARGET_ROLES = [
    "TPM",
    "Technical Program Manager",
    "AI Engineer",
    "Payments Engineer",
    "EMV Engineer",
    "Engineering Manager",
]