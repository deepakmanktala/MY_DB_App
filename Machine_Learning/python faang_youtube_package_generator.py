#!/usr/bin/env python3
"""
YouTube package generator for:
FAANG Database Designs

What this script does
---------------------
Creates a ready-to-produce project folder with:
- youtube_script.md            : full voiceover script
- storyboard.csv              : scene-by-scene plan
- visual_prompts.md           : prompts for thumbnails / slides / visuals
- capcut_canva_checklist.md   : exact workflow for free online tools
- youtube_metadata.md         : title, description, chapters, tags
- assets_to_download.csv      : what stock clips/images to fetch
- shot_list.json              : structured scene data for automation
- thumbnail_text.txt          : thumbnail copy options
- narration_chunks.txt        : shorter chunks for TTS or manual voiceover
- ffmpeg_notes.md             : optional local assembly notes

How to use
----------
1) Run:
   python faang_youtube_package_generator.py

2) Open the generated folder:
   faang_database_youtube_package/

3) Use ONLY free tools if you want:
   - Canva video editor or CapCut online for editing
   - Pexels / Pixabay for free stock footage
   - Your own voice or any TTS tool you prefer
   - YouTube Studio for upload

This script does not download assets or upload videos.
It prepares everything you need so production is much faster.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from textwrap import dedent


PROJECT_DIR = Path("faang_database_youtube_package")


SCENES = [
    {
        "scene": 1,
        "title": "Hook",
        "duration_sec": 20,
        "on_screen_text": "FAANG Database Architecture",
        "visual": "Fast-moving network/global internet animation, server racks, database icons, big-brand style motion graphics.",
        "voiceover": (
            "Ever wondered what databases power companies like Google, Amazon, and Netflix? "
            "These platforms serve billions of users and store huge amounts of data. "
            "And the key insight is this: they do not rely on one database. "
            "They use multiple specialized databases working together."
        ),
        "asset_keywords": "global network, cloud architecture, data center, databases, digital world",
    },
    {
        "scene": 2,
        "title": "Why one database is not enough",
        "duration_sec": 25,
        "on_screen_text": "One database cannot do everything",
        "visual": "Single overloaded database icon with lines coming from search, analytics, transactions, cache, graph, streaming.",
        "voiceover": (
            "A single database cannot efficiently handle every workload: "
            "billions of reads, massive writes, real-time analytics, search, graph traversal, and strict transactions. "
            "That is why hyperscale systems use the right database for the right job."
        ),
        "asset_keywords": "overloaded database, scaling bottleneck, system design",
    },
    {
        "scene": 3,
        "title": "Polyglot persistence",
        "duration_sec": 30,
        "on_screen_text": "Polyglot Persistence",
        "visual": "Six-category layout: key-value, document, graph, wide-column, relational, analytics warehouse.",
        "voiceover": (
            "This approach is called polyglot persistence. "
            "It means using different database types for different access patterns. "
            "In this video, we will map the major database categories to real tools used in large systems."
        ),
        "asset_keywords": "polyglot persistence, database categories infographic",
    },
    {
        "scene": 4,
        "title": "Key-value databases",
        "duration_sec": 50,
        "on_screen_text": "Key-Value: Redis, DynamoDB, Memcached, Aerospike",
        "visual": "Cache layer between app and DB, session tokens, counters, TTL, feature flags.",
        "voiceover": (
            "First: key-value databases. "
            "These are built for very fast lookups by key. "
            "Typical examples are Redis, DynamoDB, Memcached, and Aerospike. "
            "They are ideal for caching, session storage, rate limiting, counters, and feature flags. "
            "The strength is speed and simplicity. "
            "The tradeoff is limited query flexibility."
        ),
        "asset_keywords": "redis cache, key value store, sessions, rate limiting, counters",
    },
    {
        "scene": 5,
        "title": "Document databases",
        "duration_sec": 50,
        "on_screen_text": "Document: MongoDB, Cosmos DB, Couchbase, Firestore",
        "visual": "JSON documents floating with nested objects like user profile, catalog item, order snapshot.",
        "voiceover": (
            "Next: document databases. "
            "These store flexible JSON-like records and work well when the schema changes often. "
            "Examples include MongoDB, Cosmos DB, Couchbase, Firestore, and DocumentDB. "
            "They are commonly used for user profiles, catalogs, content systems, and service-owned application data."
        ),
        "asset_keywords": "json document database, mongodb, document store, app backend",
    },
    {
        "scene": 6,
        "title": "Wide-column databases",
        "duration_sec": 55,
        "on_screen_text": "Wide-Column: Cassandra, Bigtable, HBase, ScyllaDB",
        "visual": "Large distributed cluster receiving huge write streams from events, telemetry, chat messages.",
        "voiceover": (
            "Wide-column databases are designed for huge scale and very high write throughput. "
            "Examples include Cassandra, Bigtable, HBase, ScyllaDB, and Amazon Keyspaces. "
            "These are used for event logs, telemetry, time-series style workloads, large messaging platforms, and globally distributed storage patterns."
        ),
        "asset_keywords": "cassandra cluster, telemetry, event stream, distributed database",
    },
    {
        "scene": 7,
        "title": "Graph databases",
        "duration_sec": 45,
        "on_screen_text": "Graph: Neo4j, Neptune, TigerGraph",
        "visual": "Nodes and edges for users, devices, cards, recommendations, fraud rings.",
        "voiceover": (
            "Graph databases shine when relationships are the core query pattern. "
            "Think recommendations, social graphs, fraud detection, knowledge graphs, and identity links. "
            "Popular options include Neo4j, Amazon Neptune, TigerGraph, JanusGraph, and ArangoDB."
        ),
        "asset_keywords": "graph database, recommendation engine, fraud detection graph",
    },
    {
        "scene": 8,
        "title": "Relational databases",
        "duration_sec": 55,
        "on_screen_text": "Relational: PostgreSQL, MySQL, Oracle, SQL Server, Aurora",
        "visual": "Transactions, ACID, tables with orders/payments/users, primary-replica diagram.",
        "voiceover": (
            "Relational databases still power many mission-critical systems. "
            "PostgreSQL, MySQL, Oracle, SQL Server, and Aurora are common choices for transactional workloads. "
            "Use them when consistency, joins, constraints, and ACID behavior matter, such as payments, orders, billing, and financial records."
        ),
        "asset_keywords": "sql database, postgres, mysql, transactions, payments",
    },
    {
        "scene": 9,
        "title": "Analytics warehouses and lakehouse tools",
        "duration_sec": 55,
        "on_screen_text": "Analytics: Snowflake, BigQuery, Redshift, ClickHouse, Databricks",
        "visual": "ETL pipeline from apps to warehouse with dashboards and ML models.",
        "voiceover": (
            "Analytics databases and lakehouse platforms are optimized for large aggregations and reporting. "
            "Examples include Snowflake, BigQuery, Redshift, ClickHouse, and Databricks. "
            "These power BI dashboards, product analytics, experimentation, observability analytics, and machine-learning data pipelines."
        ),
        "asset_keywords": "data warehouse, analytics, dashboards, bigquery, snowflake",
    },
    {
        "scene": 10,
        "title": "Search systems",
        "duration_sec": 40,
        "on_screen_text": "Search: Elasticsearch, OpenSearch, Solr, Typesense, Meilisearch",
        "visual": "Search bar querying indexed content with filters and autocomplete.",
        "voiceover": (
            "Search workloads are usually handled by dedicated search engines, not by the transactional database. "
            "Elasticsearch, OpenSearch, Solr, Typesense, and Meilisearch are used for full-text search, filtering, autocomplete, log search, and ranking."
        ),
        "asset_keywords": "search index, elasticsearch, full text search, autocomplete",
    },
    {
        "scene": 11,
        "title": "FAANG-style combined architecture",
        "duration_sec": 60,
        "on_screen_text": "How they fit together",
        "visual": "Users → CDN → API Gateway → Microservices → Cache → Primary DB → Search → Event stream → Analytics.",
        "voiceover": (
            "In a real large-scale architecture, these databases work together. "
            "A common pattern is: users hit the CDN and API gateway, microservices process requests, "
            "Redis handles cache, PostgreSQL or DynamoDB stores transactional data, Elasticsearch handles search, "
            "Kafka carries events, and Snowflake or BigQuery powers analytics. "
            "This layered approach is why large systems scale."
        ),
        "asset_keywords": "microservices architecture, redis postgres elasticsearch kafka snowflake",
    },
    {
        "scene": 12,
        "title": "Example stacks",
        "duration_sec": 55,
        "on_screen_text": "Example Production Stacks",
        "visual": "Three side-by-side example stacks: ecommerce, streaming, payments.",
        "voiceover": (
            "For e-commerce, you might use Redis for carts and cache, PostgreSQL for orders, "
            "Elasticsearch for product search, Kafka for events, and Snowflake for analytics. "
            "For streaming, Redis for session data, Cassandra for event storage, search for catalogs, and a warehouse for recommendation analytics. "
            "For payments, relational databases often remain the source of truth, with Redis, graph, and analytics systems around them."
        ),
        "asset_keywords": "ecommerce architecture, streaming architecture, payments architecture",
    },
    {
        "scene": 13,
        "title": "Pros and cons summary",
        "duration_sec": 45,
        "on_screen_text": "Pick by access pattern, not hype",
        "visual": "Matrix comparing speed, flexibility, relationships, analytics, consistency.",
        "voiceover": (
            "The right choice depends on access pattern. "
            "Use key-value for speed, document for flexibility, relational for consistency, wide-column for huge write scale, "
            "graph for relationships, and warehouses for analytics. "
            "The wrong choice is usually trying to force one database to do every job."
        ),
        "asset_keywords": "database decision matrix, pros cons, architecture comparison",
    },
    {
        "scene": 14,
        "title": "Outro",
        "duration_sec": 20,
        "on_screen_text": "Subscribe for more System Design",
        "visual": "Clean outro card with channel branding and next-video teaser.",
        "voiceover": (
            "If you want more content on system design, large-scale architecture, and FAANG interview prep, subscribe. "
            "In the next video, break down how a real microservices request flows through a global distributed system."
        ),
        "asset_keywords": "youtube outro, system design channel, subscribe",
    },
]


TOOLS_GUIDE = dedent("""
# Free-tool workflow for this YouTube video

