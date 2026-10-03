# 🌊 DeepSight

### AI-Powered Automated Underwater Marine Debris & Anomaly Detection using Side-Scan Sonar Imagery

**Smart India Hackathon 2026 · SIH26057 · Ministry of Earth Sciences (MoES) · National Institute of Ocean Technology (NIOT)**

DeepSight is a production-oriented AI platform designed to assist marine researchers and survey teams in detecting, reviewing, and documenting underwater objects and anomalies from **Side-Scan Sonar (SSS)** imagery.

Instead of treating sonar imagery as a simple image-classification problem, DeepSight is designed as an end-to-end workflow:

```text
Real Side-Scan Sonar Imagery
          │
          ▼
   Ingestion & Validation
          │
          ▼
   AI Object Detection
          │
          ▼
 Acoustic / Visual Evidence
          │
          ▼
 Cross-Frame Persistence
          │
          ▼
 Geolocation when Metadata Exists
          │
          ▼
     Human Review
          │
          ▼
   Persisted Detection Record
          │
          ▼
      Research Report
```

> **Core principle:** DeepSight works with real source data and real model inference. It does not rely on fabricated detections, fake coordinates, hardcoded dashboard results, or synthetic production metrics.

---

## 🎯 Problem

Large underwater regions are difficult and expensive to inspect manually.

Side-Scan Sonar provides researchers with acoustic imagery of the seafloor, but reviewing large volumes of sonar data can become a time-consuming process.

Marine survey teams may need to identify objects such as:

* Marine debris
* Lost fishing equipment
* Crab pots
* Man-made seabed objects
* Other anomalous acoustic contacts

The challenge is not simply detecting a bright region in an image.

A useful system must connect:

**detection → evidence → persistence → metadata → review → reporting**

while preserving the provenance of the underlying data.

---

# 💡 DeepSight Solution

DeepSight combines machine learning, backend processing, evidence extraction, persistence analysis, geospatial metadata, and human review into a single workflow.

### 1. Real Sonar Data

The system accepts actual Side-Scan Sonar imagery rather than fabricated demo images or hardcoded detection arrays.

### 2. AI Detection

The ML pipeline uses YOLO-based object detection models trained for the project's sonar detection task.

### 3. Evidence Extraction

A detection is accompanied by evidence derived from the source imagery and detection context.

### 4. Cross-Frame Persistence

Where the available data and pipeline support it, detections can be evaluated across multiple frames rather than treating every frame as an isolated event.

### 5. Geolocation

Geographic information is attached only when valid source metadata is available.

If the required metadata is missing, DeepSight does **not** invent coordinates.

### 6. Human Review

AI detections are presented for human inspection and review.

The reviewer remains part of the decision-making loop.

### 7. Persistent Records

Processing jobs, detections, evidence, metadata, and review decisions are stored in the backend database.

### 8. Reporting

The system can transform persisted detection and review information into research-oriented reports.

---

# 🧠 Why Side-Scan Sonar Is Different

Side-Scan Sonar is not equivalent to ordinary RGB photography.

The resulting imagery represents acoustic responses from the seafloor and underwater objects.

Important visual characteristics can include:

* Acoustic highlights
* Acoustic shadows
* Seafloor texture
* Speckle and sonar noise
* Towfish geometry
* Object orientation
* Range-dependent appearance
* Background clutter

This makes underwater sonar detection a specialized computer-vision problem.

DeepSight therefore keeps the **ML detection stage connected to the rest of the acoustic-processing workflow** instead of treating a bounding box as the final answer.

---

# 🏗️ System Architecture

```text
                         ┌─────────────────────┐
                         │  Side-Scan Sonar    │
                         │      Imagery        │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Ingestion Pipeline  │
                         │ Validation / Jobs   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   ML Inference      │
                         │   YOLO Detector     │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
             ┌────────────┐ ┌────────────┐ ┌──────────────┐
             │ Detection  │ │ Acoustic   │ │ Frame /      │
             │ Results    │ │ Evidence   │ │ Persistence  │
             └─────┬──────┘ └─────┬──────┘ └──────┬───────┘
                   │              │               │
                   └──────────────┼───────────────┘
                                  ▼
                         ┌─────────────────────┐
                         │ Geospatial Metadata │
                         │ when available     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ PostgreSQL Database  │
                         │ Persistent Records  │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ DeepSight Dashboard │
                         │ Detection Review    │
                         │ Evidence / Reports  │
                         └─────────────────────┘
```

