# JobFinder Android — Kotlin + Spring Boot REST API

## Project Structure
```
JobFinder-Android/
├── backend/    ← Spring Boot REST API (Java 17, Maven) — port 8081
└── android/    ← Kotlin Android app (MVVM, Retrofit, Navigation Component)
```

## Backend — Spring Boot REST API

### Prerequisites
- Java 17+
- Maven 3.8+

### Run
```bash
cd backend
mvn spring-boot:run
```
API runs on **http://localhost:8081**

### Key Endpoints (API v1)
| Method | URL | Description |
|--------|-----|-------------|
| POST | `/api/v1/jobs/search` | Crawl jobs synchronously; returns list |
| GET | `/api/v1/jobs` | Paginated results with filters |
| GET | `/api/v1/jobs/{id}` | Single job detail |
| GET | `/api/v1/jobs/regions` | Supported regions |
| GET | `/api/v1/jobs/stats` | Total job count |

### Request Example
```json
POST /api/v1/jobs/search
{
  "roles": ["TPM", "Engineering Manager"],
  "region": "India",
  "dateRange": "Last 1 week"
}
```

---

## Android App — Kotlin

### Prerequisites
- Android Studio Hedgehog (2023.1.1) or later
- Android SDK 34
- Kotlin 1.9+

### Setup
1. Open `android/` folder in Android Studio
2. Let Gradle sync complete
3. Ensure backend is running (see above)
4. Run on emulator or device

> **Note:** The emulator uses `10.0.2.2` to reach host machine's localhost.
> For a real device, replace `10.0.2.2` in `RetrofitClient.kt` with your machine's LAN IP.

### Architecture (MVVM)
```
UI Layer          → SearchFragment, ResultsFragment, JobAdapter
ViewModel Layer   → JobViewModel (LiveData + Coroutines)
Data Layer        → JobRepository → JobApiService (Retrofit) → Spring Boot API
```

### App Flow
1. **Search Screen** — user enters job roles, picks region & date range, taps "Find Jobs"
2. Backend crawls LinkedIn, Indeed, Naukri etc. (synchronous for mobile)
3. **Results Screen** — RecyclerView cards with title, company, location, source badge
4. Tap any card → opens job URL in browser

### Build APK
```
Build → Build Bundle(s)/APK(s) → Build APK(s)
```
Output: `android/app/build/outputs/apk/debug/app-debug.apk`