## Recommended free online tools
1. **Canva Video Editor**
   - Use for slide-based visuals, captions, simple animations, and assembling the full video.
   - Create a 1920x1080 video project.
   - Copy each scene's on-screen text and voiceover into separate pages.

2. **CapCut Online**
   - Use if you want faster timeline editing, auto-captions, transitions, zoom effects, and easier B-roll handling.
   - Import your stock footage, voiceover, and scene text.

3. **Pexels**
   - Use for free stock videos/images relevant to tech, servers, networking, data centers, cloud animation, dashboards.

4. **Pixabay**
   - Use when Pexels does not have a suitable stock clip or icon-like footage.

## Suggested production workflow
### Option A — Canva-first workflow
1. Run this Python script.
2. Open `storyboard.csv`.
3. Create one Canva page per scene.
4. For each scene:
   - put the on-screen text as headline
   - paste or record the voiceover
   - add 1–3 stock visuals using `assets_to_download.csv`
   - animate text lightly
5. Add background music at very low volume.
6. Export as 1080p MP4.
7. Upload to YouTube Studio using `youtube_metadata.md`.

### Option B — CapCut-first workflow
1. Run this Python script.
2. Record voiceover using `narration_chunks.txt`.
3. Download clips listed in `assets_to_download.csv`.
4. Import voiceover + clips into CapCut Online.
5. Build the timeline scene by scene using `storyboard.csv`.
6. Add subtitles from the voiceover.
7. Export as 1080p or 4K MP4.
8. Upload to YouTube.

