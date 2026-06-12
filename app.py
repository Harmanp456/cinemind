import requests
import streamlit as st

# Backward compatibility for st.image(use_container_width=True) in older Streamlit versions
_orig_image = st.image
def compatible_image(image, *args, **kwargs):
    if "use_container_width" in kwargs:
        try:
            return _orig_image(image, *args, **kwargs)
        except TypeError:
            kwargs.pop("use_container_width", None)
            kwargs["use_column_width"] = True
            return _orig_image(image, *args, **kwargs)
    return _orig_image(image, *args, **kwargs)
st.image = compatible_image

# =============================
# CONFIG
# =============================
API_BASE = "https://cinemind-faec.onrender.com" or "http://127.0.0.1:8000"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(page_title="Movie Recommender", page_icon="🎬", layout="wide")

# =============================
# STYLES (minimal modern)
# =============================
st.markdown("""
<style>

/* ---------- GLOBAL ---------- */

.stApp{
    background:#0B1120;
    color:white;
}

.block-container{
    max-width:1600px;
    padding-top:1rem;
    padding-bottom:2rem;
}

/* Hide Streamlit UI */

#MainMenu{
    visibility:hidden;
}

footer{
    visibility:hidden;
}

header{
    visibility:hidden;
}

[data-testid="stSidebar"]{
    display:none;
}

[data-testid="collapsedControl"]{
    display:none;
}

/* ---------- HERO ---------- */

.hero{
    background:
    linear-gradient(
    135deg,
    #0f172a,
    #1e293b,
    #111827
    );

    padding:50px;
    border-radius:30px;
    margin-bottom:30px;
}

.hero-title{
    font-size:3rem;
    font-weight:800;
    color:white;
}

.hero-sub{
    color:#cbd5e1;
    font-size:1.1rem;
}

/* ---------- CARDS ---------- */

.movie-title{
    color:white;
    font-size:.9rem;
    font-weight:600;
    text-align:center;
    min-height:48px;
    padding-top:8px;
}

div[data-testid="stImage"] img{
    border-radius:18px;
    transition:.3s;
}

div[data-testid="stImage"] img:hover{
    transform:scale(1.03);
}

.small-muted{
    color:#94a3b8;
}

.card{
    background:#111827;
    border-radius:20px;
    padding:20px;
}

/* ---------- Button theming (Back to Home) ---------- */
/* Streamlit renders buttons with data-baseweb attr. We target the one in details view by label/key. */
button[data-testid="stButton"]{
    /* keep defaults for all buttons */
}

/* Back to Home button on details page */
div[data-testid="stHorizontalBlock"] button[data-testid="stButton'][aria-label*="Back to Home"]{
    background-color: #2563EB !important; /* blue */
    color: white !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
}

div[data-testid="stHorizontalBlock"] button[data-testid="stButton'][aria-label*="Back to Home"]:hover{
    background-color: #1D4ED8 !important;
    color: white !important;
}

</style>
""", unsafe_allow_html=True)




# =============================
# STATE + ROUTING (single-file pages)
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"  # home | details
if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None

qp_view = st.query_params.get("view")
qp_id = st.query_params.get("id")
if qp_view in ("home", "details"):
    st.session_state.view = qp_view
if qp_id:
    try:
        st.session_state.selected_tmdb_id = int(qp_id)
        st.session_state.view = "details"
    except:
        pass


def goto_home():
    st.session_state.view = "home"
    st.query_params["view"] = "home"
    if "id" in st.query_params:
        del st.query_params["id"]
    st.rerun()


def goto_details(tmdb_id: int):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = int(tmdb_id)
    st.query_params["view"] = "details"
    st.query_params["id"] = str(int(tmdb_id))
    st.rerun()


# =============================
# API HELPERS
# =============================
@st.cache_data(ttl=30)  # short cache for autocomplete
def api_get_json(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=25)
        if r.status_code >= 400:
            return None, f"HTTP {r.status_code}: {r.text[:300]}"
        return r.json(), None
    except Exception as e:
        return None, f"Request failed: {e}"


