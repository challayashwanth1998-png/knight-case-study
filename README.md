# Knight Insurance — AI-Powered Underwriting Pipeline

An intelligent commercial auto insurance underwriting system that automates the intake, classification, extraction, analysis, and rule evaluation of insurance submissions. Built as a case study for Knight Specialty Insurance Company.

## 🎯 What It Does

Agents and brokers submit insurance applications via **email** with multiple attachments (PDFs, Excel spreadsheets, images of driver licenses, loss runs, IFTA reports). The system:

1. **Receives** emails and stores all attachments
2. **Classifies** documents by content (not filename) using AI
3. **Extracts** structured data from every document type
4. **Analyzes** the submission with AI-powered risk assessment
5. **Applies** 19+ underwriting rules from Knight Guidelines
6. **Presents** results in a real-time dashboard for underwriters

### Key Design Decisions

- **Content-based classification** — filenames are intentionally ignored per case study requirements
- **Hybrid extraction** — Python regex for structured docs (Excel, PDF), AI vision for images (CDL photos)
- **Parallel processing** — vision OCR, classification, and analysis run concurrently
- **Cost-optimized** — ~$0.002 per submission via Google Gemini API
- **Sub-60s processing** — full 13-document submission processed in ~53 seconds

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Email/IMAP  │────▶│   FastAPI     │────▶│   SQLite     │
│  Intake      │     │   Backend     │     │   Database   │
└──────────────┘     └──────┬───────┘     └──────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Document  │ │   AI     │ │  Rules   │
        │ Processor │ │ Analyzer │ │  Engine  │
        │ (Gemini)  │ │ (Gemini) │ │ (Python) │
        └──────────┘ └──────────┘ └──────────┘
              │            │            │
              ▼            ▼            ▼
        ┌──────────────────────────────────┐
        │     Next.js Dashboard (UI)       │
        └──────────────────────────────────┘
```

### Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python, FastAPI, SQLAlchemy |
| **AI Engine** | Google Gemini 2.0 Flash (Vision + Text) |
| **Frontend** | Next.js 15, TypeScript, React |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **Storage** | AWS S3 + local filesystem |
| **Deployment** | Docker, Docker Compose, AWS EC2 |
| **Email** | IMAP integration (Namecheap Private Email) |

## 📋 Underwriting Rules (from Knight Guidelines)

### Eligibility Rules
- **ELIG-001**: Target risk — semi-trucks only
- **ELIG-002**: Ineligible vehicle types (dump trucks, tow trucks, cranes, etc.)
- **ELIG-006**: Auto liability deductibles not allowed
- **ELIG-007**: Physical damage not available

### Driver Rules
- **DRV-001**: Valid CDL required
- **DRV-002**: Minimum 2 years CDL experience
- **DRV-003**: Minimum age 23
- **DRV-004**: Age 65+ requires DOT medical exam
- **DRV-005**: Max 6 points in 3 years
- **DRV-006**: Max 4 points in 12 months
- **DRV-100**: Unacceptable driver history check (DUI, reckless driving, etc.)

### Exposure Rules
- **EXP-001**: Hazardous materials prohibited

### Submission Completeness
- **SUB-001**: FEIN/SSN present
- **SUB-002**: MC/DOT number present
- **SUB-003**: Loss runs current (within 60 days)
- **SUB-005**: Most recent 4 IFTA quarters

### IFTA Analysis
- **IFTA-001**: Fleet MPG reasonableness per quarter

### Selective Exposures
- **SEL-003**: Premium per unit threshold

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

## 📁 Project Structure

```
knight-insurance/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration & env vars
│   ├── models/
│   │   ├── database.py         # SQLAlchemy models
│   │   └── schemas.py          # Pydantic schemas
│   ├── routers/
│   │   └── submissions.py      # API endpoints
│   ├── services/
│   │   ├── pipeline.py         # 6-step processing pipeline
│   │   ├── document_processor.py  # Text/Vision extraction
│   │   ├── document_classifier.py # AI batch classification
│   │   ├── data_extractor.py   # Structured data extraction
│   │   ├── ai_analyzer.py      # AI analysis (parallel)
│   │   ├── email_intake.py     # Email processing
│   │   └── email_watcher.py    # IMAP polling
│   ├── rules/
│   │   ├── engine.py           # Rules orchestrator
│   │   ├── base.py             # Base types & constants
│   │   ├── eligibility.py      # Eligibility rules
│   │   ├── driver.py           # Driver qualification rules
│   │   ├── exposure.py         # Prohibited exposure rules
│   │   ├── submission.py       # Submission completeness
│   │   ├── ifta.py             # IFTA analysis rules
│   │   └── selective.py        # Selective exposure rules
│   └── utils/
│       ├── gemini.py           # Google Gemini AI client
│       ├── s3_storage.py       # AWS S3 integration
│       └── validators.py       # Data validation
├── frontend/
│   └── src/
│       ├── app/                # Next.js pages
│       ├── components/         # React components
│       ├── lib/api.ts          # API client
│       └── types/index.ts      # TypeScript types
├── sample-data/                # Test submissions
├── docs/
│   └── architecture.html       # Interactive architecture diagram
├── docker-compose.yml
└── deploy_aws.sh
```

## 🔄 Processing Pipeline

| Step | Name | Method | Time |
|------|------|--------|------|
| 1 | Text Extraction | Parallel Gemini Vision (images) + Python (PDF/Excel) | ~11s |
| 2 | Document Classification | Single batch AI call (content-based) | ~11s |
| 3 | Data Extraction | Python regex (Excel/PDF/DL) + AI (application) | ~15s |
| 4 | AI Analysis | 4 parallel calls (summary, conflicts, risk, recs) | ~16s |
| 5 | Rules Engine | 19 Python-based rule evaluations | <1s |
| 6 | Decision | Automated accept/refer/decline | <1s |
| **Total** | | | **~53s** |

## 💰 Cost Analysis

| Resource | Cost |
|----------|------|
| AI per submission | ~$0.002 |
| EC2 (t2.micro) | ~$8.50/mo |
| S3 storage | ~$0.02/mo |
| **Total monthly (100 submissions)** | **~$8.72/mo** |

## 🔒 Security

- API keys stored in environment variables (never in code)
- S3 storage with server-side encryption
- Audit logging for all pipeline operations
- CORS configuration for frontend origin only

## 📄 License

Built for Knight Specialty Insurance Company case study evaluation.
