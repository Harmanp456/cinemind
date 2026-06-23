# 🎬 CineMind — AI-Powered Movie Discovery Platform

CineMind is a modern, high-fidelity movie discovery and recommendation platform. It combines a custom, content-based recommendation engine (computed locally via TF-IDF cosine similarity) with real-time TMDB (The Movie Database) live search and discovery services.

The system is split into:
1. 🖥️ **Streamlit Frontend (`app.py`)**: A premium, responsive dark-themed user interface featuring glassmorphic UI elements, interactive grids, dynamic routing, and tabbed recommendation panels.
2. ⚡ **FastAPI Backend (`main.py`)**: A robust REST API serving real-time TMDB movie statistics, search autocompletion, category-based movie feeds, and similarity recommendations.
3. 📓 **Data Pipeline (`movie.ipynb`)**: A Jupyter notebook that details the cleaning, preparation, and text-vectorization process for a dataset of over 45,000 movies.

---

## 🌟 Key Features

*   🔍 **Interactive Movie Search**: Real-time keyword search with instant autocomplete dropdowns and responsive movie card grids.
*   🤖 **AI Similarity Engine**: Content-based filtering using **TF-IDF Vectorization** and **Cosine Similarity** calculated over merged metadata tags (genres + taglines + overviews).
*   🎭 **Live Genre-Match Recommendations**: Dynamic backend query to TMDB discover services based on the primary genre of the selected movie.
*   📺 **Immersive Media Views**: High-resolution movie posters, rating badges, backdrops, release metadata, and formatted descriptions.
*   🏠 **Curated Home Feed**: Quick-switch lists for Trending, Popular, Top Rated, Now Playing, and Upcoming releases.
*   📈 **Intelligent Caching**: Local caching of TMDB requests to minimize API usage and speed up navigation.

---

## 📁 Repository Structure

```
movierec/
├── app.py                  # Streamlit frontend application & styles
├── main.py                 # FastAPI backend server & API endpoints
├── movie.ipynb             # Jupyter Notebook for data preprocessing & TF-IDF generation
├── movies_metadata.csv     # Raw dataset containing movie stats, budgets, and text metadata
├── requirements.txt        # Python dependency list
├── runtime.txt             # Target python environment runtime
├── .env.example            # Template for TMDB API credentials
│
│   # Pre-computed NLP Pickles (Loaded at Startup by FastAPI)
├── movies.pkl              # Cleaned pandas DataFrame containing title and metadata
├── indices.pkl             # Mapping dictionary from movie title to pandas index
├── tfidf_matrix.pkl        # Compressed sparse row matrix representing TF-IDF vectors
└── tfidf.pkl               # Pickled Scikit-Learn TfidfVectorizer instance
```

---

## 🛠️ Installation & Setup

Follow these steps to run CineMind locally on your machine:

### 1. Prerequisites
Ensure you have **Python 3.10+** installed. You will also need a **TMDB API Key** (v3 auth). You can get one for free by signing up on [The Movie Database (TMDB)](https://www.themoviedb.org/).

### 2. Clone the Repository
Clone the codebase and navigate to the project root directory:
```bash
git clone <repository-url>
cd movierec
```

### 3. Set Up Virtual Environment
Create a clean virtual environment and install the required libraries:

```bash
# Create venv
python -m venv venv

# Activate venv (Windows)
venv\Scripts\activate

# Activate venv (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a file named `.env` in the root directory and add your TMDB API Key:
```env
TMDB_API_KEY=your_tmdb_api_key_here
```

### 5. Launch the FastAPI Backend
Start the FastAPI server using Uvicorn. The backend runs on `http://127.0.0.1:8000` by default:
```bash
uvicorn main:app --reload
```

### 6. Launch the Streamlit Frontend
In a new terminal window (with the virtual environment activated), start the Streamlit application:
```bash
streamlit run app.py
```
Streamlit will automatically open the web app in your default browser at `http://localhost:8501`.

---

## 🔌 API Documentation

FastAPI automatically generates interactive Swagger docs. You can access them at `http://127.0.0.1:8000/docs`.

### Primary Endpoints
*   `GET /health`: Health-check endpoint.
*   `GET /home`: Fetches movie posters for the home feed based on category query (`trending`, `popular`, `top_rated`, `upcoming`, `now_playing`).
*   `GET /tmdb/search`: Queries TMDB for search terms (used for live recommendations/autocomplete).
*   `GET /movie/id/{tmdb_id}`: Returns complete metadata details for a specific movie ID.
*   `GET /movie/search`: The core recommendation bundle. Returns TMDB details, TF-IDF cosine-similarity recommendations, and TMDB genre recommendations for a given query title.
*   `GET /recommend/genre`: Returns live TMDB recommendation cards belonging to the first genre of the provided movie.
*   `GET /recommend/tfidf`: Returns raw TF-IDF similarity recommendations (list of titles and matching scores).

---

## 🧪 Machine Learning Pipeline & Data Preprocessing

The preprocessing details are outlined in `movie.ipynb`:
1. **Deduplication**: Filters out duplicate records inside `movies_metadata.csv`.
2. **Metadata Cleansing**: Replaces null entries and extracts names from JSON-formatted string lists (e.g., parsing genres).
3. **Feature Engineering**: Concatenates `overview`, `genres`, and `tagline` into a single lowercase `tags` text block.
4. **TF-IDF Vectorization**: Uses `TfidfVectorizer(stop_words='english')` to translate the textual data into high-dimensional vector representations.
5. **Serialization**: Pickles the dataframe, vectorizer, and sparse matrices for deployment.

---

## 🎨 Technologies Used

*   **Python**: Core programming language.
*   **FastAPI**: High-performance async web framework for the API layer.
*   **Streamlit**: Fast, reactive front-end styling and rendering.
*   **Scikit-Learn**: Vectorization engine for tf-idf computation.
*   **Pandas & NumPy**: Data processing and matrix operations.
*   **Httpx**: Asynchronous HTTP client for interacting with TMDB APIs.
