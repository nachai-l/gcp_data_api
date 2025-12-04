# 📘 GCP Data API – Student Profile & Taxonomy Service

**FastAPI + BigQuery service powering the E-Portfolio (CV) Generation System**

---

## 🚀 Overview

This service provides the **data access layer** for the CV Generation pipeline.
It exposes a clean HTTP API to retrieve:

* **Student full profiles** (nested query, 1 BigQuery call)
* **Role taxonomy** (roles + required skills)
* **Job Description (JD) taxonomy**
* **Template metadata** used by the CV generator

All data lives in **Google BigQuery**.
The API is deployed on **Google Cloud Run** (fully serverless, autoscaling).

---

## 🏗️ Updated Architecture Highlights

### 🔹 **Single nested BigQuery query for `/full-profile`**

Replaced 10 sequential BigQuery queries with **one array-aggregated query**:

* `student`
* `education`
* `experience`
* `skills`
* `awards`
* `extracurriculars`
* `publications`
* `training`
* `references`
* `additional_info`

This reduces latency from **~80 seconds → ~2–3 seconds**.

### 🔹 **Async endpoints ready for Orchestrator parallelization**

The Data API is fully compatible with:

* `httpx.AsyncClient`
* `asyncio.gather`
* Cloud-Run-to-Cloud-Run calls

---

## 🧱 Project Structure

```
eport_data_api/
├── api.py                         # FastAPI entrypoint (async)
├── config/
│   └── settings.py                # Reads env vars (project, dataset, region)
├── database/
│   └── bigquery_client.py         # BigQuery client wrapper (sync)
├── functions/
│   └── orchestrator/
│       └── eport_data_gathering_orchestrator.py  # Hydration logic
├── repositories/
│   ├── student_repo.py            # Nested full-profile BigQuery query
│   ├── role_repo.py               # Role/JD/template queries
│   └── __init__.py
├── parameters/
│   ├── schemas/                   # Optional schema definitions
│   └── keys/                      # (ignored)
├── tests/
│   ├── example_input_tables/      
│   └── load_csv_files2_bigquery.py# Bulk CSV → BigQuery loader
└── requirements.txt
```

---

## ⚙️ Features

### ✔ **Fast Student Full-Profile Aggregation**

`/v1/students/{user_id}/full-profile`

Powered by a single BigQuery query with `ARRAY(SELECT AS STRUCT ...)`
Handles missing tables gracefully (returns empty lists).

### ✔ **Role Taxonomy**

`/v1/roles/{role_id}/taxonomy`

Includes:

* Role metadata
* Required skills (ordered)

### ✔ **JD Taxonomy**

`/v1/jds/{jd_id}/taxonomy`

Includes:

* Job metadata
* Required skills
* Responsibilities

### ✔ **Template Metadata**

`/v1/templates/{template_id}`

Used by the CV Generation Orchestrator.

---

## 🛠️ Running Locally

### 1. Install dependencies

```bash
uv sync
```

or:

```bash
pip install -r requirements.txt
```

### 2. Authenticate via GCP service account

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
```

### 3. Run FastAPI

```bash
uvicorn api:app --reload --port 8001
```

Open docs:

* [http://localhost:8001/docs](http://localhost:8001/docs)
* [http://localhost:8001/redoc](http://localhost:8001/redoc)

---

## 🔽 Loading Sample Data Into BigQuery

Use included loader:

```bash
python tests/example_input_tables/load_csv_files2_bigquery.py \
    --project_id YOUR_PROJECT \
    --dataset_id gold_layer \
    --location asia-southeast1
```

Supports schema autodetect + BOM-safe CSV headers.

---

## 🌐 API Endpoints

### Students

| Method | Endpoint                              | Description           |
| ------ | ------------------------------------- | --------------------- |
| GET    | `/v1/students/{user_id}/core`         | Raw student row       |
| GET    | `/v1/students/{user_id}/full-profile` | Hydrated full profile |

### Roles

| Method | Endpoint                       | Description     |
| ------ | ------------------------------ | --------------- |
| GET    | `/v1/roles/{role_id}/core`     | Raw role record |
| GET    | `/v1/roles/{role_id}/taxonomy` | Role + skills   |

### JDs

| Method | Endpoint                   | Description         |
| ------ | -------------------------- | ------------------- |
| GET    | `/v1/jds/{jd_id}/core`     | Raw JD record       |
| GET    | `/v1/jds/{jd_id}/taxonomy` | JD + skills + tasks |

### Templates

| Method | Endpoint                      | Description   |
| ------ | ----------------------------- | ------------- |
| GET    | `/v1/templates/{template_id}` | Template info |

---

## ☁️ Deploying to Cloud Run

### Build with Cloud Build

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/eport-data-api
```

### Deploy

```bash
gcloud run deploy eport-data-api \
  --image gcr.io/PROJECT_ID/eport-data-api \
  --region asia-southeast1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=...,BQ_DATASET=gold_layer,BQ_LOCATION=asia-southeast1 \
  --service-account=YOUR_SERVICE_ACCOUNT
```

---

## 🔒 Security Notes

* Never commit keys in `parameters/keys/`
* Use **GCP Secret Manager** for production secrets
* Cloud Run uses service account identity → no JSON keys needed in production
* Enable GitHub Secret Scanning

---

## 🧩 Future Enhancements

* Add `async BigQuery client` for fully async repo layer
* Add Redis/Memorystore caching
* Publish OpenAPI schema to Artifact Registry
* Add Cloud Build CI/CD pipeline
* Add response Pydantic models

---
