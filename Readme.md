# AdServe — Privacy-First On-Device Ad Targeting Platform

AdServe is a three-tier ad targeting system built on a core privacy principle:
all ML inference runs on the user's device. Raw browsing data never leaves the
user's machine — only derived interest signals travel to the ad server.

> This is a Proof of Concept. The LLM classifier currently uses the HuggingFace
> Inference API and will be replaced with an on-prem model (Ollama + Phi-3 Mini)
> in production.

---

## How It Works

1. User selects a browser profile in the dashboard
2. Client Service reads Chrome history locally and runs it through a 5-level classification cascade entirely on the user's machine
3. Only 4 derived interest signals leave the device — no raw URLs, no queries
4. Ad Server scores all ads against those signals using a weighted engine
5. Ranked ads are returned and displayed in the dashboard

---

## Project Structure

```
adserve/
├── Client/          ← On-device ML pipeline (FastAPI, Port 8000)
├── Server/          ← Ad matching engine (FastAPI, Port 8001)
├── adserve-platform/         ← React dashboard (Vite, Port 3000) 
```

---

## Tech Stack

### Client Service — Port 8000

| Layer         | Technology                               |
| ------------- | ---------------------------------------- |
| API Framework | FastAPI                                  |
| ML Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| ML Classifier | scikit-learn (SVM)                       |
| Vector Store  | ChromaDB                                 |
| LLM (POC)     | HuggingFace Inference API                |
| Settings      | pydantic-settings                        |
| Runtime       | Python 3.10+                             |

### Ad Server — Port 8001

| Layer         | Technology           |
| ------------- | -------------------- |
| API Framework | FastAPI              |
| ORM           | SQLAlchemy 2.0       |
| Database      | SQLite (adserver.db) |
| Schemas       | Pydantic v2          |
| HTTP Client   | httpx                |
| Settings      | pydantic-settings    |
| Runtime       | Python 3.10+         |

### Frontend — Port 3000

| Layer        | Technology            |
| ------------ | --------------------- |
| Framework    | React 18 + TypeScript |
| Build Tool   | Vite                  |
| Global State | Zustand               |
| Server State | TanStack React Query  |
| Forms        | react-hook-form + zod |
| Charts       | Recharts              |
| Animations   | framer-motion         |
| HTTP Client  | axios                 |
| Styling      | Tailwind CSS          |

---

## Prerequisites

* Python 3.10 or higher
* Node.js 18 or higher
* npm 9 or higher
* Google Chrome
* HuggingFace API token

---

## Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/adserve.git
cd adserve
```

### 2. Client Service Setup

```bash
cd Client

python -m venv venv

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
```

Open `Client/.env` and fill in:

```env
HF_API_TOKEN=your_huggingface_token_here
```

### 3. Ad Server Setup

```bash
cd Server

python -m venv venv

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
```

Open `Server/.env` and fill in:

```env
HF_API_TOKEN=your_huggingface_token_here
DATABASE_URL=sqlite:///./adserver.db
CORS_ORIGINS=["http://localhost:3000"]
```

### 4. Frontend Setup

```bash
cd ad_copy
npm install
```

---

## Running the Application

Open three separate terminals and run each service simultaneously.

### Terminal 1 — Client Service

```bash
cd Client

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

python scripts/run_api.py
```

Client Service runs at `http://localhost:8000`

### Terminal 2 — Ad Server

```bash
cd Server

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

python scripts/run_server.py
```

Ad Server runs at `http://localhost:8001`

### Terminal 3 — Frontend

```bash
cd ad_copy
npm run dev
```

Dashboard runs at `http://localhost:3000`

---

## Using the Dashboard

**Demo Page** — Test ad targeting

1. Go to `http://localhost:3000`
2. Click Demo in the navigation
3. Enter your Chrome profile path
4. Click Run Pipeline — Client Service reads your browser history,
   classifies queries locally, and returns interest signals
5. Ads ranked by relevance score will appear

**Ads Manager** — Manage ad inventory

1. Click Ads in the navigation
2. Create, edit, or delete ads
3. Use the AI Generate button to auto-generate categories and keywords
4. Upload ad images directly or provide an image URL

**Analytics** — View performance

1. Click Analytics in the navigation
2. View impressions, clicks, and CTR across all ads

---

## The 5-Level Classification Cascade

Every search query is classified locally on the user's device through this
cascade. Each level only activates if the level above misses:

```
Query
  │
  ├── L0: ML Binary Filter (SVM + SentenceTransformer)
  │       product=1 → continue | non-product=0 → discard
  │
  ├── L1a: ChromaDB Exact Hash Lookup
  │       HIT → return cached classification
  │
  ├── L1b: ChromaDB Semantic Search (cosine similarity >= 0.85)
  │       HIT → return nearest classification
  │
  ├── L2: User Data Store (user_data.json)
  │       HIT → return hand-curated classification
  │
  ├── L3: Training Data Store (training_data.json)
  │       HIT → return static classification
  │
  └── L4: LLM Classifier (on-prem target / HuggingFace in POC)
          → classify → write result back to ChromaDB
          → future identical queries hit L1a instead
```

---

## The 4 Interest Signals

These are the only values that leave the user's device:

| Signal | Method                                 | What it captures          |
| ------ | -------------------------------------- | ------------------------- |
| top_1  | max(timestamp)                         | Most recent product query |
| top_2  | sum(engagement) by brand/product/model | Most searched product     |
| top_3  | sum(engagement) by category/product    | Dominant subcategory      |
| top_4  | sum(engagement) by category            | Broadest interest area    |

---

## Ad Scoring Formula

```
Final Score = (Category Score × 0.45)
            + (Keyword Score  × 0.35)
            + (Brand Score    × 0.20)
```

| Component | Match Type            | Score      |
| --------- | --------------------- | ---------- |
| Category  | Exact                 | 1.0        |
| Category  | Substring             | 0.6        |
| Brand     | Exact                 | 1.0        |
| Brand     | Substring             | 0.3        |
| Keyword   | Jaccard overlap ratio | 0.0 – 1.0 |

Ads scoring below 0.05 are not served. When top_1 and top_2 match the same
product, a 2.5x CPM premium is applied as a purchase intent signal.

---

## Managing the Vector Database

```bash
cd Client

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

python manage_vectordb.py
```

---

## Environment Variables

### Client/.env

| Variable     | Description                                  |
| ------------ | -------------------------------------------- |
| HF_API_TOKEN | HuggingFace API token for LLM classification |

### Server/.env

| Variable     | Description                                     |
| ------------ | ----------------------------------------------- |
| HF_API_TOKEN | HuggingFace API token for ad keyword generation |
| DATABASE_URL | SQLite connection string                        |
| CORS_ORIGINS | Allowed origins for CORS                        |

---

## License

MIT
