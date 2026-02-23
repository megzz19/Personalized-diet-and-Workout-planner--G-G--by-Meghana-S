# 🏋️ G&G (Goal Getter) — AI-Powered Fitness Planner

A full-stack web application that generates **personalized 7-day diet and workout plans** using machine learning and the **Google Gemini API**. It also features an **AI-powered food image analyzer** that estimates nutritional information from photos.

---

## ✨ Features

- **Personalized Plans** — Generates a tailored 7-day diet + workout plan based on age, weight, height, gender, activity level, dietary preference, and health conditions.
- **AI-Powered (Gemini)** — Uses Google Gemini 2.5 Flash for intelligent, context-aware plan generation with automatic fallback to a heuristic KNN-based engine.
- **Food Image Analysis** — Upload a food photo and get instant nutritional breakdown, health rating, and healthier alternatives.
- **PDF Download** — Export your generated fitness plan as a PDF.

---

## 📁 Project Structure

```
brownie/
├── main.py                   # FastAPI application & API endpoints
├── gemini_service.py         # Google Gemini API integration
├── recommendation_engine.py  # KNN-based recommendation engine (fallback)
├── models.py                 # Pydantic data models & validation
├── verify_model.py           # Model verification script
├── verify_api.py             # API verification script
├── .env                      # Environment variables (API keys — not committed)
├── dataset/
│   ├── final_nutrition.csv   # Nutrition dataset
│   └── final_workouts.csv    # Workouts dataset
├── model_artifacts/          # Trained ML model files (.pkl)
├── frontend/
│   ├── index.html            # Home page
│   ├── results.html          # Results display page
│   ├── food_analysis.html    # Food image analysis page
│   ├── style.css             # Stylesheet
│   └── script.js             # Frontend logic
└── README.md
```

---

## 🛠️ Requirements

- **Python 3.9+**
- A **Google Gemini API Key** (free tier available at [Google AI Studio](https://aistudio.google.com/))

### Python Dependencies

| Package | Purpose |
|---|---|
| `fastapi` | Web framework for the REST API |
| `uvicorn` | ASGI server to run FastAPI |
| `python-dotenv` | Loads environment variables from `.env` |
| `google-generativeai` | Google Gemini API SDK |
| `pandas` | Data manipulation & analysis |
| `numpy` | Numerical computing |
| `scikit-learn` | KNN models for recommendations |
| `joblib` | Model serialization (save/load `.pkl`) |
| `pydantic` | Data validation & models |
| `Pillow` | Image processing for food analysis |
| `python-multipart` | File upload support for FastAPI |

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/brownie.git
cd brownie
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

**Activate it:**

- **Windows:**
  ```bash
  .venv\Scripts\activate
  ```
- **macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```

### 3. Install Dependencies

```bash
pip install fastapi uvicorn python-dotenv google-generativeai pandas numpy scikit-learn joblib pydantic Pillow python-multipart
```

### 4. Configure Your API Key

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## ▶️ Running the Application

### Start the Backend Server

```bash
python main.py
```

The API will be available at **`http://127.0.0.1:8000`**.

### Open the Frontend

Open `frontend/index.html` in your browser, or serve it using a local development server (e.g., VS Code Live Server on port `5500`).

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/generate-plan` | Generates a personalized 7-day fitness & diet plan |
| `POST` | `/analyze-food` | Analyzes an uploaded food image for nutritional info |

---

This is a Capston Project
