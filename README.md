# Knight Insurance — AI-Powered Underwriting Pipeline

An intelligent commercial auto insurance underwriting system that automates the intake, classification, extraction, analysis, and rule evaluation of insurance submissions. Built as a case study for Knight Specialty Insurance Company.

## 🎯 What It Does

Agents and brokers submit insurance applications via **email** or **web upload** with multiple attachments (PDFs, Excel spreadsheets, images of driver licenses, loss runs, IFTA reports). The system:

1. **Receives** emails/uploads and stores all attachments in AWS S3
2. **Classifies** documents by content (never filenames) using Gemini AI
3. **Extracts** structured data — hybrid regex ($0 cost) + Vision (images only)
4. **Analyzes** the submission with 4 parallel AI risk assessment calls
5. **Detects** cross-document conflicts (counts, names, IDs, duplicates)
6. **Applies** 27 configurable underwriting rules across 6 categories
7. **Routes** to the appropriate team (Standard, Specialty, Driver, Ops, Senior UW)
8. **Presents** results in a real-time dashboard with underwriter review workflow

### Key Design Decisions

- **Content-based classification** — filenames are intentionally ignored per case study requirements
- **Hybrid extraction** — Python regex for structured docs ($0), AI vision only for CDL images
- **Parallel processing** — 4 concurrent AI calls via ThreadPoolExecutor (~45s vs ~3min)
- **Cross-document conflicts** — validates vehicle/driver counts, company names, FEIN/DOT, duplicate CDLs/VINs
- **Team routing** — auto-routes to 5 specialized teams based on triggered rules
- **Human-in-the-loop** — underwriters can Approve, Reject, or Override decisions with full audit trail
- **Cost-optimized** — ~$0.05–$0.09 per submission via Google Gemini 2.5 Flash

## 🏗️ Architecture

```
                         ┌─────────────────────────────────────────┐
                         │      Presentation Layer (Next.js 14)    │
                         │  Dashboard · Upload · Review · Compare  │
                         │  Analytics · Health · Architecture       │
                         └────────────────┬────────────────────────┘
                                          │ REST API
                         ┌────────────────▼────────────────────────┐
                         │    API & Orchestration (FastAPI 8000)    │
                         │  REST Router · Pipeline · Email Watcher  │
                         │  Review API (Approve/Reject/Override)    │
                         └────────────────┬────────────────────────┘
                                          │ Pipeline Invocation
              ┌───────────────┬───────────┼──────────┬──────────────┐
              ▼               ▼           ▼          ▼              ▼
        ┌───────────┐  ┌───────────┐ ┌─────────┐ ┌────────┐ ┌───────────┐
        │   Text    │  │ Classify  │ │ Extract │ │   AI   │ │   Rules   │
        │ Extractor │  │ (Gemini)  │ │ (Regex  │ │Analyzer│ │  Engine   │
        │ PyMuPDF   │  │ Content   │ │+Vision) │ │4 calls │ │ 27 rules  │
        └───────────┘  └───────────┘ └─────────┘ └────────┘ └───────────┘
              │               │           │          │              │
              ▼               ▼           ▼          ▼              ▼
        ┌──────────────────────────────────────────────────────────────┐
        │  Decision + Team Routing → Accept / Refer / Decline          │
        │  → Standard · Specialty Risk · Driver · Ops · Senior UW     │
        └──────────────────────────────────────────────────────────────┘
              │                                              │
     ┌────────▼──────────┐                       ┌──────────▼──────────┐
     │ SQLite + S3       │                       │ Gemini 2.5 Flash    │
     │ SQLAlchemy ORM    │                       │ ~$0.05-0.09/sub     │
     │ 6 tables          │                       │ IMAP Mail Server    │
     └───────────────────┘                       └─────────────────────┘
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy, Uvicorn |
| **AI Engine** | Google Gemini 2.5 Flash (Vision + Text) |
| **Frontend** | Next.js 14, TypeScript, React |
| **Database** | SQLite (Postgres-ready — one connection string change) |
| **Storage** | AWS S3 (AES-256 encryption, versioned) |
| **Deployment** | Docker, Docker Compose, AWS EC2 (t2.micro) |
| **Email** | IMAP integration (polls every 30s) |

## ⚖️ Business Rules — 27 Rules, 6 Categories

### 🏢 Eligibility (4 rules)
| Rule | Description |
|------|------------|
| ELIG-001 | Years in business ≥ 2 |
| ELIG-002 | Covered vehicle types only (semi-trucks) |
| ELIG-003 | Non-covered states exclusion |
| ELIG-004 | Operating radius within limits |

### 👤 Driver (7 rules)
| Rule | Description |
|------|------------|
| DRV-001 | Valid CDL required for all drivers |
| DRV-002 | Driver age between 23–70 |
| DRV-003 | Minimum 2 years driving experience |
| DRV-004 | Maximum 3 violations in 3 years |
| DRV-005 | No major violations (DUI/reckless driving) |
| DRV-006 | Maximum 2 at-fault accidents |
| DRV-007 | MVR check required |

### ⚠️ Exposure (4 rules)
| Rule | Description |
|------|------------|
| EXP-001 | Hazardous materials prohibited |
| EXP-002 | Prohibited commodities check |
| EXP-003 | Maximum power units ≤ 26 |
| EXP-004 | Mexico border operations (50 miles) |

### 📋 Submission (4 rules)
| Rule | Description |
|------|------------|
| SEL-001 | FEIN and DOT number required |
| SEL-002 | Tow trucks excluded |
| SEL-003 | Minimum premium per power unit ($13,000) |
| SEL-004 | Sole proprietor check |

### ⛽ IFTA (4 rules)
| Rule | Description |
|------|------------|
| IFTA-001 | IFTA filings required |
| IFTA-002 | Minimum annual mileage threshold |
| IFTA-003 | Multi-state operation eligibility |
| IFTA-004 | Border state check |

### 🔀 Cross-Document Conflict Detection (6 rules)
| Rule | Description |
|------|------------|
| CON-001 | Vehicle count mismatch across documents |
| CON-002 | Driver count mismatch across documents |
| CON-003 | Company name inconsistency |
| CON-004 | FEIN/DOT number conflict |
| CON-005 | Duplicate CDL numbers detected |
| CON-006 | Duplicate VINs detected |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (for deployment)

### Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
cp .env.example .env
```

