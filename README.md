# 🌊 DeepSight

**AI-powered underwater marine-debris & anomaly detection from side-scan sonar imagery.** Smart India Hackathon 2026 · Problem Statement **SIH26057** · Organization **MoES / NIOT**.

DeepSight ingests real **Side-Scan Sonar (SSS)** imagery, runs YOLO-based detection, extracts acoustic evidence, analyzes detections across frames, uses available geospatial metadata, and provides a human-review workflow with structured reporting. The current shipped model detects **Crab-Pot**.

> **Current status:** Local development · not currently deployed.

---

## 1. Repository layout

```text
DeepSight/
├── .github/              GitHub Actions / CI
├── data/                 Source and processing data
├── docs/                 Project documentation
├── frontend/             React + TypeScript + Vite dashboard
│   ├── src/
│   └── package.json
├── ml/                   Detection and evidence pipeline
│   ├── evidence/
│   ├── inference/
│   └── models/
├── runs/                 Training / analysis runs
├── services/
│   ├── api/              FastAPI application
│   └── worker/           Background processing worker
├── storage/              Model / run artifacts
├── tests/                Backend / contract tests
├── .env.example
├── alembic.ini
├── requirements-backend.txt
├── Dockerfile
└── README.md
```

The database is **PostgreSQL + PostGIS** and Redis is used for background-job coordination.

---

## 2. Run it locally

The application consists of **PostgreSQL/PostGIS · Redis · FastAPI · Python worker · React/Vite frontend**.

### 2.1 Backend

```powershell
git clone https://github.com/ronny-dev01/DeepSight.git
cd DeepSight

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements-backend.txt
Copy-Item .env.example .env
alembic upgrade head
```

Default development services:

```text
PostgreSQL : localhost:5432
Database   : sonar_mvp
User       : sonar
Password   : sonar

Redis      : redis://localhost:6379/0
```

### 2.2 API

```powershell
uvicorn services.api.main:app --reload --host 127.0.0.1 --port 8000
```

API documentation:

`http://127.0.0.1:8000/docs`

### 2.3 Worker

```powershell
python -m services.worker.worker
```

The worker claims queued jobs, processes them through the detection pipeline, and persists results to the database.

### 2.4 Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend API configuration:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## 3. The dashboard

The React dashboard provides the operational review surface:

* **Sonar ingestion** — submit real SSS imagery for processing.
* **Detection results** — inspect persisted model detections.
* **Evidence** — view supporting detection information.
* **Review queue** — inspect and record human decisions.
* **Geolocation** — display available spatial metadata.
* **Reports** — access structured reporting results.
* **Database-backed state** — results come from persisted backend data, not mock arrays.

---

## 4. The model & pipeline

### 4.1 Model

* **YOLO11n**, configured through the project's model registry.
* Current model: **`ghostvision-crab-pot-custom`**.
* Current version: **`v5-hardneg-epoch9-640-6caf0930`**.
* Current shipped detection class: **`Crab-Pot`**.
* Input size: **640 px**.
* Default device: **CPU**.
* Confidence threshold: **0.25**.
* IoU threshold: **0.45**.
* Model artifact hash verification: **enabled**.
* Tiling is available in the inference configuration but **disabled by default**.

### 4.2 Pipeline

```text
Real SSS imagery
       │
       ▼
  📥 Ingestion
       │
       ▼
  🤖 YOLO Detection
       │
       ▼
  🔎 Evidence Extraction
       │
       ▼
  🔄 Cross-Frame Analysis
       │
       ▼
  📍 Available Geospatial Metadata
       │
       ▼
  👤 Human Review
       │
       ▼
  📄 Structured Reports
```

The worker executes the processing pipeline in-process. Detection results, evidence, review state, and provenance are persisted through the backend.

### 4.3 Detection evidence

Each persisted detection can include:

| Field           | Purpose                                 |
| --------------- | --------------------------------------- |
| 🎯 Confidence   | Model detection confidence              |
| 📦 Bounding box | Detected image region                   |
| 🔎 Evidence     | Supporting acoustic/evidence attributes |
| 🧠 Model        | Model name and version                  |
| 🧬 Provenance   | Model artifact/source information       |
| 🔄 Persistence  | Cross-frame context                     |
| 📍 Geolocation  | Available source metadata               |

If required metadata is unavailable, DeepSight keeps it unavailable rather than generating a value.

### 4.4 Cross-frame analysis

```text
Frame 01 ──► Detection ─┐
Frame 02 ──► Detection ─┤
Frame 03 ──► Detection ─┼──► 🔄 Persistence
Frame 04 ──► Detection ─┘
```

This provides additional context for human review instead of treating every frame as an isolated result.

---

## 5. Model evaluation

### Validation

| Metric    |   Value |
| --------- | ------: |
| Precision | 0.58602 |
| Recall    | 0.50353 |
| mAP@50    | 0.50096 |
| mAP@50–95 | 0.17023 |