## Free production checklist
- [ ] Create 16:9 project
- [ ] Keep total runtime around 8–10 minutes
- [ ] Use large readable titles
- [ ] Keep 1 idea per scene
- [ ] Add subtle zoom/pan to static visuals
- [ ] Add subtitles
- [ ] Use royalty-free visuals only
- [ ] Check pronunciation of product names
- [ ] Export 1080p MP4
- [ ] Upload thumbnail + metadata

## Thumbnail plan
Big text options:
- FAANG Database Designs
- 25 Databases Explained
- System Design Databases
- Redis vs Mongo vs Cassandra

Visual idea:
- dark tech background
- 4–6 database logos
- arrows between app, cache, DB, analytics
""")


YOUTUBE_METADATA = dedent("""
# YouTube metadata

## Title options
1. FAANG Database Architecture Explained | Redis, MongoDB, Cassandra, Snowflake, PostgreSQL
2. 25 Databases Used in FAANG Architectures | System Design Explained
3. How Netflix, Amazon, and Google Choose Databases | FAANG Database Designs

## Description
In this video, we break down the database categories used in large-scale architectures:
- key-value stores
- document databases
- wide-column stores
- graph databases
- relational databases
- analytics warehouses
- search systems

You will also see how these fit into real microservices architectures used in internet-scale systems.