Required variables: `GEMINI_API_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME`, `IMAP_SERVER`, `EMAIL_ADDRESS`, `EMAIL_PASSWORD`

### Local Development

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000 --host 0.0.0.0
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Docker Deployment

```bash
docker-compose up -d
```

Access: Frontend at `:3000`, API at `:8000`, Swagger at `:8000/docs`

## 📁 Project Structure

```
knight-insurance/
├── backend/
│   ├── main.py                    # FastAPI app + email watcher
│   ├── config.py                  # Configuration & env vars
│   ├── models/
│   │   ├── database.py            # SQLAlchemy models (6 tables)
│   │   └── schemas.py             # Pydantic schemas
│   ├── routers/
│   │   └── submissions.py         # API endpoints + review workflow
│   ├── services/
│   │   ├── pipeline.py            # 6-step processing pipeline
│   │   ├── document_processor.py  # Text/Vision extraction
│   │   ├── document_classifier.py # AI content-based classification
│   │   ├── data_extractor.py      # Hybrid regex + Vision extraction
│   │   ├── ai_analyzer.py         # 4 parallel AI risk analysis calls
│   │   ├── email_intake.py        # Email attachment processing
│   │   └── email_watcher.py       # IMAP polling daemon (30s)
│   ├── rules/
│   │   ├── engine.py              # Rules orchestrator + conflict detection
│   │   ├── base.py                # Base types & constants
│   │   ├── eligibility.py         # ELIG-001 to ELIG-004
│   │   ├── driver.py              # DRV-001 to DRV-007
│   │   ├── exposure.py            # EXP-001 to EXP-004
│   │   ├── submission.py          # SEL-001 to SEL-004
│   │   ├── ifta.py                # IFTA-001 to IFTA-004
│   │   └── conflicts.py           # CON-001 to CON-006
│   └── utils/
│       ├── gemini.py              # Google Gemini AI client
│       └── s3_storage.py          # AWS S3 integration
├── frontend/
│   └── src/
│       ├── app/                   # Next.js pages (dashboard, submissions, analytics, health, compare)
│       ├── components/            # React components (layout, submission tabs, charts)
│       ├── lib/api.ts             # API client
│       └── types/index.ts         # TypeScript types
├── sample-data/                   # Test submission generators
├── docs/
│   └── architecture.html          # Interactive architecture diagram (7 views)
├── docker-compose.yml
└── deploy_aws.sh
```

## 🔄 Processing Pipeline

| Step | Name | Method | Time |
|------|------|--------|------|
| 1 | Text Extraction | PyMuPDF (PDF), openpyxl (Excel), Gemini Vision (images) | ~5s |
| 2 | Classification | Single batched Gemini call — content-based only | ~3s |
| 3 | Data Extraction | Python regex ($0) + Gemini Vision (CDL images) | ~10s |
| 4 | AI Risk Analysis | 4 parallel Gemini calls (company, driver, fleet, financial) | ~20s |
| 5 | Rules Engine | 27 rule evaluations + 6 conflict detections | <1s |
| 6 | Decision + Routing | Accept/Refer/Decline → team assignment | <1s |
| **Total** | | | **~45s** |

## 💰 Cost Analysis

| Resource | Cost |
|----------|------|
| AI per submission | ~$0.05–$0.09 |
| EC2 (t2.micro) | Free tier / ~$8.50/mo |
| S3 storage | ~$0.02/mo |
| **Total monthly (100 submissions)** | **~$14–17/mo** |

## 🔒 Security & Governance

- **Audit trail** — every pipeline step logged with timestamps
- **Data encryption** — S3 AES-256 at rest, IMAP TLS / HTTPS in transit
- **Human-in-the-loop** — no auto-approval; underwriter must Approve/Reject/Override
- **AI transparency** — input/output tokens, cost, and call count tracked per submission
- **Credentials** — environment variables, never committed to git
- **Scalability** — SQLite → PostgreSQL (one line), EC2 → ECS/Fargate, SQS for async

## 📄 License

Built for Knight Specialty Insurance Company case study evaluation.