### Test

| Metric    |   Value |
| --------- | ------: |
| Images    |     398 |
| Instances |     567 |
| Precision | 0.44775 |
| Recall    | 0.40741 |
| mAP@50    | 0.37390 |
| mAP@50–95 | 0.14874 |

These are recorded evaluation results for the current model/configuration and are not universal performance guarantees.

---

## 6. Technology stack

| Layer               | Technology                               |
| ------------------- | ---------------------------------------- |
| 🎨 Frontend         | React · TypeScript · Vite · Tailwind CSS |
| 🗺️ Maps            | Leaflet · React Leaflet                  |
| ⚡ API               | FastAPI                                  |
| 🐍 Backend          | Python                                   |
| 🗄️ Database        | PostgreSQL · PostGIS                     |
| 🔗 ORM              | SQLAlchemy                               |
| 🔄 Migrations       | Alembic                                  |
| 🔴 Queue            | Redis                                    |
| ⚙️ Worker           | Python                                   |
| 🤖 ML               | YOLO · Ultralytics                       |
| 👁️ Computer Vision | OpenCV                                   |
| 🧪 Testing          | Pytest · Contract Tests                  |
| 🔧 Version Control  | Git · GitHub                             |

---

## 7. API

The FastAPI backend currently exposes:

| Method | Area      | Purpose                     |
| ------ | --------- | --------------------------- |
| `GET`  | `/health` | Service health              |
| `POST` | Ingestion | Create/process sonar jobs   |
| `GET`  | Reviews   | Retrieve review records     |
| `GET`  | Reports   | Retrieve structured reports |

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

---

## 8. Data & model provenance

DeepSight keeps the database as the authoritative application state.

The system records:

* Real source-data information
* Model name/version
* Model artifact information
* Detection results
* Evidence
* Review decisions
* Available spatial metadata

### Non-negotiables

```text
🚫 No mock detections
🚫 No fake coordinates
🚫 No hardcoded result arrays
🚫 No fabricated metrics

🗄️ Database is authoritative
📍 Missing metadata remains unavailable
🧬 Model provenance is recorded
👤 Human review remains part of the workflow
```

---

## 9. Testing

The project includes backend contract tests and frontend validation.

```text
🧪 Contract Tests
      ↓
🗄️ Database / API Validation
      ↓
🎨 Type Check
      ↓
🏗️ Frontend Build
      ↓
🔍 Lint
```

GitHub Actions runs backend contract tests with PostgreSQL/PostGIS.

---

## 10. Current limitations

| Area                 | Current state                                   |
| -------------------- | ----------------------------------------------- |
| 🎯 Detection         | Current trained class is `Crab-Pot`             |
| 📍 Geolocation       | Depends on available source metadata            |
| 💻 Deployment        | Local development only                          |
| 🧠 Model performance | Depends on evaluated data/configuration         |
| 🌊 More classes      | Require additional model development/evaluation |

---

## 11. Roadmap

* 🤖 Expand marine-debris/anomaly classes
* 🔎 Improve evidence extraction
* 🔄 Improve cross-frame association
* 📍 Expand spatial analysis
* 📊 Improve research reporting
* 🧪 Expand datasets and evaluation
* ☁️ Add deployment infrastructure in a future phase

---

## 12. SIH 2026

|                      |                                                                                                          |
| -------------------- | -------------------------------------------------------------------------------------------------------- |
| 🏆 Hackathon         | Smart India Hackathon 2026                                                                               |
| 🆔 Problem Statement | SIH26057                                                                                                 |
| 📌 Title             | AI-Powered Automated Underwater Marine Debris and Anomaly Detection System using Side-Scan Sonar Imagery |
| 🏢 Organization      | Ministry of Earth Sciences (MoES)                                                                        |
| 🔬 Department        | National Institute of Ocean Technology (NIOT)                                                            |

---

## 13. Status

| Component                          | Status                             |
| ---------------------------------- | ---------------------------------- |
| 📥 Sonar ingestion                 | **Functional**                     |
| 🤖 AI detection                    | **Functional**                     |
| 🔎 Evidence pipeline               | **Functional**                     |
| 🔄 Cross-frame analysis            | **Implemented**                    |
| 📍 Metadata-based geolocation      | **Supported when metadata exists** |
| 👤 Review workflow                 | **Functional**                     |
| 📄 Reporting                       | **Implemented**                    |
| 🗄️ PostgreSQL/PostGIS persistence | **Implemented**                    |
| 🎨 React dashboard                 | **Functional**                     |
| ☁️ Public/cloud deployment         | **Not deployed**                   |

---

## 🌊 Vision

**Raw Sonar → AI Detection → Evidence → Persistence → Human Review → Research Record**

DeepSight is being developed to make underwater sonar analysis **structured, explainable, traceable, and reviewable**.