Topics covered:
- Redis
- DynamoDB
- MongoDB
- Cassandra
- PostgreSQL
- Snowflake
- BigQuery
- Elasticsearch
- Neo4j
- and more

## Suggested chapters
00:00 Hook
00:20 Why one database is not enough
00:45 Polyglot persistence
01:20 Key-value databases
02:10 Document databases
03:00 Wide-column databases
03:55 Graph databases
04:40 Relational databases
05:35 Analytics warehouses
06:30 Search systems
07:10 FAANG-style combined architecture
08:10 Example stacks
09:05 Pros and cons summary
09:45 Outro

## Tags
system design
database design
faang interview
redis
mongodb
cassandra
postgresql
snowflake
bigquery
elasticsearch
microservices
distributed systems
youtube tech education
database architecture

## Pinned comment
Which database category do you want next: graph, document, key-value, or analytics warehouse?
""")


THUMBNAIL_TEXT = dedent("""
FAANG Database Designs
25 Databases Explained

Alternative lines:
Redis vs Mongo vs Cassandra
How Big Tech Picks Databases
System Design Database Map
""")


VISUAL_PROMPTS = dedent("""
# Visual prompts for thumbnails/slides/B-roll search

## Thumbnail prompts
1. Dark blue technology background with global network lines, glowing database cylinders, cloud icons, modern YouTube tech thumbnail composition, bold empty space for title.
2. Futuristic distributed systems diagram with app, cache, database, search, analytics layers, cinematic lighting, high contrast, clean composition.
3. Global FAANG-style infrastructure visual with database icons, arrows, server racks, dashboards, neon tech look.

## B-roll / stock search prompts
- server racks in data center
- global network animation
- database icon animation
- cloud infrastructure dashboard
- coding on monitor
- backend architecture diagram
- microservices animation
- analytics dashboard
- search interface closeup
- digital graph network
- cybersecurity / datacenter

## Slide art prompts
- clean infographic comparing key-value, document, graph, wide-column, relational, analytics warehouse
- modern software architecture diagram with cache, DB, search, queue, warehouse
- ecommerce architecture with redis, postgres, elasticsearch, kafka, snowflake
- streaming platform architecture with cache, event storage, analytics
""")


FFMPEG_NOTES = dedent("""
# Optional local workflow with FFmpeg (not required)

If you want to assemble a simple video locally:
1. Create images/slides for each scene using Canva exports or screenshots.
2. Record voiceover scene by scene.
3. Put scene images into /assets/images
4. Put audio files into /assets/audio
5. Use FFmpeg to create one clip per scene and concat them.

This generator does not create FFmpeg commands automatically because your exported file names will vary.
But your folder structure is ready for it.