---

# 🔬 Detection Philosophy

DeepSight follows a simple principle:

> **A model prediction is evidence for investigation, not automatically ground truth.**

Therefore the application separates:

* Model prediction
* Confidence
* Detection evidence
* Source metadata
* Persistence information
* Human review decision

This separation is important for scientific traceability and future model improvement.

---

# 🤖 Machine Learning Pipeline

The current ML stack uses a YOLO-based object detector for Side-Scan Sonar imagery.

The repository contains model artifacts, inference code, evaluation tooling, and experiment outputs.

Current production-oriented model infrastructure includes:

```text
ml/
├── inference/
│   └── detector.py
├── evidence/
│   └── extractor.py
├── models/
│   └── model_registry.json
└── ...
```

Model artifacts are tracked through the project's model registry so that the inference pipeline can identify the intended model and verify the associated artifact.

---

# 📊 Model Evaluation

DeepSight intentionally separates **model confidence** from **model accuracy**.

A confidence score is the detector's belief in an individual prediction. It is not equivalent to precision, recall, or accuracy.

The currently tracked `ghostvision-crab-pot-custom` v5 model has recorded evaluation results in the project registry.

### Validation metrics

| Metric    | Recorded value |
| --------- | -------------: |
| Precision |         0.5860 |
| Recall    |         0.5035 |
| mAP@50    |         0.5010 |
| mAP@50–95 |         0.1702 |

### Test metrics

| Metric    | Recorded value |
| --------- | -------------: |
| Precision |         0.4478 |
| Recall    |         0.4074 |
| mAP@50    |         0.3739 |
| mAP@50–95 |         0.1487 |

These values describe a specific model version and evaluation split. They should **not** be interpreted as universal accuracy across all sonar environments.

DeepSight therefore avoids claiming a generalized "95–98% accuracy" without a corresponding reproducible evaluation.

---

# 🔎 Explainable Evidence

A major component of DeepSight is the evidence layer.

Instead of presenting only:

```text
Crab-Pot — 72%
```

the system is designed to expose additional information surrounding the detection.

Examples include:

* Detection bounding box
* Model confidence
* Source frame
* Evidence characteristics
* Persistence information
* Geospatial metadata when available
* Model/version provenance
* Human review state

This makes the detection easier for a researcher to inspect and audit.

---

# 👨‍🔬 Human-in-the-Loop Review

AI detection is not treated as the final decision.

The review workflow allows a human operator to inspect detections and record a decision.

```text
AI Detection
     │
     ▼
Evidence Presented
     │
     ▼
Human Inspection
     │
 ┌───┴────┐
 ▼        ▼
Confirm  Reject
 │        │
 └───┬────┘
     ▼
Persisted Review Record
```

This architecture also provides a foundation for future dataset improvement and model retraining using reviewed detections.

---

# 🗺️ Geolocation

DeepSight does not fabricate geographic coordinates.

When valid navigation or positional metadata exists, the pipeline can associate detection information with geographic information.

When metadata is unavailable:

```text
Coordinates = unavailable
```

rather than:

```text
Coordinates = guessed
```

This distinction is essential when working with scientific or survey data.

---

# 🗄️ Data Persistence

The backend uses PostgreSQL as the authoritative source for application state.

Important records include concepts such as:

* Processing jobs
* Ingestion state
* Detections
* Detection evidence
* Review decisions
* Model provenance
* Report information

The frontend does not manufacture detection results.

It consumes persisted backend data.

---

# 🖥️ Application Architecture

## Backend

DeepSight uses:

* Python
* FastAPI
* SQLAlchemy
* PostgreSQL
* Alembic
* Background processing workers

