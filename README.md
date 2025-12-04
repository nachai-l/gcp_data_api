# 📘 GCP Data API – Student Profile & Taxonomy Service

**FastAPI + BigQuery service powering the E-Portfolio (CV) Generation System**

---

## 🚀 Overview

This service provides the **data access layer** for the CV Generation pipeline.
It exposes a clean HTTP API to retrieve:

* **Student full profiles** (single nested BigQuery query)
* **Role taxonomy** (roles + required skills)
* **Job Description (JD) taxonomy**
* **Template metadata** for CV generation

The API runs on **Google Cloud Run**, and all data is stored in **Google BigQuery**.

---

## 🏗️ Architecture Highlights

### 🔹 Optimized student profile query

`/full-profile` now uses **one ARRAY-aggregated BigQuery query**, collapsing 10+ queries into one, improving latency from:

> **~80 seconds → ~2–3 seconds**

### 🔹 Async-ready

Compatible with:

* `httpx.AsyncClient`
* `asyncio.gather`
* Cloud Run → Cloud Run internal calls

---

## 🧱 Project Structure

```
eport_data_api/
├── api.py                         # FastAPI entrypoint
├── config/settings.py             # Loads GCP project/dataset/location
├── database/bigquery_client.py    # BigQuery client wrapper
├── functions/orchestrator/
│   └── eport_data_gathering_orchestrator.py
├── repositories/
│   ├── student_repo.py            # Nested aggregated student query
│   ├── role_repo.py               # Role/JD/template queries
│   └── __init__.py
├── parameters/
│   ├── schemas/
│   └── keys/                      # Ignored (local dev only)
├── tests/
│   ├── example_input_tables/
│   └── load_csv_files2_bigquery.py
└── requirements.txt
```

---

## ⚙️ Features

### ✔ Single-query full student profile

Gracefully handles missing linked tables (returns empty arrays).

### ✔ Role taxonomy

Includes required skills with proficiency levels.

### ✔ JD taxonomy

Includes skills + ordered responsibilities.

### ✔ Template metadata

Used by the CV generator.

---

## 🛠 Running Locally

### 1. Install dependencies

```bash
uv sync
```

Or:

```bash
pip install -r requirements.txt
```

### 2. Authenticate using a local service account

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/local/key.json"
```

### 3. Start API locally

```bash
uvicorn api:app --reload --port 8001
```

Open:

* [http://localhost:8001/docs](http://localhost:8001/docs)
* [http://localhost:8001/redoc](http://localhost:8001/redoc)

---

## 🔽 Load Sample Data Into BigQuery

```bash
python tests/example_input_tables/load_csv_files2_bigquery.py \
  --project_id YOUR_PROJECT \
  --dataset_id gold_layer \
  --location asia-southeast1
```

---

## 🌐 API Endpoints

### Students

| Method | Endpoint                              | Description             |
| ------ | ------------------------------------- | ----------------------- |
| GET    | `/v1/students/{user_id}/core`         | Raw student record      |
| GET    | `/v1/students/{user_id}/full-profile` | Aggregated full profile |

### Roles

| Method | Endpoint                       | Description            |
| ------ | ------------------------------ | ---------------------- |
| GET    | `/v1/roles/{role_id}/core`     | Raw role record        |
| GET    | `/v1/roles/{role_id}/taxonomy` | Hydrated role taxonomy |

### JDs

| Method | Endpoint                   | Description          |
| ------ | -------------------------- | -------------------- |
| GET    | `/v1/jds/{jd_id}/core`     | Raw JD record        |
| GET    | `/v1/jds/{jd_id}/taxonomy` | Hydrated JD taxonomy |

### Templates

| Method | Endpoint                      | Description          |
| ------ | ----------------------------- | -------------------- |
| GET    | `/v1/templates/{template_id}` | CV template metadata |

---

# ☁️ **Deploying to Google Cloud Run**

## 1️⃣ Build container with Cloud Build

```bash
gcloud builds submit \
  --tag "REGION-docker.pkg.dev/PROJECT_ID/eport-data-api/service"
```

Examples (masked):

```bash
REGION="asia-southeast1"
PROJECT_ID="your-gcp-project"
REPO="eport-data-api"
IMAGE_NAME="service"
```

---

## 2️⃣ Create Cloud Run service account (optional but recommended)

```bash
gcloud iam service-accounts create eport-data-api-sa \
  --description="Data API service account" \
  --display-name="Eport Data API SA"
```

Grant required roles:

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:eport-data-api-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:eport-data-api-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

(Cloud Run automatically handles token exchange → **no JSON key needed** in production.)

---

## 3️⃣ Deploy to Cloud Run

```bash
gcloud run deploy eport-data-api \
  --image "REGION-docker.pkg.dev/PROJECT_ID/eport-data-api/service" \
  --region "asia-southeast1" \
  --platform managed \
  --allow-unauthenticated \
  --service-account "eport-data-api-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --set-env-vars \
      GCP_PROJECT_ID="PROJECT_ID",\
      BQ_DATASET="gold_layer",\
      BQ_LOCATION="asia-southeast1"
```

Cloud Run will return a URL like:

```
https://eport-data-api-XXXXXX-REGION.run.app
```

---

## 🔒 Security Notes

* Do **not** store service account keys in the repo
* Use Cloud Run identity instead of JSON keys in production
* Keep `parameters/keys/` ignored
* Enable GitHub secret scanning
* Use IAM least-privilege roles only

---

## 🧩 Future Enhancements

* Full async BigQuery client
* Redis/Memorystore caching
* Strong Pydantic response schemas
* Automated CI/CD to Cloud Run
* OpenAPI export to Artifact Registry

---
