# DeepSight

### AI-Powered Underwater Marine Debris & Anomaly Detection using Side-Scan Sonar Imagery

**Smart India Hackathon 2026 — SIH26057**
**Organization:** Ministry of Earth Sciences (MoES) / National Institute of Ocean Technology (NIOT)

DeepSight is an engineering-focused marine-vision platform designed to process **Side-Scan Sonar (SSS) imagery**, run AI-assisted object detection, extract explainable acoustic evidence, track detections across frames, associate detections with available geospatial metadata, and provide a **human-in-the-loop review workflow** for marine researchers.

The system is designed around one core principle:

> **A detection should be traceable from its original sonar source to the final reviewed result.**

---

## Table of Contents

* [Overview](#overview)
* [Problem](#problem)
* [Solution](#solution)
* [Core Capabilities](#core-capabilities)
* [System Architecture](#system-architecture)
* [End-to-End Processing Pipeline](#end-to-end-processing-pipeline)
* [AI/ML Pipeline](#aiml-pipeline)
* [Explainable Acoustic Evidence](#explainable-acoustic-evidence)
* [Cross-Frame Persistence](#cross-frame-persistence)
* [Geolocation](#geolocation)
* [Human Review](#human-review)
* [Reports and Provenance](#reports-and-provenance)
* [Technology Stack](#technology-stack)
* [Repository Structure](#repository-structure)
* [Local Development](#local-development)
* [Environment Configuration](#environment-configuration)
* [Database Setup](#database-setup)
* [Running the Backend](#running-the-backend)
* [Running the Worker](#running-the-worker)
* [Running the Frontend](#running-the-frontend)
* [Running with Docker](#running-with-docker)
* [API Surface](#api-surface)
* [Testing and Quality Checks](#testing-and-quality-checks)
* [Model and Evaluation](#model-and-evaluation)
* [Current Limitations](#current-limitations)
* [Roadmap](#roadmap)
* [Engineering Principles](#engineering-principles)
* [Smart India Hackathon Context](#smart-india-hackathon-context)
* [Project Status](#project-status)

---

# Overview

Side-Scan Sonar produces acoustic imagery rather than conventional optical photographs. Objects and seabed structures are represented through patterns of acoustic return, shadow, intensity, texture, and geometry.

This creates a different computer-vision problem from ordinary RGB image detection.

DeepSight combines:

```text
Side-Scan Sonar Imagery
        │
        ▼
   Data Ingestion
        │
        ▼
 Image / Metadata Validation
        │
        ▼
   AI Object Detection
        │
        ▼
 Acoustic Evidence Extraction
        │
        ▼
 Cross-Frame Persistence
        │
        ▼
 Geospatial Association
        │
        ▼
 Human Review
        │
        ▼
 Research / Detection Report
```

The platform is intended to make the complete processing chain observable and reproducible rather than treating the model prediction as the final answer.

---

# Problem

Marine debris and underwater anomalies are difficult to inspect at scale.

Traditional sonar analysis can involve:

* large volumes of imagery
* manual inspection
* visually ambiguous acoustic signatures
* repeated detections across adjacent frames
* uncertain object boundaries
* incomplete geospatial metadata
* differences between sonar acquisition conditions
* difficulty explaining why an AI system produced a particular detection

A useful system therefore needs more than an object detector.

It needs a workflow that connects:

**source data → detection → evidence → persistence → location → review → report**

---

# Solution

DeepSight provides an integrated workflow for marine sonar analysis.

### 1. Real sonar ingestion

The system accepts actual source imagery rather than relying on hardcoded demonstration detections.

### 2. AI-assisted detection

The backend loads a registered detection model and performs inference against the ingested imagery.

### 3. Evidence extraction

Detection results can be accompanied by measurable evidence derived from the underlying sonar image.

### 4. Cross-frame reasoning

Repeated detections can be examined across frames instead of treating every frame prediction as an isolated event.

### 5. Geospatial association

When valid positioning metadata is available, detections can be associated with geographic information.

### 6. Human review

AI-generated detections are presented for review rather than automatically treated as ground truth.

### 7. Reporting

Reviewed information can be used to generate structured research-oriented reports.

---

# Core Capabilities

| Capability              | Description                                           |
| ----------------------- | ----------------------------------------------------- |
| Sonar ingestion         | Ingest real Side-Scan Sonar imagery                   |
| AI detection            | YOLO-based object detection                           |
| Model registry          | Versioned model and artifact metadata                 |
| Artifact verification   | Optional model SHA-256 verification                   |
| Acoustic evidence       | Extract measurable image-level evidence               |
| Cross-frame persistence | Associate repeated observations                       |
| Geolocation             | Preserve and expose available positioning information |
| Human review            | Review and classify AI-generated detections           |
| Provenance              | Preserve source/model/evidence information            |
| Reports                 | Generate structured detection/review outputs          |
| Persistent storage      | PostgreSQL-backed application state                   |
| Background processing   | Dedicated ingestion worker                            |
| API                     | FastAPI backend                                       |
| Web application         | React + TypeScript frontend                           |

---

# System Architecture

```text
                         ┌─────────────────────────┐
                         │       Web Client        │
                         │ React + TypeScript/Vite │
                         └────────────┬────────────┘
                                      │
                                      │ HTTP
                                      ▼
                         ┌─────────────────────────┐
                         │      FastAPI API        │
                         │                         │
                         │ • Ingestion              │
                         │ • Review                 │
                         │ • Reports                │
                         │ • Health                 │
                         └───────┬─────────┬───────┘
                                 │         │
                                 │         │
                         ┌───────▼───┐ ┌──▼──────────┐
                         │ PostgreSQL│ │   Redis     │
                         │ + PostGIS │ │ coordination│
                         └───────┬───┘ └─────────────┘
                                 │
                                 │ queued jobs
                                 ▼
                         ┌─────────────────────────┐
                         │    Background Worker    │
                         │                         │
                         │ • Job recovery          │
                         │ • Job claiming          │
                         │ • Ingestion pipeline    │
                         │ • AI inference          │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │       ML Pipeline       │
                         │                         │
                         │ Model Registry          │
                         │ YOLO Detector           │
                         │ Evidence Extraction    │
                         │ Persistence Analysis    │
                         └─────────────────────────┘
```

---

# End-to-End Processing Pipeline

DeepSight separates ingestion, processing, inference, evidence generation, and review.

## Stage 1 — Ingestion

A user submits sonar imagery through the application.

The backend creates an ingestion job and persists the associated state.

The system applies configured limits such as:

* maximum upload size
* maximum number of files per job
* maximum image width
* maximum image height
* concurrent processing limits

---

## Stage 2 — Job Processing

A dedicated worker continuously polls for queued jobs.

The worker:

1. acquires a PostgreSQL advisory lock
2. recovers orphaned jobs when necessary
3. claims the next queued job
4. executes the ingestion pipeline
5. records processing failures
6. continues polling for subsequent jobs

The current worker polling interval is **1 second**.

A PostgreSQL advisory lock prevents multiple marine-ingestion workers from processing the same worker workload simultaneously.

---

## Stage 3 — AI Inference

The configured model is loaded through the project's model/inference layer.

Current default model configuration:

```text
Model:
ghostvision-crab-pot-custom

Version:
v5-hardneg-epoch9-640-6caf0930

Architecture:
YOLO11n

Input size:
640

Confidence threshold:
0.25

IoU threshold:
0.45

Device:
CPU by default

Tiling:
Disabled by default
```

The model registry is used to identify the active artifact and associated metadata.

---

## Stage 4 — Evidence Extraction

A prediction is not treated as self-explanatory.

DeepSight can extract additional evidence associated with a detection, allowing reviewers to inspect information surrounding the predicted object.

This supports a more transparent workflow:

```text
Prediction
   │
   ├── Bounding box
   ├── Confidence
   ├── Model identity
   ├── Model version
   ├── Source image
   └── Acoustic / image evidence
```

---

## Stage 5 — Cross-Frame Persistence

A sonar object may appear in multiple adjacent frames.

Treating every detection independently can create repeated observations of the same physical object.

DeepSight therefore includes processing intended to support cross-frame persistence analysis.

The goal is to distinguish:

```text
Frame A ──┐
Frame B ──┼──► repeated observation
Frame C ──┘
```

from unrelated detections.

---

## Stage 6 — Geospatial Association

When valid geospatial metadata exists, it can be associated with detections.

DeepSight follows an important data-integrity rule:

> **Unavailable metadata remains unavailable.**

The system does not manufacture coordinates when source metadata does not contain valid location information.

---

## Stage 7 — Human Review

AI output enters a review workflow.

Reviewers can inspect detections and associated evidence before accepting or rejecting them.

This creates a distinction between:

```text
AI Prediction
      ↓
Review Candidate
      ↓
Human Decision
      ↓
Reviewed Result
```

The AI prediction itself is not automatically treated as confirmed ground truth.

---

# Explainable Acoustic Evidence

One of the project's important design goals is moving beyond:

> "The model detected an object."

toward:

> "The model detected an object, and the application can expose additional measurable evidence associated with that detection."

Evidence can help a reviewer understand the prediction in the context of the underlying sonar image.

This is particularly important for sonar imagery because acoustic signatures can be ambiguous and can differ significantly from conventional photographic appearance.

---

# Cross-Frame Persistence

Marine sonar surveys commonly contain sequential or overlapping observations.

A detection appearing in several frames may provide stronger contextual evidence than an isolated prediction.

DeepSight therefore treats temporal/frame relationships as part of the analysis workflow.

The system can preserve relationships between observations rather than reducing the entire pipeline to independent frame-level bounding boxes.

---

# Geolocation

Geospatial information is treated as source-derived data.

The system can preserve available positioning metadata and expose it alongside relevant detection information.

The implementation intentionally avoids fabricated coordinates.

```text
Valid metadata
      │
      ▼
Detection ↔ Location

Missing metadata
      │
      ▼
Location remains unavailable
```

This distinction is important for scientific traceability.

---

# Human Review

The review workflow is designed around the principle that machine predictions require contextual verification.

A reviewer can inspect:

* detected object
* confidence
* model/version
* evidence
* source information
* available geospatial information
* detection context

The review state is persisted in the application database.

This allows downstream reports to distinguish between model-generated predictions and reviewed outcomes.

---

# Reports and Provenance

DeepSight is designed to preserve provenance throughout the processing chain.

Relevant information may include:

* source image
* ingestion job
* detection
* model name
* model version
* model artifact
* evidence
* review decision
* geospatial metadata
* processing state

The objective is to make a detection traceable rather than producing an unexplained final result.

---

# Technology Stack

## Backend

* Python
* FastAPI
* Uvicorn
* SQLAlchemy
* Alembic
* Pydantic Settings
* Psycopg
* GeoAlchemy2
* PostgreSQL
* PostGIS

## AI / Computer Vision

* Ultralytics
* YOLO-based detection
* OpenCV
* NumPy-based image processing
* Versioned model artifacts
* Model registry

## Frontend

* React
* TypeScript
* Vite
* React Leaflet
* Leaflet
* Lucide React
* ESLint

## Infrastructure

* Redis
* Docker
* Git
* GitHub Actions
* Local filesystem storage
* S3-compatible storage support through `boto3`

---

# Repository Structure

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
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig*.json
│
├── ml/
│   ├── evidence/
│   ├── inference/
│   └── models/
│       └── model_registry.json
│
├── runs/
│   └── error_analysis/
│
├── services/
│   ├── api/
│   │   ├── alembic/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── config.py
│   │   ├── db.py
│   │   └── main.py
│   │
│   └── worker/
│       ├── job_runner.py
│       └── worker.py
│
├── storage/
│   └── runs/
│
├── tests/
│
├── Dockerfile
├── alembic.ini
├── requirements-backend.txt
├── .env.example
└── README.md
```

The repository also contains a collection of model-development and evaluation utilities for dataset construction, error analysis, false-positive analysis, localization analysis, confidence analysis, and audit generation.

---

# Local Development

## Prerequisites

Before running DeepSight locally, install:

* Python 3.14
* Node.js and npm
* PostgreSQL
* PostGIS extension
* Redis
* Git

The backend dependencies are pinned in:

```text
requirements-backend.txt
```

The frontend dependencies are pinned through:

```text
frontend/package.json
frontend/package-lock.json
```

---

## 1. Clone the Repository

```powershell
git clone https://github.com/ronny-dev01/DeepSight.git
cd DeepSight
```

---

## 2. Create the Python Virtual Environment

From the repository root:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Your terminal should then show the virtual environment, for example:

```text
(.venv) PS D:\Projects\DeepSight>
```

---

## 3. Install Backend Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements-backend.txt
```

---

## 4. Install Frontend Dependencies

Open another PowerShell terminal or continue from the project root:

```powershell
cd frontend
npm install
cd ..
```

---

# Environment Configuration

Create a local `.env` file from the provided example:

```powershell
Copy-Item .env.example .env
```

The default development configuration expects:

```env
PROJECT_NAME=SIH2026_MarineMVP
ENVIRONMENT=development
FRONTEND_ORIGIN=

DATABASE_URL=postgresql+psycopg://sonar:sonar@localhost:5432/sonar_mvp
REDIS_URL=redis://localhost:6379/0

MAX_UPLOAD_BYTES=524288000
MAX_FILES_PER_JOB=200
MAX_IMAGE_WIDTH=12000
MAX_IMAGE_HEIGHT=12000
MAX_CONCURRENT_JOBS=1

MODEL_NAME=ghostvision-crab-pot-custom
MODEL_VERSION=v5-hardneg-epoch9-640-6caf0930
MODEL_PATH=storage/runs/crab_pot_v5_finetune_hardneg/weights/best.pt
MODEL_ARTIFACT_KEY=models/ghostvision-crab-pot-custom/v5-hardneg-epoch9-640-6caf0930/best.pt
MODEL_DEVICE=cpu
MODEL_CONFIDENCE=0.25
MODEL_IOU=0.45
MODEL_IMAGE_SIZE=640

MODEL_TILING_ENABLED=false
MODEL_TILE_SIZE=384
MODEL_TILE_STRIDE=256
MODEL_TILE_IOU=0.70
MODEL_TILE_NMS_IOU=0.50

MODEL_REGISTRY_PATH=ml/models/model_registry.json
MODEL_VERIFY_HASH=true

STORAGE_BACKEND=local
STORAGE_BUCKET=
STORAGE_REGION=
STORAGE_ENDPOINT_URL=
STORAGE_PREFIX=

API_HOST=127.0.0.1
API_PORT=8000
```

### Important

Do not commit your real `.env` file.

The repository contains `.env.example` as the development configuration template.

---

# Database Setup

DeepSight uses PostgreSQL and PostGIS.

The development configuration expects:

```text
Database:
sonar_mvp

User:
sonar

Password:
sonar

Host:
localhost

Port:
5432
```

The database must have the PostGIS extension available because the application uses geospatial database functionality.

Once PostgreSQL is running and the database exists, apply the Alembic migrations:

```powershell
alembic upgrade head
```

The Alembic configuration reads the database URL from the application's settings.

---

# Redis

The development configuration expects Redis at:

```text
redis://localhost:6379/0
```

Start Redis using your local Redis installation or your preferred local Redis runtime.

Verify that Redis is available before starting the application services.

---

# Running the Backend

From the repository root with the Python virtual environment activated:

```powershell
uvicorn services.api.main:app --reload --host 127.0.0.1 --port 8000
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI also provides its development API documentation through its standard documentation endpoints.

---

# Running the Worker

The ingestion worker is a separate process.

Open another PowerShell terminal, activate the virtual environment, and run:

```powershell
python -m services.worker.worker
```

The worker continuously checks for queued ingestion jobs.

Its current behavior includes:

* PostgreSQL advisory locking
* orphaned-job recovery
* queued-job claiming
* ingestion processing
* exception logging
* continuous polling

The worker uses a **1-second polling interval**.

Only one worker acquires the configured PostgreSQL advisory lock for the marine-ingestion workload.

---

# Running the Frontend

Open another terminal:

```powershell
cd frontend
npm run dev
```

Vite will start the development server.

The frontend API client reads:

```text
VITE_API_BASE_URL
```

from the frontend environment.

For local development, configure the frontend API base URL to point to the backend:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

# Development Process Layout

A typical local development setup therefore consists of three running processes:

### Terminal 1 — API

```powershell
uvicorn services.api.main:app --reload --host 127.0.0.1 --port 8000
```

### Terminal 2 — Worker

```powershell
python -m services.worker.worker
```

### Terminal 3 — Frontend

```powershell
cd frontend
npm run dev
```

PostgreSQL and Redis must also be running.

---

# Running with Docker

The repository includes a backend Dockerfile.

Build the image:

```powershell
docker build -t deepsight-backend .
```

Run the container:

```powershell
docker run --rm -p 8000:8000 deepsight-backend
```

The container starts the FastAPI application using:

```text
uvicorn services.api.main:app --host 0.0.0.0 --port 8000
```

The current Dockerfile packages the Python backend runtime and application code.

Database and Redis connectivity still need to be provided through the container environment/network configuration.

---

# API Surface

The FastAPI application currently exposes functionality around several primary areas:

```text
Health
  └── service health / dependency state

Ingestion
  └── upload and processing workflows

Review
  └── detection review and review state

Reports
  └── structured report generation
```

The implementation is organized under:

```text
services/api/routes/
```

with:

```text
health.py
ingestion.py
review.py
report.py
```

---

# Model Registry

DeepSight maintains model metadata through:

```text
ml/models/model_registry.json
```

The registry identifies the active model and its artifact information.

The application can verify the model artifact hash before using it.

This provides a reproducibility mechanism between:

```text
Model Name
     │
     ▼
Model Version
     │
     ▼
Artifact
     │
     ▼
SHA-256
     │
     ▼
Inference Runtime
```

---

# Model and Evaluation

The currently registered primary model is:

```text
Model:
ghostvision-crab-pot-custom

Version:
v5-hardneg-epoch9-640-6caf0930

Architecture:
YOLO11n

Input:
640 × 640

Class:
Crab-Pot
```

## Recorded validation metrics

The model registry records the following validation metrics:

| Metric    | Validation |
| --------- | ---------: |
| Precision |     0.5860 |
| Recall    |     0.5035 |
| mAP50     |     0.5010 |
| mAP50-95  |     0.1702 |

## Recorded test metrics

The recorded test evaluation contains:

```text
Images:     398
Instances:  567
```

| Metric    |   Test |
| --------- | -----: |
| Precision | 0.4478 |
| Recall    | 0.4074 |
| mAP50     | 0.3739 |
| mAP50-95  | 0.1487 |

These metrics describe the recorded evaluation runs and should not be interpreted as a guarantee of performance on arbitrary real-world sonar surveys.

### Confidence is not accuracy

The inference confidence threshold is currently configured at:

```text
0.25
```

A model confidence score is not equivalent to accuracy.

Changing the confidence threshold changes the precision/recall operating point; it does not automatically make the underlying model more accurate.

---

# Model Development and Analysis

The repository contains tooling for investigating model behavior beyond a single aggregate metric.

Examples include utilities for:

* ground-truth annotation analysis
* false-positive analysis
* false-positive type analysis
* IoU analysis
* localization analysis
* confidence comparisons
* hard-negative mining
* high-confidence FP/TP audits
* dataset construction
* model error analysis
* contact-sheet generation
* annotation audits

Representative scripts include:

```text
analyze_gt_annotations.py
analyze_v5_errors.py
analyze_v5_fp.py
analyze_v5_fp_types.py
compare_v1_v5_fp_thresholds.py
compare_v1_v5_recall_matched.py
make_high_conf_fp_tp_audit.py
make_annotation_audit.py
make_localization_sheet.py
```

This analysis layer is intended to support evidence-based model iteration rather than relying exclusively on a single metric.

---

# Testing and Quality Checks

Backend contract tests are included under:

```text
tests/
```

The project also contains GitHub Actions configuration under:

```text
.github/workflows/
```

Frontend quality checks are available through:

```powershell
cd frontend
npm run lint
```

Frontend production build:

```powershell
npm run build
```

Preview the production build locally:

```powershell
npm run preview
```

Before committing changes, useful repository checks include:

```powershell
git diff --check
```

and the relevant backend/frontend tests and builds.

---

# Engineering Principles

DeepSight follows several project-level principles.

## No mock detections

Production application results should originate from the actual inference and persistence pipeline.

## No fabricated coordinates

If geospatial metadata is unavailable, the application should preserve that absence.

## No hardcoded result arrays

Detection results should come from actual processing and persisted application state.

## No fake metrics

Model metrics must correspond to recorded evaluation results.

## Database as the source of truth

Application state should be persisted and retrieved through the backend data layer.

## Model provenance

The active model, version, artifact, and verification information should remain traceable.

## Human-in-the-loop validation

AI-generated detections are review candidates rather than automatic scientific conclusions.

## Evidence over assumptions

The system should expose measurable evidence wherever possible and avoid claiming information that the source data cannot support.

---

# Current Limitations

DeepSight is an actively developed SIH 2026 MVP and has important limitations.

### Model limitations

The current registered model has moderate recorded evaluation metrics and should not be treated as a universally reliable marine-object detector.

The available evaluation is associated with the datasets and splits used during development.

Real-world performance can vary with:

* sonar sensor
* acquisition conditions
* depth
* seabed characteristics
* object appearance
* resolution
* noise
* preprocessing
* geographic environment

### Class coverage

The current registered model configuration identifies:

```text
Crab-Pot
```

as its detection class.

The system architecture is intended to support broader anomaly/debris detection, but a single registered model/class should not be presented as comprehensive marine debris recognition.

### Geolocation

Location information depends on valid source metadata.

No location should be inferred merely because a detection exists.

### Generalization

Recorded benchmark performance does not establish generalization to every sonar system, geographic region, or acquisition condition.

---

# Roadmap

Future development areas include:

* expanded marine debris/anomaly classes
* stronger cross-frame association
* improved acoustic evidence extraction
* additional sonar preprocessing techniques
* broader evaluation datasets
* harder geographic/source-domain validation
* improved model calibration
* more advanced geospatial visualization
* scalable background processing
* cloud deployment
* object-storage integration
* production observability
* richer report generation
* role-based research workflows
* improved model/version management

---

# Smart India Hackathon Context

## SIH 2026

**Problem Statement:** SIH26057

**Title:**

> AI-Powered Automated Underwater Marine Debris and Anomaly Detection System using Side-Scan Sonar Imagery

**Organization:**

Ministry of Earth Sciences (MoES) / National Institute of Ocean Technology (NIOT)

DeepSight is being developed as the technical platform for addressing the problem through a combination of:

* computer vision
* marine sonar analysis
* machine learning
* geospatial processing
* backend engineering
* human review
* data provenance

---

# Why DeepSight?

DeepSight is not intended to be only a YOLO inference demo.

The broader objective is to build a complete engineering workflow around marine sonar intelligence:

```text
                ┌────────────────────┐
                │   Real Sonar Data  │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │   AI Detection     │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ Acoustic Evidence  │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ Cross-Frame Context│
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ Geospatial Context │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │   Human Review     │
                └─────────┬──────────┘
                          │
                          ▼
                ┌────────────────────┐
                │ Research / Report  │
                └────────────────────┘
```

The value of the platform is therefore in connecting these stages into a traceable workflow.

---

# Project Status

DeepSight is an **active Smart India Hackathon 2026 MVP under development**.

Current implementation areas include:

* React/TypeScript frontend
* FastAPI backend
* PostgreSQL/PostGIS persistence
* Redis integration
* background ingestion worker
* YOLO-based marine detection
* model registry
* evidence extraction
* cross-frame analysis
* geospatial handling
* human review workflow
* reporting
* automated testing
* Docker support
* CI workflow
* model evaluation and error-analysis tooling

The system should be evaluated according to the capabilities actually implemented in the current repository rather than treating planned roadmap functionality as completed functionality.

---

# Development Philosophy

DeepSight is being developed with an emphasis on:

**Real Data**

Use real sonar data and real persisted application state wherever available.

**Traceability**

Every meaningful result should be traceable back to its source and processing context.

**Reproducibility**

Model versions, artifacts, configurations, and migrations should be identifiable.

**Explainability**

Where possible, expose evidence that helps a reviewer understand the prediction.

**Human Oversight**

Machine predictions should support researchers rather than silently replacing their judgment.

**Engineering Discipline**

Changes should be developed through isolated branches, tested, reviewed, and integrated through version control.

---

# License

This repository is currently maintained as part of the Smart India Hackathon 2026 project.

License and redistribution terms should be added here when the project establishes its final licensing policy.
