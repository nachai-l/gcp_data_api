# 📘 GCP Data API – Student Profile & Taxonomy Service

**FastAPI service for accessing BigQuery-backed e-portfolio data**

---

## 🚀 Overview

This project provides a **data access layer** for e-portfolio generation systems.
It exposes a clean HTTP API to retrieve:

* Student full profiles
* Role taxonomy (roles + required skills)
* Job description (JD) taxonomy
* Template metadata for CV generation

All data is stored in **Google BigQuery**, accessed through repository classes that keep storage details abstracted behind a simple interface.

This service is designed to be deployed on **Google Cloud Run**, but can also run locally.

---

## 🏗️ Project Structure

```
eport_data_api/
├── api.py                         # FastAPI entrypoint
├── config/
│   └── settings.py                # Optional project settings (future use)
├── database/
│   └── bigquery_client.py         # BigQuery client factory
├── functions/
│   └── orchestrator/
│       └── eport_data_gathering_orchestrator.py
├── repositories/
│   ├── student_repo.py            # Student data queries
│   ├── role_repo.py               # Role/JD/template queries
│   └── __init__.py
├── parameters/
│   ├── schemas/                   # Optional schema definitions
│   └── keys/                      # **Ignored** (local keys only)
├── tests/
│   ├── example_input_tables/      # CSVs for loading sample data
│   └── load_csv_files2_bigquery.py# Bulk loader into BigQuery
└── requirements.txt / pyproject.toml
```

---

## ⚙️ Features

### ✔ Student Data Aggregation

`/v1/students/{user_id}/full-profile`
Combines data from:

* student
* education
* experience
* skills
* awards
* extracurriculars
* publications
* training
* references
* additional_info

### ✔ Role Taxonomy

`/v1/roles/{role_id}/taxonomy`
Includes role metadata + required skills.

### ✔ Job Description (JD) Taxonomy

`/v1/jds/{jd_id}/taxonomy`
Includes job title, company, required skills, responsibilities.

### ✔ Template Metadata

`/v1/templates/{template_id}`
Used by the external CV generation engine.

---

## 🛠️ Running Locally

### 1. Install dependencies

```bash
uv sync
```

or

```bash
pip install -r requirements.txt
```

### 2. Export your BigQuery service account key

```
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/key.json"
```

(Your JSON key **must not** be committed — `.gitignore` enforces this.)

### 3. Start FastAPI locally

```bash
uvicorn api:app --reload --port 8001
```

API docs automatically available at:

🔗 [http://localhost:8001/docs](http://localhost:8001/docs)
🔗 [http://localhost:8001/redoc](http://localhost:8001/redoc)

---

## 🧪 Loading Sample Data into BigQuery

Use the included helper script:

```bash
python tests/example_input_tables/load_csv_files2_bigquery.py \
    --project_id YOUR_PROJECT \
    --dataset_id gold_layer \
    --location asia-southeast1
```

Supports autodetection, delimiter detection, BOM-safe header parsing.

---

## 🌐 API Endpoints

### Students

| Method | Endpoint                              | Description             |
| ------ | ------------------------------------- | ----------------------- |
| GET    | `/v1/students/{user_id}/core`         | Raw student row         |
| GET    | `/v1/students/{user_id}/full-profile` | Aggregated full profile |

### Roles

| Method | Endpoint                       | Description            |
| ------ | ------------------------------ | ---------------------- |
| GET    | `/v1/roles/{role_id}/core`     | Raw role data          |
| GET    | `/v1/roles/{role_id}/taxonomy` | Hydrated role taxonomy |

### Job Descriptions

| Method | Endpoint                   | Description          |
| ------ | -------------------------- | -------------------- |
| GET    | `/v1/jds/{jd_id}/core`     | Raw JD data          |
| GET    | `/v1/jds/{jd_id}/taxonomy` | Hydrated JD taxonomy |

### Templates

| Method | Endpoint                      | Description       |
| ------ | ----------------------------- | ----------------- |
| GET    | `/v1/templates/{template_id}` | Template metadata |

---

## 🚫 Security Notes

* **NEVER** commit any files inside `parameters/keys/`
* `.gitignore` explicitly blocks JSON keys
* Use GCP Secret Manager for production deployments
* Enable GitHub **Secret Scanning** for this repository

---

## 🧩 Future Enhancements

* Parallelized BigQuery queries for faster full-profile retrieval
* Stateless caching layer (Cloud Run → Memorystore)
* Pydantic schemas for response typing
* Automated CI/CD to Cloud Run
* Unit tests with BigQuery emulator (optional)

---
