# JobFinder Web — Spring Boot + Angular

## Project Structure
```
JobFinder-Web/
├── backend/    ← Spring Boot REST API (Java 17, Maven)
└── frontend/   ← Angular 17 SPA (Node.js / npm)
```

## Backend — Spring Boot

### Prerequisites
- Java 17+
- Maven 3.8+

### Run
```bash
cd backend
mvn spring-boot:run
```
API runs on **http://localhost:8080**

H2 console available at: http://localhost:8080/h2-console

### Key Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/jobs/search` | Start async crawl, returns `crawlId` |
| GET | `/api/jobs/search/{crawlId}/progress` | SSE stream for live progress |
| GET | `/api/jobs?keyword=TPM&region=India` | Paginated job results |
| GET | `/api/jobs/regions` | Supported regions list |
| DELETE | `/api/jobs` | Clear all cached jobs |

---

## Frontend — Angular

### Prerequisites
- Node.js 18+
- Angular CLI: `npm install -g @angular/cli`

### Setup & Run
```bash
cd frontend
npm install
ng serve
```
App runs on **http://localhost:4200**

### Pages
- `/search` — Configure roles, region, date range; see live crawl progress via SSE
- `/results` — Browse, filter, and paginate all crawled jobs

---

## How It Works

1. User fills the search form (roles, region, date range)
2. Angular POSTs to `/api/jobs/search` → Spring Boot kicks off async crawl
3. Backend returns a `crawlId`; Angular opens an SSE connection for live logs
4. Crawler uses **Jsoup** to scrape LinkedIn, Indeed, Naukri, etc.
5. Results are deduped and stored in H2; UI polls `/api/jobs` to display them
