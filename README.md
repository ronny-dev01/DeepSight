# DeepSight

### AI-Powered Underwater Marine Debris & Anomaly Detection using Side-Scan Sonar Imagery

**Smart India Hackathon 2026 — SIH26057**
**Organization:** Ministry of Earth Sciences (MoES) / National Institute of Ocean Technology (NIOT)

DeepSight is an AI-powered marine sonar analysis platform designed to process **Side-Scan Sonar (SSS) imagery**, detect underwater objects and anomalies using computer vision, extract supporting acoustic evidence, associate detections with available geospatial metadata, and provide a human-in-the-loop review workflow.

The current project is developed and tested **locally on localhost**.

> **Current status:** Local development / SIH 2026 MVP
> **Deployment:** Not currently deployed

---

## Table of Contents

* [Overview](#overview)
* [Problem](#problem)
* [Solution](#solution)
* [Core Capabilities](#core-capabilities)
* [System Architecture](#system-architecture)
* [Processing Pipeline](#processing-pipeline)
* [AI/ML Pipeline](#aiml-pipeline)
* [Explainable Evidence](#explainable-evidence)
* [Cross-Frame Persistence](#cross-frame-persistence)
* [Geolocation](#geolocation)
* [Human Review](#human-review)
* [Technology Stack](#technology-stack)
* [Repository Structure](#repository-structure)
* [Local Setup](#local-setup)
* [Environment Configuration](#environment-configuration)
* [Database Setup](#database-setup)
* [Run the Backend](#run-the-backend)
* [Run the Worker](#run-the-worker)
* [Run the Frontend](#run-the-frontend)
* [Local Development Workflow](#local-development-workflow)
* [API](#api)
* [Model Configuration](#model-configuration)
* [Model Evaluation](#model-evaluation)
* [Testing](#testing)
* [Current Limitations](#current-limitations)
* [Roadmap](#roadmap)
* [Smart India Hackathon](#smart-india-hackathon)
* [Project Status](#project-status)

---

# Overview

Side-Scan Sonar imagery is fundamentally different from conventional RGB imagery.

Instead of visible colors and textures, sonar imagery represents acoustic returns from the underwater environment. Objects can appear through combinations of:

* acoustic intensity
* shape
* texture
* shadow
* seabed interaction
* surrounding context

DeepSight combines machine learning with a backend processing pipeline and a web-based review interface.

```text
Side-Scan Sonar Image
          │
          ▼
     Data Ingestion
          │
          ▼
   Image Validation
          │
          ▼
    AI Detection
          │
          ▼
 Acoustic Evidence
          │
          ▼
 Cross-Frame Analysis
          │
          ▼
 Geospatial Metadata
          │
          ▼
     Human Review
          │
          ▼
   Research / Report
```

---

# Problem

Underwater marine surveys can generate large volumes of sonar imagery that may require extensive manual inspection.

Potential challenges include:

* large sonar datasets
* visually ambiguous acoustic signatures
* repeated observations across frames
* uncertain object boundaries
* false detections
* different sonar acquisition conditions
* incomplete positioning metadata
* difficulty explaining AI predictions
* need for human validation

A useful system therefore needs more than an object detector.

It needs a workflow connecting:

**sonar data → AI detection → evidence → context → review → report**

---

# Solution

DeepSight provides an integrated local web application for marine sonar analysis.

The platform is designed around several major components.

### AI Detection

A YOLO-based computer-vision model analyzes sonar imagery and generates candidate detections.

### Acoustic Evidence

Additional information can be extracted around detections to provide supporting evidence for review.

### Cross-Frame Analysis

Detections can be analyzed across multiple frames instead of treating every prediction as completely independent.

### Geospatial Context

Available positioning metadata can be associated with detections.

### Human Review

Researchers can review AI-generated detections before considering them confirmed results.

### Persistent Data

Jobs, detections, review information, and associated metadata are persisted through the backend database.

---

# Core Capabilities

| Capability            | Description                             |
| --------------------- | --------------------------------------- |
| Sonar ingestion       | Process real Side-Scan Sonar imagery    |
| AI detection          | YOLO-based object detection             |
| Model registry        | Versioned model metadata                |
| Artifact verification | Optional model hash verification        |
| Evidence extraction   | Additional detection-related evidence   |
| Cross-frame analysis  | Analyze repeated observations           |
| Geolocation           | Preserve available positioning metadata |
| Human review          | Review AI-generated detections          |
| Reports               | Generate structured report information  |
| Persistent storage    | PostgreSQL/PostGIS                      |
| Background processing | Dedicated ingestion worker              |
| REST API              | FastAPI backend                         |
| Web interface         | React + TypeScript frontend             |

---

# System Architecture

```text
                         ┌─────────────────────────┐
                         │     React Frontend      │
                         │     TypeScript/Vite     │
                         └────────────┬────────────┘
                                      │
                                      │ HTTP
                                      ▼
                         ┌─────────────────────────┐
                         │      FastAPI API        │
                         │                         │
                         │  Ingestion              │
                         │  Review                 │
                         │  Reports                │
                         │  Health                 │
                         └───────────┬─────────────┘
                                     │
                         ┌───────────┴───────────┐
                         │                       │
                         ▼                       ▼
                ┌─────────────────┐      ┌───────────────┐
                │   PostgreSQL    │      │     Redis     │
                │    + PostGIS    │      │               │
                └────────┬────────┘      └───────────────┘
                         │
                         ▼
                ┌─────────────────────┐
                │   Background Worker │
                │                     │
                │  Job Queue          │
                │  Ingestion          │
                │  AI Processing      │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │     ML Pipeline     │
                │                     │
                │  Model Registry     │
                │  YOLO Detection     │
                │  Evidence           │
                │  Analysis           │
                └─────────────────────┘
```

Everything currently runs on the developer's local machine.

---

# Processing Pipeline

## 1. Sonar Ingestion

A user uploads sonar imagery through the frontend.

The backend creates an ingestion job and stores its state.

The application enforces configurable limits for:

* upload size
* number of files
* image dimensions
* concurrent processing

---

## 2. Background Processing

The ingestion worker continuously checks for queued jobs.

The worker:

1. acquires a PostgreSQL advisory lock
2. recovers orphaned jobs
3. claims queued jobs
4. processes ingestion
5. runs the processing pipeline
6. records failures
7. continues polling

The current polling interval is:

```text
1 second
```

---

## 3. AI Detection

The configured YOLO model processes the sonar imagery.

The current default configuration uses:

```text
Model:
ghostvision-crab-pot-custom

Version:
v5-hardneg-epoch9-640-6caf0930

Architecture:
YOLO11n

Image Size:
640

Confidence Threshold:
0.25

IoU Threshold:
0.45

Device:
CPU

Tiling:
Disabled by default
```

---

## 4. Evidence Extraction

Detection results can be accompanied by additional evidence derived from the source sonar imagery.

This allows the review interface to provide more context than simply displaying a bounding box.

```text
AI Prediction
     │
     ├── Class
     ├── Bounding Box
     ├── Confidence
     ├── Model
     ├── Model Version
     ├── Source
     └── Evidence
```

---

## 5. Cross-Frame Persistence

The same physical object can appear in multiple sonar frames.

DeepSight therefore includes analysis intended to associate repeated observations across frames.

```text
Frame 1 ──┐
Frame 2 ──┼──► Potential persistent observation
Frame 3 ──┘
```

This helps provide contextual information around individual predictions.

---

## 6. Geolocation

When valid positioning metadata exists, it can be associated with detection information.

DeepSight does **not** generate fake coordinates.

```text
Metadata available
       │
       ▼
Detection + Location

Metadata unavailable
       │
       ▼
Location remains unavailable
```

This keeps location information traceable to the original source data.

---

## 7. Human Review

AI predictions enter a review workflow.

A reviewer can inspect available information before making a decision.

```text
AI Detection
     │
     ▼
Review Candidate
     │
     ▼
Human Decision
     │
     ▼
Persisted Review Result
```

The objective is to keep humans in the decision loop instead of treating every model prediction as confirmed truth.

---

# Explainable Evidence

DeepSight is designed around the idea that:

> A model prediction should be accompanied by useful context whenever that context can be derived from the source data.

The review interface can expose evidence associated with detections, helping researchers investigate why a prediction was generated.

This is particularly useful for sonar imagery because underwater acoustic signatures can be ambiguous.

---

# Geospatial Information

Geospatial information is treated as source-derived data.

If valid metadata is available, DeepSight can preserve and expose that information alongside detection results.

If metadata is unavailable, the system does not fabricate coordinates.

This distinction is important for maintaining data provenance.

---

# Human Review

The review interface is designed to help researchers inspect AI-generated detections.

Depending on the available information, a reviewer can inspect:

* detected class
* confidence
* bounding box
* source image
* model name
* model version
* evidence
* geospatial information
* review state

This creates a clear distinction between:

```text
Model Prediction
       ≠
Confirmed Result
```

---

# Technology Stack

## Backend

* Python
* FastAPI
* Uvicorn
* SQLAlchemy
* Alembic
* Psycopg
* Pydantic Settings
* GeoAlchemy2
* PostgreSQL
* PostGIS

## Machine Learning

* Ultralytics
* YOLO
* OpenCV
* Computer vision
* Model registry
* Model artifact verification

## Frontend

* React
* TypeScript
* Vite
* React Leaflet
* Leaflet
* Lucide React
* ESLint

## Local Infrastructure

* PostgreSQL
* PostGIS
* Redis
* Python virtual environment
* Node.js / npm

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
│   ├── package-lock.json
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

The repository also contains multiple scripts used for:

* dataset analysis
* false-positive analysis
* hard-negative generation
* model error analysis
* confidence analysis
* localization analysis
* annotation auditing
* evaluation
* visualization

---

# Local Setup

DeepSight currently runs **locally**.

There is no cloud deployment required for the current development setup.

## Prerequisites

Install the following:

* Git
* Python 3.14
* Node.js
* npm
* PostgreSQL
* PostGIS
* Redis

---

# 1. Clone the Repository

```powershell
git clone https://github.com/ronny-dev01/DeepSight.git
cd DeepSight
```

---

# 2. Create the Python Environment

From the project root:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

You should see:

```text
(.venv) PS D:\Projects\DeepSight>
```

---

# 3. Install Backend Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements-backend.txt
```

The backend requirements include:

```text
FastAPI
Uvicorn
SQLAlchemy
Alembic
Psycopg
GeoAlchemy2
Pydantic Settings
OpenCV
Ultralytics
Boto3
```

---

# 4. Install Frontend Dependencies

```powershell
cd frontend
npm install
cd ..
```

---

# Environment Configuration

Create your local environment file:

```powershell
Copy-Item .env.example .env
```

The default local configuration expects PostgreSQL and Redis to run on the local machine.

Important environment variables include:

```env
DATABASE_URL=postgresql+psycopg://sonar:sonar@localhost:5432/sonar_mvp

REDIS_URL=redis://localhost:6379/0

MODEL_NAME=ghostvision-crab-pot-custom
MODEL_VERSION=v5-hardneg-epoch9-640-6caf0930
MODEL_PATH=storage/runs/crab_pot_v5_finetune_hardneg/weights/best.pt

MODEL_DEVICE=cpu
MODEL_CONFIDENCE=0.25
MODEL_IOU=0.45
MODEL_IMAGE_SIZE=640

STORAGE_BACKEND=local

API_HOST=127.0.0.1
API_PORT=8000
```

### Do not commit `.env`

Your actual `.env` contains local configuration and should remain untracked.

---

# Database Setup

DeepSight uses:

```text
PostgreSQL
+
PostGIS
```

The default development database configuration is:

```text
Host:     localhost
Port:     5432
Database: sonar_mvp
User:     sonar
Password: sonar
```

Make sure PostgreSQL is running and the database exists.

PostGIS must also be available because DeepSight uses geospatial functionality.

---

# Run Database Migrations

From the project root:

```powershell
alembic upgrade head
```

Alembic uses the database URL configured through the application's settings.

The migration configuration is located at:

```text
services/api/alembic/
```

---

# Start Redis

Make sure Redis is running locally:

```text
redis://localhost:6379/0
```

The backend expects Redis to be available at this address unless `.env` is configured differently.

---

# Run the Backend

Open **PowerShell Terminal 1**.

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then run:

```powershell
uvicorn services.api.main:app --reload --host 127.0.0.1 --port 8000
```

The backend will run at:

```text
http://127.0.0.1:8000
```

---

# Run the Worker

Open **PowerShell Terminal 2**.

Activate the virtual environment:

```powershell
cd D:\Projects\DeepSight
.\.venv\Scripts\Activate.ps1
```

Run the worker:

```powershell
python -m services.worker.worker
```

The worker will continuously monitor queued ingestion jobs.

It uses a PostgreSQL advisory lock to prevent multiple marine-ingestion workers from processing the same workload simultaneously.

---

# Run the Frontend

Open **PowerShell Terminal 3**.

```powershell
cd D:\Projects\DeepSight\frontend
npm run dev
```

Vite will start the frontend development server.

The frontend API client uses:

```text
VITE_API_BASE_URL
```

Configure it to point to the local backend:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Then open the local Vite URL shown in the terminal.

---

# Complete Local Development Setup

At runtime, DeepSight currently consists of:

```text
                 LOCAL MACHINE
┌──────────────────────────────────────────────┐
│                                              │
│  PostgreSQL + PostGIS                        │
│       │                                      │
│       ├──────────────┐                       │
│       │              │                       │
│       ▼              ▼                       │
│    FastAPI          Worker                   │
│       │              │                       │
│       │              ▼                       │
│       │          ML Pipeline                 │
│       │                                      │
│       ▼                                      │
│  React/Vite Frontend                         │
│                                              │
│  Redis                                       │
│                                              │
└──────────────────────────────────────────────┘
```

### Terminal 1 — Backend

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

### Required local services

```text
PostgreSQL + PostGIS
Redis
```

---

# API

The backend is organized into several API areas:

```text
services/api/routes/
│
├── health.py
├── ingestion.py
├── review.py
└── report.py
```

The API is implemented using FastAPI.

The application entry point is:

```text
services.api.main:app
```

---

# Model Configuration

The active model is configured through:

```text
ml/models/model_registry.json
```

Current model:

```text
ghostvision-crab-pot-custom
```

Current version:

```text
v5-hardneg-epoch9-640-6caf0930
```

Architecture:

```text
YOLO11n
```

Input resolution:

```text
640 × 640
```

Current detection class:

```text
Crab-Pot
```

Default inference configuration:

```text
Confidence: 0.25
IoU:        0.45
Device:     CPU
Tiling:     Disabled
```

The application can verify the model artifact hash through the model registry configuration.

---

# Model Evaluation

The currently registered model has recorded validation and test metrics.

## Validation

| Metric    |  Value |
| --------- | -----: |
| Precision | 0.5860 |
| Recall    | 0.5035 |
| mAP50     | 0.5010 |
| mAP50-95  | 0.1702 |

## Test

```text
Images:     398
Instances:  567
```

| Metric    |  Value |
| --------- | -----: |
| Precision | 0.4478 |
| Recall    | 0.4074 |
| mAP50     | 0.3739 |
| mAP50-95  | 0.1487 |

These are recorded evaluation results for the current model/version and are not a guarantee of performance on every real-world sonar dataset.

### Confidence vs Accuracy

The configured confidence threshold is:

```text
0.25
```

Confidence is not the same thing as accuracy.

A high confidence score does not automatically mean that a prediction is correct, and changing the confidence threshold changes the operating point between precision and recall.

---

# Model Analysis

The repository contains several analysis utilities used during model development.

Examples include:

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

generate_v5_raw_predictions.py
tp_confidence_compare.py
```

These tools are used to investigate:

* false positives
* false negatives
* confidence distributions
* localization
* IoU
* dataset quality
* hard negatives
* annotation quality
* model failure cases

---

# Testing

## Backend

Backend tests are located under:

```text
tests/
```

The project also contains GitHub Actions configuration for automated backend contract testing.

## Frontend lint

```powershell
cd frontend
npm run lint
```

## Frontend build

```powershell
npm run build
```

The build performs TypeScript compilation and the Vite production build.

## Frontend preview

```powershell
npm run preview
```

## Git whitespace check

Before committing changes:

```powershell
git diff --check
```

---

# Current Limitations

DeepSight is an actively developed **SIH 2026 MVP**.

The following limitations should be considered.

## Model performance

The current model's recorded evaluation metrics do not establish universal performance across all marine sonar environments.

Performance can vary depending on:

* sonar hardware
* acquisition conditions
* depth
* seabed type
* image quality
* resolution
* object appearance
* noise
* preprocessing
* geographic environment

## Detection classes

The current registered model is configured for:

```text
Crab-Pot
```

The broader DeepSight architecture is intended for marine debris and anomaly detection, but the current model should not be represented as a complete detector for every marine object.

## Geolocation

Geolocation depends on valid source metadata.

The application does not invent coordinates when source positioning information is unavailable.

## Generalization

Benchmark metrics from a particular dataset or evaluation split should not automatically be interpreted as real-world performance across unrelated sonar surveys.

---

# Roadmap

Potential future development includes:

* additional marine debris classes
* broader anomaly detection
* improved cross-frame association
* stronger acoustic evidence extraction
* improved model calibration
* larger and more diverse datasets
* geographic/source-domain evaluation
* improved geospatial visualization
* richer reporting
* advanced model version management
* production deployment
* cloud object storage
* scalable processing infrastructure
* monitoring and observability

These items represent future development and should not be interpreted as currently deployed functionality.

---

# Engineering Principles

DeepSight follows several important development principles.

### Real Data

Use actual sonar data and persisted application state.

### No Mock Detections

Detection results should originate from the actual inference pipeline.

### No Fake Coordinates

Unavailable geospatial metadata remains unavailable.

### No Hardcoded Results

Application results should come from actual processing and database state.

### No Fake Metrics

Evaluation numbers must correspond to actual recorded experiments.

### Database as Source of Truth

Persisted backend state is authoritative.

### Model Provenance

Model name, version, artifact, and verification information should remain traceable.

### Human-in-the-Loop

AI predictions are review candidates rather than automatic scientific conclusions.

### Evidence-Based Development

Model improvements should be supported by measurable evaluation and error analysis.

---

# Smart India Hackathon 2026

### Problem Statement

**SIH26057**

### Title

**AI-Powered Automated Underwater Marine Debris and Anomaly Detection System using Side-Scan Sonar Imagery**

### Organization

**Ministry of Earth Sciences (MoES) / National Institute of Ocean Technology (NIOT)**

DeepSight is being developed to address this problem through a combination of:

* artificial intelligence
* computer vision
* Side-Scan Sonar analysis
* geospatial processing
* backend engineering
* human review
* data provenance

---

# Project Status

**Development Stage:** Active MVP development

**Execution Environment:** Localhost

**Cloud Deployment:** Not currently deployed

**Primary Model:** `ghostvision-crab-pot-custom`

**Backend:** FastAPI

**Frontend:** React + TypeScript + Vite

**Database:** PostgreSQL + PostGIS

**Background Processing:** Python worker

**Cache / Supporting Service:** Redis

---

# Development Philosophy

DeepSight is being developed as more than a model inference demo.

The goal is to create a traceable engineering workflow:

```text
Real Sonar Data
      │
      ▼
AI Detection
      │
      ▼
Acoustic Evidence
      │
      ▼
Cross-Frame Context
      │
      ▼
Geospatial Context
      │
      ▼
Human Review
      │
      ▼
Persisted Result
      │
      ▼
Research Report
```

The project prioritizes:

**Traceability**
Results should remain connected to their source and processing context.

**Reproducibility**
Models, versions, configurations, and database migrations should be identifiable.

**Explainability**
Useful evidence should be available around AI-generated detections.

**Human Oversight**
Researchers remain part of the final review process.

**Engineering Discipline**
Changes should be tested, reviewed, and tracked through version control.

---

## Local Development Summary

```powershell
# Backend environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-backend.txt

# Database
alembic upgrade head

# Terminal 1 — API
uvicorn services.api.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — Worker
python -m services.worker.worker

# Terminal 3 — Frontend
cd frontend
npm install
npm run dev
```

DeepSight currently runs locally and is intended to be developed, tested, and demonstrated through this localhost environment.
