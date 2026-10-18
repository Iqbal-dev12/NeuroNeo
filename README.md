# EthiCare — AI-Based Neonatal Facial Expression Pain Detection System

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/Frontend-React%2019-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![TensorFlow / Keras 3](https://img.shields.io/badge/Deep%20Learning-Keras%203-FF6F00.svg?style=flat&logo=tensorflow)](https://keras.io)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com)

EthiCare is an end-to-end medical AI application engineered to detect, classify, and track neonatal pain in real time using facial expression analysis. Built for Neonatal Intensive Care Units (NICUs), the platform bridges deep learning computer vision with an intuitive clinical dashboard to assist doctors and nurses in early pain diagnosis and intervention.

---

## 🏛️ System Architecture

```text
                               +-----------------------------+
                               |     Video / Image Feed      |
                               +--------------+--------------+
                                              |
                                              v
                              +---------------+---------------+
                              |    Face Detection Engine      |
                              |  (MediaPipe / Haar Cascades)  |
                              +---------------+---------------+
                                              |
                                              v
                              +---------------+---------------+
                              |  Temporal Sequence Extractor  |
                              |   (16 Normalized ROI Frames)  |
                              +---------------+---------------+
                                              |
                                              v
                              +---------------+---------------+
                              |     CNN-LSTM Architecture     |
                              |   - MobileNetV2 Backbone      |
                              |   - Temporal LSTM Layer       |
                              +---------------+---------------+
                                              |
                                              v
             +--------------------------------+--------------------------------+
             |                                                                 |
             v                                                                 v
+------------------------+                                      +------------------------+
|   Clinical Diagnosis   |                                      |   Automated Alerting   |
| - Severe Pain (≥70%)   |                                      | - Triggers Alert for   |
| - Moderate Pain (45%)  |                                      |   Severe Pain cases    |
| - Mild Pain (20%)      |                                      | - Database Logging     |
| - No Pain / Rest (<20%)|                                      +------------------------+
+------------------------+
```

---

## 📁 Repository Structure

```text
ETHICARE HACKATHON/
│
├── backend/                       # FastAPI application & AI inference pipeline
│   ├── app/                       # Modular application code
│   │   ├── constants/             # Clinical thresholds & pain mappings
│   │   ├── database/              # SQLAlchemy engine, session & connection pooling
│   │   ├── routes/                # REST endpoints (/api/pain/predict, /history, /alerts)
│   │   ├── schemas/               # Pydantic validation schemas
│   │   ├── services/              # ML inference (prediction_service.py, face_detection.py)
│   │   └── utils/                 # Image processing & file utilities
│   ├── model/                     # Trained CNN-LSTM weights (pain_video_model.keras)
│   ├── training/                  # Model training pipeline (train_model.py)
│   ├── main.py                    # FastAPI server entrypoint
│   ├── auth.py                    # JWT authentication & bcrypt security
│   ├── database.py                # Database connector with environment fallback
│   ├── models.py & schemas.py     # User auth ORM models and schemas
│   ├── schema.sql                 # MySQL relational schema definition
│   └── requirements.txt           # Python dependency manifest
│
├── frontend/                      # React 19 + Vite clinical web application
│   ├── src/                       # Components & page views
│   │   ├── components/            # Navbar, Landmark Canvas, Hero, UI cards
│   │   ├── context/               # Authentication & session context
│   │   └── pages/                 # Analyze, History (latest 5), Reports (PDF), Alerts
│   ├── public/                    # Static branding & assets
│   ├── package.json               # NPM package manifest
│   └── vite.config.js             # Vite configuration
│
├── demo_samples/                  # Pre-packaged evaluation videos for testing
│   ├── S001_Pain_1_[0]_20s.mp4    # Pain expression sample (triggers Severe Pain diagnosis)
│   └── S001_Rest_1_[0]_20s.mp4    # Rest / baseline sample (triggers No Pain diagnosis)
│
├── uploads/                       # Server upload staging directory
└── README.md                      # Documentation
```

---

## ⚡ Quickstart Guide

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 18+** & npm
- **MySQL Server** (listening on localhost:3306)

---

### 2. Backend Setup
1. Open terminal and navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables (optional; defaults to `root`/`root`):
   ```bash
   export MYSQL_USER="root"
   export MYSQL_PASSWORD="your_password"
   export MYSQL_DB="neonatal_auth"
   ```
4. Start the FastAPI server:
   ```bash
   py -3.11 -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```
   * Swagger Documentation: **http://127.0.0.1:8000/docs**

---

### 3. Frontend Setup
1. In a second terminal, navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   * Web Application: **http://localhost:5173**

---

## 🧪 Testing with Sample Videos

Two sample videos are included in `demo_samples/` to evaluate the model immediately:

1. Open **[http://localhost:5173/analyze](http://localhost:5173/analyze)**.
2. Enter an Infant ID (e.g. `INF001`).
3. Upload **`demo_samples/S001_Pain_1_[0]_20s.mp4`**:
   - **Diagnosis**: `Severe Pain`
   - **Score**: ~88.7%
   - **Action**: Triggers an automated alert.
4. Upload **`demo_samples/S001_Rest_1_[0]_20s.mp4`**:
   - **Diagnosis**: `No Pain`
   - **Score**: ~8.5%
   - **Action**: Confirms baseline resting state.

---

## 📊 Core Features

* **Real-Time Facial Expression Classification**: MobileNetV2 spatial extraction combined with LSTM temporal sequence learning.
* **Automated Clinical Alerting**: Flagging critical thresholds directly into clinical staff alerts.
* **Patient History & PDF Reporting**: Historical scan tracking (capped at latest 5 findings) with client-side PDF export (`jspdf-autotable`).
* **JWT Protected Authentication**: Secure role-based doctor/nurse access.