Suggested naming:
images/scene_01.png
audio/scene_01.mp3
...
""")


def write_markdown_script(path: Path) -> None:
    total_duration = sum(scene["duration_sec"] for scene in SCENES)
    mins = total_duration // 60
    secs = total_duration % 60

    lines = []
    lines.append("# FAANG Database Designs — YouTube Script\n")
    lines.append(f"Estimated runtime: {mins}:{secs:02d}\n")
    lines.append("## Full voiceover + scene guide\n")

    for s in SCENES:
        lines.append(f"### Scene {s['scene']}: {s['title']}")
        lines.append(f"- Duration: {s['duration_sec']} sec")
        lines.append(f"- On-screen text: {s['on_screen_text']}")
        lines.append(f"- Visual direction: {s['visual']}")
        lines.append(f"- Voiceover: {s['voiceover']}\n")

    path.write_text("\n".join(lines), encoding="utf-8")


def write_storyboard_csv(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "scene",
                "title",
                "duration_sec",
                "on_screen_text",
                "visual",
                "voiceover",
                "asset_keywords",
            ],
        )
        writer.writeheader()
        for scene in SCENES:
            writer.writerow(scene)


def write_assets_csv(path: Path) -> None:
    rows = []
    for scene in SCENES:
        rows.append(
            {
                "scene": scene["scene"],
                "title": scene["title"],
                "search_query_1": scene["asset_keywords"],
                "search_query_2": scene["title"].lower() + " infographic",
                "asset_type": "stock video / image / icon / slide art",
                "source_hint": "Pexels or Pixabay",
            }
        )

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "scene",
                "title",
                "search_query_1",
                "search_query_2",
                "asset_type",
                "source_hint",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_shot_list_json(path: Path) -> None:
    payload = {
        "project_title": "FAANG Database Designs",
        "aspect_ratio": "16:9",
        "estimated_runtime_sec": sum(scene["duration_sec"] for scene in SCENES),
        "scenes": SCENES,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_narration_chunks(path: Path) -> None:
    chunks = []
    for scene in SCENES:
        chunks.append(f"[Scene {scene['scene']} — {scene['title']}]")
        chunks.append(scene["voiceover"])
        chunks.append("")
    path.write_text("\n".join(chunks), encoding="utf-8")


def write_readme(path: Path) -> None:
    path.write_text(
        dedent("""
        # FAANG Database YouTube Package

        This folder was generated automatically.

        Files:
        - youtube_script.md
        - storyboard.csv
        - visual_prompts.md
        - capcut_canva_checklist.md
        - youtube_metadata.md
        - assets_to_download.csv
        - shot_list.json
        - thumbnail_text.txt
        - narration_chunks.txt
        - ffmpeg_notes.md

        Suggested fast workflow:
        1. Read youtube_script.md
        2. Record voiceover from narration_chunks.txt
        3. Download visuals listed in assets_to_download.csv
        4. Edit in Canva Video or CapCut Online
        5. Use youtube_metadata.md during upload
        """).strip() + "\n",
        encoding="utf-8",
        )


def main() -> None:
    PROJECT_DIR.mkdir(exist_ok=True)

    write_readme(PROJECT_DIR / "README.md")
    write_markdown_script(PROJECT_DIR / "youtube_script.md")
    write_storyboard_csv(PROJECT_DIR / "storyboard.csv")
    write_assets_csv(PROJECT_DIR / "assets_to_download.csv")
    write_shot_list_json(PROJECT_DIR / "shot_list.json")
    write_narration_chunks(PROJECT_DIR / "narration_chunks.txt")

    (PROJECT_DIR / "visual_prompts.md").write_text(VISUAL_PROMPTS, encoding="utf-8")
    (PROJECT_DIR / "capcut_canva_checklist.md").write_text(TOOLS_GUIDE, encoding="utf-8")
    (PROJECT_DIR / "youtube_metadata.md").write_text(YOUTUBE_METADATA, encoding="utf-8")
    (PROJECT_DIR / "thumbnail_text.txt").write_text(THUMBNAIL_TEXT, encoding="utf-8")
    (PROJECT_DIR / "ffmpeg_notes.md").write_text(FFMPEG_NOTES, encoding="utf-8")

    print("Created project folder:", PROJECT_DIR.resolve())
    print("Open README.md first.")

if __name__ == "__main__":
    main()