The FastAPI application exposes the backend API and connects the frontend, database, ingestion system, review workflow, and ML pipeline.

---

## Frontend

The frontend is built around a modern TypeScript/Vite application.

The dashboard is intended to provide:

* Sonar data ingestion
* Detection inspection
* Evidence visualization
* Review workflows
* Processing status
* Persisted detection information
* Report-oriented workflows

The UI is designed around actual backend records rather than mock dashboard statistics.

---

# ⚙️ Processing Architecture

DeepSight separates API responsibilities from longer-running processing tasks.

```text
Frontend
   │
   ▼
FastAPI
   │
   ├──────────────► PostgreSQL
   │
   └──────────────► Processing Job
                         │
                         ▼
                    ML Pipeline
                         │
                         ▼
                   Detection Data
                         │
                         ▼
                     PostgreSQL
                         │
                         ▼
                     Frontend
```

A worker process handles background ingestion and processing so that long-running ML operations do not need to execute directly inside the request/response lifecycle.

---

# 📁 Repository Structure

The repository is organized around the application's major responsibilities:

```text
DeepSight/
│
├── .github/
│   └── workflows/
│
├── data/
│   └── derived/
│
├── docs/
│
├── frontend/
│
├── ml/
│   ├── evidence/
│   ├── inference/
│   └── models/
│
├── runs/
│   └── error_analysis/
│
├── services/
│   ├── api/
│   └── worker/
│
├── storage/
│   └── runs/
│
├── tests/
│
├── requirements-backend.txt
├── README.md
└── ...
```

The exact contents may evolve as the project develops.

---

# 🧪 Testing & Quality

DeepSight includes automated backend testing and CI checks.

The development workflow emphasizes:

* Backend contract tests
* API validation
* Database integration testing
* Frontend TypeScript validation
* Production build verification
* Git diff validation
* ML evaluation scripts
* Error-analysis tooling

The project uses GitHub Actions for automated checks.

---

# 🔐 Engineering Principles

DeepSight follows several non-negotiable engineering principles.

### No fake detections

Detection results must originate from the actual inference pipeline.

### No fake coordinates

Geolocation must come from valid metadata or remain unavailable.

### No hardcoded dashboard results

The frontend must consume actual persisted backend data.

### No fabricated metrics

Model metrics must correspond to a defined evaluation procedure.

### Database is authoritative

The database is the source of truth for persisted application state.

### Provenance matters

Model and source-data provenance should be preserved wherever practical.

### Missing information stays missing

The system must not invent metadata merely to make a UI field look complete.

---

# 🚀 Local Development

> The exact setup commands may change as the application evolves. Always use the project's current dependency and environment configuration.

### Clone the repository

```powershell
git clone <repository-url>
cd DeepSight
```

### Create a Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Install backend dependencies

```powershell
pip install -r requirements-backend.txt
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Backend and database configuration should be supplied through environment variables appropriate for the local environment.

**Do not commit production secrets or `.env` files.**

---

# 🔌 API

The backend is implemented using FastAPI.

Core API areas include:

```text
/api/health
/api/ingestion
/api/reviews
/api/reports
```

The exact routes and request/response contracts are defined by the current backend implementation.

Interactive API documentation is available through FastAPI when the development server is running.

---

# 🧭 Development Workflow

DeepSight follows a feature-branch workflow.

```text
Create feature branch
        │
        ▼
Implement change
        │
        ▼
Run tests / build
        │
        ▼
git diff --check
        │
        ▼
Commit
        │
        ▼
Push branch
        │
        ▼
Pull Request
        │
        ▼
Review
        │
        ▼
Merge
```

The `main` branch should remain deployable and should not be rewritten with destructive Git operations.

---

# ☁️ Deployment

The project is being prepared for cloud deployment with GitHub-based CI/CD.

The intended production workflow is:

```text
Developer
   │
   ▼
Feature Branch
   │
   ▼
Pull Request
   │
   ▼