def poster_grid(cards, cols=6, key_prefix="grid"):
    if not cards:
        st.info("No movies to show.")
        return

    rows = (len(cards) + cols - 1) // cols
    idx = 0
    for r in range(rows):
        colset = st.columns(cols)
        for c in range(cols):
            if idx >= len(cards):
                break
            m = cards[idx]
            idx += 1

            tmdb_id = m.get("tmdb_id")
            title = m.get("title", "Untitled")
            poster = m.get("poster_url")

            with colset[c]:
                if isinstance(poster, str) and poster.strip().startswith(("http://", "https://", "data:")):
                    st.image(poster, use_container_width=True)
                else:
                    st.write("🖼️ No poster")

                if st.button(
                    "🎬 View",
                    key=f"{key_prefix}_{r}_{c}_{idx}_{tmdb_id}",
                    use_container_width=True,
                ):
                    if tmdb_id:
                        goto_details(tmdb_id)

                st.markdown(
                    f"""
                    <div class=\"movie-title\">
                    {title}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )



def to_cards_from_tfidf_items(tfidf_items):
    cards = []
    for x in tfidf_items or []:
        tmdb = x.get("tmdb") or {}
        if tmdb.get("tmdb_id"):
            cards.append(
                {
                    "tmdb_id": tmdb["tmdb_id"],
                    "title": tmdb.get("title") or x.get("title") or "Untitled",
                    "poster_url": tmdb.get("poster_url"),
                }
            )
    return cards


# =============================
# IMPORTANT: Robust TMDB search parsing
# Supports BOTH API shapes:
# 1) raw TMDB: {"results":[{id,title,poster_path,...}]}
# 2) list cards: [{tmdb_id,title,poster_url,...}]
# =============================
def parse_tmdb_search_to_cards(data, keyword: str, limit: int = 24):
    """
    Returns:
      suggestions: list[(label, tmdb_id)]
      cards: list[{tmdb_id,title,poster_url}]
    """
    keyword_l = keyword.strip().lower()

    # A) If API returns dict with 'results'
    if isinstance(data, dict) and "results" in data:
        raw = data.get("results") or []
        raw_items = []
        for m in raw:
            title = (m.get("title") or "").strip()
            tmdb_id = m.get("id")
            poster_path = m.get("poster_path")
            if not title or not tmdb_id:
                continue
            raw_items.append(
                {
                    "tmdb_id": int(tmdb_id),
                    "title": title,
                    "poster_url": f"{TMDB_IMG}{poster_path}" if poster_path else None,
                    "release_date": m.get("release_date", ""),
                }
            )

    # B) If API returns already as list
    elif isinstance(data, list):
        raw_items = []
        for m in data:
            # might be {tmdb_id,title,poster_url}
            tmdb_id = m.get("tmdb_id") or m.get("id")
            title = (m.get("title") or "").strip()
            poster_url = m.get("poster_url")
            if not title or not tmdb_id:
                continue
            raw_items.append(
                {
                    "tmdb_id": int(tmdb_id),
                    "title": title,
                    "poster_url": poster_url,
                    "release_date": m.get("release_date", ""),
                }
            )
    else:
        return [], []

    # Word-match filtering (contains)
    matched = [x for x in raw_items if keyword_l in x["title"].lower()]

    # If nothing matched, fallback to raw list (so never blank)
    final_list = matched if matched else raw_items

    # Suggestions = top 10 labels
    suggestions = []
    for x in final_list[:10]:
        year = (x.get("release_date") or "")[:4]
        label = f"{x['title']} ({year})" if year else x["title"]
        suggestions.append((label, x["tmdb_id"]))

    # Cards = top N
    cards = [
        {"tmdb_id": x["tmdb_id"], "title": x["title"], "poster_url": x["poster_url"]}
        for x in final_list[:limit]
    ]
    return suggestions, cards


# =============================
# SIDEBAR (removed)
# =============================
home_category = "trending"
grid_cols = 6


# =============================
# HEADER
# =============================
st.markdown("""
<div class="hero">

<div class="hero-title">
🎬 CineMind
</div>

<div class="hero-sub">
AI Powered Movie Discovery Platform
<br>
Search • Explore • Discover
</div>

</div>
""", unsafe_allow_html=True)
st.divider()


# ==========================================================
# VIEW: HOME
# ==========================================================
if st.session_state.view == "home":
    typed = st.text_input(
        label="Search movies",
        label_visibility="collapsed",
        placeholder="🔍 Search movies, actors, genres..."
    )


    st.divider()

    # SEARCH MODE (Autocomplete + word-match results)
    if typed.strip():
        if len(typed.strip()) < 2:
            st.caption("Type at least 2 characters for suggestions.")
        else:
            data, err = api_get_json("/tmdb/search", params={"query": typed.strip()})

            if err or data is None:
                st.error(f"Search failed: {err}")
            else:
                suggestions, cards = parse_tmdb_search_to_cards(
                    data, typed.strip(), limit=24
                )

                # Dropdown
                if suggestions:
                    labels = ["-- Select a movie --"] + [s[0] for s in suggestions]
                    selected = st.selectbox("Suggestions", labels, index=0)

                    if selected != "-- Select a movie --":
                        # map label -> id
                        label_to_id = {s[0]: s[1] for s in suggestions}
                        goto_details(label_to_id[selected])
                else:
                    st.info("No suggestions found. Try another keyword.")

                st.markdown("### Results")
                poster_grid(cards, cols=grid_cols, key_prefix="search_results")

        st.stop()

    # HOME FEED MODE
    st.markdown(f"### 🏠 Home — {home_category.replace('_',' ').title()}")

    home_cards, err = api_get_json(
        "/home", params={"category": home_category, "limit": 24}
    )
    if err or not home_cards:
        st.error(f"Home feed failed: {err or 'Unknown error'}")
        st.stop()

    poster_grid(home_cards, cols=grid_cols, key_prefix="home_feed")

# ==========================================================
# VIEW: DETAILS
# ==========================================================
elif st.session_state.view == "details":
    tmdb_id = st.session_state.selected_tmdb_id
    if not tmdb_id:
        st.warning("No movie selected.")
        if st.button("← Back to Home"):
            goto_home()
        st.stop()

    # Top bar
    left, right = st.columns([8, 2])

    with left:
        st.markdown("### 📄 Movie Details")

    with right:
        # Put the button in the right column and make it take available width,
        # so it visually flushes to the far right.
        st.markdown(
            """
            <div class='card' style='display:flex; justify-content:flex-end;'>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "← Back to Home",
            key="back_to_home_details",
            type="primary",
            use_container_width=True,
        ):
            goto_home()

        st.markdown("</div>", unsafe_allow_html=True)




    # Details (your FastAPI safe route)
    data, err = api_get_json(f"/movie/id/{tmdb_id}")
    if err or not data:
        st.error(f"Could not load details: {err or 'Unknown error'}")
        st.stop()




    # Layout: Poster LEFT, Details RIGHT
    left, right = st.columns([1, 2.4], gap="large")

    with left:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        if data.get("poster_url"):
            st.image(data["poster_url"], use_container_width=True)
        else:
            st.write("🖼️ No poster")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"## {data.get('title','')}")
        release = data.get("release_date") or "-"
        rating = data.get("vote_average", "N/A")
        genres = ", ".join([g["name"] for g in data.get("genres", [])]) or "-"
        st.markdown(
            f"<div class='small-muted'>Release: {release}</div>", unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='small-muted'>⭐ Rating: {rating}</div>", unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='small-muted'>Genres: {genres}</div>", unsafe_allow_html=True
        )
        st.markdown("---")
        st.markdown("### Overview")
        st.write(data.get("overview") or "No overview available.")
        st.markdown("</div>", unsafe_allow_html=True)


    if data.get("backdrop_url"):
        st.markdown("#### Backdrop")
        st.image(data["backdrop_url"], use_container_width=True)

    st.divider()
    st.markdown("### ✅ Recommendations")

    # Recommendations (TF-IDF + Genre) via your bundle endpoint

    title = (data.get("title") or "").strip()
    if title:
        bundle, err2 = api_get_json(
            "/movie/search",
            params={"query": title, "tfidf_top_n": 12, "genre_limit": 12},
        )

        if not err2 and bundle:
            tab1, tab2 = st.tabs([
                "🤖 AI Similar",
                "🎭 Genre Match",
            ])

            with tab1:
                poster_grid(
                    to_cards_from_tfidf_items(bundle.get("tfidf_recommendations")),
                    cols=grid_cols,
                    key_prefix="details_tfidf",
                )

            with tab2:
                poster_grid(
                    bundle.get("genre_recommendations", []),
                    cols=grid_cols,
                    key_prefix="details_genre",
                )

        else:
            st.info("Showing Genre recommendations (fallback).")
            genre_only, err3 = api_get_json(
                "/recommend/genre", params={"tmdb_id": tmdb_id, "limit": 18}
            )
            if not err3 and genre_only:
                poster_grid(
                    genre_only, cols=grid_cols, key_prefix="details_genre_fallback"
                )
            else:
                st.warning("No recommendations available right now.")
    else:
        st.warning("No title available to compute recommendations.")