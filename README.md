<div align="right"><img src="./Assets/logo.svg" width="300" height="300" alt="NETRA Logo" /></div>

# NETRA
**Network Evaluation, Trend & Relationship Analytics**

>Secure, open-source, multi-layered intelligence and relationship analytics platform for intelligence agencies, shifting tactical defense from reactive monitoring to audited, proactive operations

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev)
[![Neo4j](https://img.shields.io/badge/Neo4j-GDS-008CC1.svg)](https://neo4j.com)

---

## What it does

NETRA unifies fragmented tactical data pipelines into a single audited point of truth across five dedicated layers:

| Layer | Responsibility |
|-------|----------------|
| **1 · Ingestion** | OCR → Translation → NLP → Entity Resolution via Kafka + Celery |
| **2 · Storage** | Hybrid PostgreSQL/PostGIS + Neo4j + Elasticsearch with RLS + AES-256 |
| **3 · Analytics** | GDS in-memory graph projections, HDBSCAN spatial clustering, MAD anomaly detection |
| **4 · API Gateway** | Zero-trust RBAC, jurisdictional enforcement, immutable audit trail |
| **5 · Frontend** | Four-board React SPA — map, case workspace, link explorer, vehicle registry |

---

## System Architecture

```mermaid
graph TD
    subgraph L1["① Ingestion & NLP"]
        A[Raw Files\nPDFs · TIFFs · CDRs] --> B[Debezium CDC]
        B -->|JSON stream| K[(Apache Kafka)]
        K --> W[Celery Workers]
        W --> O[OCR Engine\nTesseract · PaddleOCR]
        O --> T[IndicTrans2\nBilingual Translation]
        T --> N[spaCy + IndicBERT\nNER Pipeline]
        N --> ER{Entity Resolution\nDouble Metaphone\nJaro-Winkler}
        ER -->|score ≥ 0.85| AM[Auto Merge]
        ER -->|0.60 – 0.85| MQ[/Analyst Queue/]
        ER -->|score < 0.60| NG[New KSP-GUID]
    end

    subgraph L2["② Hybrid Storage"]
        PG[(PostgreSQL\n+ PostGIS\nTabular · GIS · RLS)]
        NJ[(Neo4j\nOPL Graph\nOLTP)]
        ES[(Elasticsearch\nFuzzy · Phonetic)]
    end

    subgraph L3["③ Analytics & ML"]
        GDS[GDS In-Memory\nProjection\nBetweenness · Louvain]
        HDB[HDBSCAN\nHaversine Clustering]
        MAD[Modified Z-Score\nMAD Anomaly Engine]
    end

    subgraph L4["④ API Gateway"]
        FA[FastAPI\nasyncio.gather]
        JG[JurisdictionalGuard\nRBAC · JWT · LDAP]
        AL[(Audit Logger\nWrite-Only Table)]
    end

    subgraph L5["⑤ Frontend — React + Zustand"]
        GB[General Board\nMapLibre GL]
        CB[Case Board\nBreak-Glass Modal]
        PB[Profile Board\nCytoscape.js]
        VB[Vehicle Board\nVAHAN API]
    end

    AM & NG --> PG & NJ
    MQ -.->|post-review| PG & NJ
    PG & NJ --> ES
    NJ --> GDS
    PG --> HDB & MAD
    GDS & HDB & MAD -->|write-back properties| PG & NJ
    PG & NJ & ES --> FA
    FA --> JG --> AL
    FA --> GB & CB & PB & VB
```

---

## Data Ingestion & Resolution Flow

```mermaid
flowchart LR
    SRC([State DB Replica\nPhysical Records]) -->|transaction log| CDC[Debezium CDC]
    CDC -->|netra-raw-records| KF[(Kafka Topic)]
    KF --> CW[Celery Workers\nasync queue]

    CW --> OCR[OCR\nTesseract · PaddleOCR\nEN + Kannada]
    OCR --> IT2[IndicTrans2\nRegional → English]
    IT2 --> SP[spaCy Pipeline\nIndicBERT transformer]

    SP --> E1([PERSON])
    SP --> E2([VEHICLE_NO])
    SP --> E3([CONTACT])
    SP --> E4([MO])
    SP --> E5([SECTION_OF_LAW])

    E1 & E2 & E3 & E4 & E5 --> ER{Entity Resolution}

    ER -->|Exact ID match\nAadhaar · Phone| DET[Deterministic\nAuto Link]
    ER -->|score ≥ 0.85| AUTO[Auto Merge]
    ER -->|0.60 – 0.85| MANUAL[/Manual Verification\nQueue/]
    ER -->|score < 0.60| NEW[Generate\nKSP-GUID]

    DET & AUTO & NEW --> PG2[(PostgreSQL)]
    DET & AUTO & NEW --> NJ2[(Neo4j)]
    PG2 & NJ2 -->|sync| ES2[(Elasticsearch)]
```

---

## API Request & Access Control Flow

```mermaid
sequenceDiagram
    participant C  as Client (React)
    participant JG as JurisdictionalGuard
    participant AL as Audit Logger
    participant DB as PG · Neo4j · ES

    C->>JG: Request + JWT
    JG-->>JG: Verify role & station scope

    alt In-jurisdiction
        JG->>AL: Log event (immutable)
        JG->>DB: asyncio.gather(pg_query, neo4j_query, es_query)
        DB-->>C: Unified JSON payload < 100 ms
    else Cross-jurisdiction — Break-Glass
        C->>JG: + X-Emergency-Override-Reason\n+ X-Active-Investigation-FIR
        JG->>AL: Log override + FIR ref (immutable)
        JG->>DB: Temporary read grant (user_id · case_id · TTL)
        DB-->>C: Full payload — PII visible, audit stamped
    else Federated search (outside jurisdiction)
        JG->>DB: Execute with RLS mask
        DB-->>C: Redacted result + Request Access link
    end
```

---

## Analytical Engines

### Neo4j GDS — In-Memory Projection

```mermaid
flowchart LR
    OLTP[(Live Neo4j\nOLTP Graph)] -->|gds.graph.project| MEM[/netra-analytical-graph\nIn-Memory OLAP/]
    MEM --> BC[Betweenness Centrality\nIdentify hawala nodes\n& fences]
    MEM --> LC[Louvain Community Detection\nCluster criminal networks\nmodularity-based]
    BC & LC -->|write-back| OLTP
    MEM -->|drop projection| RAM([RAM Released])
```

### HDBSCAN Spatial Clustering & MAD Anomaly Detection

```mermaid
flowchart LR
    INC([Incident\nCoordinates]) -->|lat/lon → radians| HAV[Haversine\nDistance Matrix]
    HAV --> HDB[HDBSCAN\nHierarchical Density]
    HDB --> OUT1([cluster_id\ncluster_probability])
    HDB --> OUT2([noise = isolated\nincident])

    CNT([Incident\nCounts]) --> MAD_E[MAD Engine\nMi = 0.6745 × xi − x̃ ÷ MAD]
    MAD_E -->|Mi > 3.5| ALERT([High-Priority Alert\nStation boundary flashes])
    MAD_E -->|MAD = 0| FB[Fallback:\nScaled Mean Abs Dev]
```

---

## Storage & Security Model

| Store | Role | Security |
|-------|------|----------|
| **PostgreSQL + PostGIS** | Transactional record · GIS boundaries · R-Tree index | Row-Level Security · AES-256 PII · Write-only audit table |
| **Neo4j / Apache AGE** | OPL graph — `INVOLVED_IN`, `ASSOCIATED_WITH`, `USED_VEHICLE`, `PRESENT_AT` | Cluster auth · role scoping |
| **Elasticsearch** | Fuzzy + phonetic full-text · < 50 ms state-wide queries | Index-level ACL · TLS in-transit |

---

## Interface
| Board | Purpose | Key Features |
| :--- | :--- | :--- |
| **General Board** | Regional heatmap · Z-score alert overlays | • HDBSCAN density-based incident clustering visualization<br>• Real-time MAD anomaly flashing on station boundaries<br>• Survey of India-compliant boundary correction layers<br>• Live spatial filtering by incident type and time range |
| **Case Board** | FIR workspace · entity highlights · Break-Glass modal | • Interactive NLP entity tagging (person, vehicle, contact, MO)<br>• Integrated regional-to-English translation viewer<br>• "Break-Glass" cross-jurisdiction temporary PII decryption modal<br>• Manual entity resolution queue for review and matching |
| **Profile Board** | Suspect link graph · cross-jurisdiction timeline | • Cytoscape.js canvas with force-directed and radial layouts<br>• GDS Centrality node-sizing and Louvain community coloring<br>• Interactive timeline merging multi-jurisdictional incident logs<br>• Direct dynamic expansion of first- and second-degree associates |
| **Vehicle Board** | VAHAN registry · challan log · state-wide flag history | • Direct VAHAN API real-time registration retrieval<br>• State-wide alerts for blacklisted/wanted vehicle plate matches<br>• Aggregated history of traffic challans and violations<br>• Geographic mapping of vehicle sighting logs |

---

## Project Structure
```
netra/
│
├── backend/
│   ├── alembic/                    # DB Migrations (PostgreSQL)
│   ├── app/                        # Renamed from NETRA_ingestion for broader scope
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic BaseSettings
│   │   ├── database.py             # DB Session initializers (PG, Neo4j, ES)
│   │   ├── models.py               # SQL Alchemy / Neo4j OGM models
│   │   ├── schemas_api.py          # Pydantic validation schemas
│   │   ├── parsers.py              # OCR & Regional translator pipelines
│   │   ├── nlp_engine.py           # spaCy/IndicBERT NER
│   │   ├── external_api.py         # VAHAN API integrations
│   │   ├── spatial_engine.py       # HDBSCAN and MAD engines
│   │   ├── mo_matcher.py           # Modus Operandi analytics
│   │   ├── graph_analytics.py      # Neo4j GDS projections
│   │   ├── auth.py                 # RBAC and JurisdictionalGuard
│   │   ├── orchestrator.py         # Celery/Kafka worker pipelines
│   │   └── middleware.py           # Audit logging interceptor
│   │
│   ├── routes/                     # Split routes if they grow large
│   │   ├── __init__.py
│   │   └── api.py                  # API endpoints
│   │
│   ├── .env.example                # Template for database credentials/keys
│   ├── main.py                     # FastAPI entry point
│   └── requirements.txt
│
└── frontend/
    ├── package.json
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── assets/                 # SVGs and background graphics
        ├── components/
        │   ├── GeneralBoardMap.jsx
        │   ├── LinkExplorer.jsx
        │   └── BreakGlassModal.jsx
        ├── views/
        │   ├── CaseBoard.jsx
        │   ├── ProfileBoard.jsx
        │   └── VehicleBoard.jsx
        ├── main.jsx
        ├── store.js                # Zustand state
        ├── api.js                  # Axios client configuration
        └── App.jsx
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Profile Board API response | **< 100 ms** |
| Elasticsearch fuzzy search | **< 50 ms** |
| Kafka ingestion throughput | **10,000 events / min** |

---

## Deployment

- **Transport:** TLS 1.3 enforced on all connections; API behind HAProxy / NGINX in private subnet
- **PostgreSQL:** Master (writes) + read-replicas (reads) multi-node cluster
- **Neo4j:** Multi-instance autonomous cluster for heavy graph workloads
- **Elasticsearch:** 3-node cluster with dedicated master and data roles

---

## License

MIT — see [LICENSE](LICENSE).
NETRA is designed for official law enforcement and defense use. All deployments must comply with applicable data protection, privacy, and national security regulations.