GitHub Actions
   │
   ├── Tests
   ├── Frontend Build
   ├── Backend Validation
   └── Deployment Checks
   │
   ▼
Production
```

The final cloud architecture will be selected according to:

* ML inference requirements
* CPU/GPU requirements
* Database requirements
* Storage requirements
* Expected workload
* Security
* Cost
* Reliability

Deployment documentation will be expanded as the production infrastructure is finalized.

---

# 📈 Roadmap

### Completed / In Progress

* [x] FastAPI backend foundation
* [x] PostgreSQL persistence
* [x] SQLAlchemy data layer
* [x] Alembic migrations
* [x] Background processing architecture
* [x] YOLO-based detection pipeline
* [x] Model registry
* [x] Evidence extraction infrastructure
* [x] Human review workflow
* [x] Detection review API
* [x] Frontend detection/review integration
* [x] Backend CI workflow
* [ ] Final production deployment
* [ ] Automated cloud deployment
* [ ] Production observability
* [ ] Extended model evaluation
* [ ] Larger domain-aware validation
* [ ] Model calibration improvements

---

# ⚠️ Current Limitations

DeepSight is an active research and engineering project.

Current limitations include:

* Detection performance varies across acquisition groups and sonar conditions.
* Model confidence should not be interpreted as calibrated probability without calibration analysis.
* Performance on unseen sonar environments requires additional validation.
* Geolocation depends on the availability and quality of source metadata.
* Detection quality is affected by object scale, background clutter, sonar conditions, and acquisition characteristics.
* Current model evaluation does not establish universal performance across all marine environments.
* GPU/CPU deployment requirements still need to be evaluated against the final production workload.

These limitations are documented intentionally rather than hidden.

---

# 🔬 Research & Future Work

Potential future improvements include:

### Model improvements

* Hard-negative mining
* Group-aware validation
* Better domain generalization
* Confidence calibration
* Additional sonar-specific preprocessing
* Improved small-object detection
* Expanded real-world datasets

### Detection intelligence

* Stronger cross-frame association
* Improved persistence scoring
* Multi-scale inference
* Temporal consistency analysis
* Better acoustic-shadow reasoning

### Geospatial intelligence

* More robust navigation metadata parsing
* Coordinate uncertainty modeling
* Survey-track visualization
* GIS-compatible exports

### Platform

* Production cloud deployment
* Scalable ML workers
* Object storage for large sonar datasets
* Automated CI/CD
* Monitoring and observability
* Role-based access control
* Audit trails

---

# 🌊 Why DeepSight?

DeepSight is not intended to be just another image-detection demo.

The goal is to build a complete engineering pipeline around a difficult real-world problem:

```text
Raw Acoustic Data
       ↓
Machine Learning
       ↓
Evidence
       ↓
Persistence
       ↓
Geospatial Context
       ↓
Human Validation
       ↓
Persistent Scientific Record
```

The system is designed around the principle that **AI should assist the researcher, not replace the researcher's ability to inspect and verify the evidence.**

---

# 🏆 Smart India Hackathon 2026

**Problem Statement:** SIH26057

**Title:** AI-Powered Automated Underwater Marine Debris and Anomaly Detection System using Side-Scan Sonar Imagery

**Organization:** Ministry of Earth Sciences (MoES)

**Institute / Department:** National Institute of Ocean Technology (NIOT)

**Theme:** Disaster Management

---

# 👥 Team

DeepSight is being developed as a collaborative Smart India Hackathon 2026 project.

The development responsibilities include:

* Frontend engineering
* Backend engineering
* ML / computer vision
* Data processing
* System architecture
* Database engineering
* DevOps and deployment
* UI/UX and integration

---

# 📜 Project Status

**Status:** Active Development

DeepSight is an evolving engineering and research prototype. Architecture, model versions, evaluation methodology, and deployment infrastructure may change as validation and development continue.

Performance claims in this README should always be interpreted together with the corresponding model version, dataset, evaluation split, and methodology.

---

## Built for real-world marine AI research.

**DeepSight — From Sonar Pixels to Explainable Detection.**
