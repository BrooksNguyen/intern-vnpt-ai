"""
Universal Kaggle Dataset Analyzer
---------------------------------
Produces a comprehensive, column-level data profile for ANY CSV dataset.
Chart-type selection is delegated to the Gemini AI endpoint so that
visualizations adapt intelligently to the data characteristics.
"""
import os
import glob
import shutil
import json
import pandas as pd
import numpy as np
from fastapi import HTTPException


def _safe_json(obj):
    """Convert numpy/pandas types to JSON-safe Python types."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return round(float(obj), 4)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    if pd.isna(obj):
        return None
    return obj


def _profile_numeric(series: pd.Series) -> dict:
    """Generate stats + distribution for a numeric column."""
    clean = series.dropna()
    if clean.empty:
        return {"type": "numeric", "stats": {}, "distribution": []}

    stats = {
        "mean": _safe_json(clean.mean()),
        "median": _safe_json(clean.median()),
        "std": _safe_json(clean.std()),
        "min": _safe_json(clean.min()),
        "max": _safe_json(clean.max()),
        "q25": _safe_json(clean.quantile(0.25)),
        "q75": _safe_json(clean.quantile(0.75)),
        "skewness": _safe_json(clean.skew()),
        "zeros_pct": _safe_json(round((clean == 0).sum() / len(clean) * 100, 2)),
    }

    # Histogram (10 bins)
    try:
        counts, edges = np.histogram(clean, bins=min(10, len(clean.unique())))
        distribution = [
            {"bin": f"{round(float(edges[i]), 2)}-{round(float(edges[i+1]), 2)}",
             "count": int(counts[i])}
            for i in range(len(counts))
        ]
    except Exception:
        distribution = []

    # Sample trend (first 200 values)
    trend = clean.head(200).tolist()
    trend = [_safe_json(v) for v in trend]

    return {"type": "numeric", "stats": stats, "distribution": distribution, "trend": trend}


def _profile_categorical(series: pd.Series) -> dict:
    """Generate value counts for a categorical / low-cardinality string column."""
    clean = series.dropna().astype(str)
    vc = clean.value_counts().head(15)
    distribution = [{"label": str(k), "count": int(v)} for k, v in vc.items()]
    return {
        "type": "categorical",
        "unique_count": int(clean.nunique()),
        "distribution": distribution,
    }


def _profile_text(series: pd.Series) -> dict:
    """Generate word-frequency and basic text stats for a long-text column."""
    clean = series.dropna().astype(str)
    lengths = clean.str.len()

    stop_words = {
        'the', 'is', 'at', 'which', 'on', 'in', 'a', 'an', 'and', 'of',
        'to', 'for', 'with', 'that', 'this', 'was', 'are', 'it', 'not',
        'but', 'have', 'has', 'had', 'from', 'they', 'been', 'would',
        'will', 'can', 'than', 'its', 'also', 'into', 'just', 'about',
        'you', 'your', 'all', 'there', 'their', 'what', 'when', 'out',
        'were', 'some', 'them', 'then', 'like', 'more', 'could', 'very',
        'http', 'https', 'www', 'com',
    }

    word_freq: dict[str, int] = {}
    for text in clean.head(2000):  # cap for performance
        for w in text.lower().split():
            w = "".join(c for c in w if c.isalpha())
            if len(w) > 2 and w not in stop_words:
                word_freq[w] = word_freq.get(w, 0) + 1

    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]

    return {
        "type": "text",
        "avg_length": _safe_json(lengths.mean()),
        "max_length": _safe_json(lengths.max()),
        "top_words": [{"word": w, "count": c} for w, c in top_words],
    }


def _profile_datetime(series: pd.Series) -> dict:
    """Generate date-range stats for a datetime column."""
    clean = pd.to_datetime(series, errors='coerce').dropna()
    if clean.empty:
        return {"type": "datetime", "stats": {}}
    return {
        "type": "datetime",
        "stats": {
            "min": str(clean.min()),
            "max": str(clean.max()),
            "range_days": int((clean.max() - clean.min()).days),
        },
    }


def _classify_column(series: pd.Series) -> str:
    """Decide whether a column is numeric, categorical, text, or datetime."""
    if pd.api.types.is_bool_dtype(series):
        return "categorical"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    # Try datetime
    sample = series.dropna().head(20).astype(str)
    try:
        parsed = pd.to_datetime(sample, errors='coerce')
        if parsed.notna().sum() > len(sample) * 0.6:
            return "datetime"
    except Exception:
        pass

    # String: categorical vs long-text
    clean = series.dropna().astype(str)
    avg_len = clean.str.len().mean() if len(clean) > 0 else 0
    nunique = clean.nunique()
    if nunique <= 30 or (nunique / max(len(clean), 1)) < 0.05:
        return "categorical"
    if avg_len > 30:
        return "text"
    return "categorical"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def analyze_kaggle_dataset(dataset_slug: str, text_column: str = None) -> dict:
    """
    Downloads a Kaggle dataset, profiles EVERY column, and returns
    a universal data profile that Gemini can use to decide charts.
    """
    error_msg = None
    try:
        # --- Vercel guard ---
        if os.environ.get('VERCEL'):
            raise ValueError("Bypassing Kaggle download on Vercel to prevent SIGKILL timeouts.")

        # --- Kaggle auth ---
        has_legacy = os.environ.get('KAGGLE_USERNAME') and os.environ.get('KAGGLE_KEY')
        has_new_token = os.environ.get('KAGGLE_API_TOKEN')

        if not (has_legacy or has_new_token):
            raise ValueError("Missing credentials. Set KAGGLE_USERNAME+KAGGLE_KEY or KAGGLE_API_TOKEN.")

        if has_new_token:
            kaggle_dir = os.path.expanduser("~/.kaggle")
            os.makedirs(kaggle_dir, exist_ok=True)
            token_path = os.path.join(kaggle_dir, "access_token")
            with open(token_path, "w") as f:
                f.write(has_new_token.strip())
            os.chmod(token_path, 0o600)

        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
            api = KaggleApi()
            api.authenticate()
        except Exception as e:
            raise ValueError(f"Kaggle API Auth Failed: {e}")

        # --- Download ---
        safe_slug = dataset_slug.replace('/', '_').replace('\\', '_')
        download_path = f"/tmp/kaggle_data/{safe_slug}"
        # Clean old download for fresh data
        if os.path.exists(download_path):
            shutil.rmtree(download_path, ignore_errors=True)
        os.makedirs(download_path, exist_ok=True)

        api.dataset_download_files(dataset_slug, path=download_path, unzip=True)

        # --- Find CSV ---
        data_files = (
            glob.glob(f"{download_path}/**/*.csv", recursive=True)
            + glob.glob(f"{download_path}/**/*.tsv", recursive=True)
            + glob.glob(f"{download_path}/**/*.txt", recursive=True)
        )
        data_files = [f for f in data_files if "readme" not in f.lower() and os.path.isfile(f)]
        if not data_files:
            raise ValueError("No CSV/TSV/TXT data files found in the dataset.")

        # Pick the largest file
        target_csv = max(data_files, key=os.path.getsize)
        df = pd.read_csv(target_csv, nrows=3000, sep=None, engine='python', on_bad_lines='skip')
        if df.empty:
            raise ValueError("CSV file is empty.")

    except BaseException as e:
        error_msg = str(e)
        # Generate rich mock profile instead of a flat mock
        return _generate_mock_profile(dataset_slug, text_column, error_msg)

    # === Build universal profile ===
    total_rows, total_cols = df.shape
    total_cells = total_rows * total_cols
    missing_count = int(df.isnull().sum().sum())
    missing_rate = round(missing_count / total_cells * 100, 2) if total_cells > 0 else 0

    columns_profile: dict[str, dict] = {}
    for col in df.columns:
        col_type = _classify_column(df[col])
        missing_pct = round(df[col].isnull().sum() / total_rows * 100, 2)

        if col_type == "numeric":
            profile = _profile_numeric(df[col])
        elif col_type == "datetime":
            profile = _profile_datetime(df[col])
        elif col_type == "text":
            profile = _profile_text(df[col])
        else:
            profile = _profile_categorical(df[col])

        profile["missing_pct"] = missing_pct
        profile["sample_values"] = [_safe_json(v) for v in df[col].dropna().head(5).tolist()]
        columns_profile[str(col)] = profile

    # Correlation matrix (numeric cols only)
    num_cols = df.select_dtypes(include=['number']).select_dtypes(exclude=['bool', 'boolean']).columns.tolist()
    correlation = None
    if len(num_cols) >= 2:
        corr_df = df[num_cols].corr()
        correlation = {
            "columns": num_cols,
            "matrix": [[_safe_json(v) for v in row] for row in corr_df.values.tolist()],
        }

    return {
        "dataset": dataset_slug,
        "csv_analyzed": os.path.basename(target_csv),
        "total_rows": int(total_rows),
        "total_cols": int(total_cols),
        "missing_rate": missing_rate,
        "column_names": list(df.columns.astype(str)),
        "columns": columns_profile,
        "correlation": correlation,
        "error": error_msg,
    }


def _generate_mock_profile(slug: str, text_column: str = None, error: str = None) -> dict:
    """Rich mock profile so the frontend/AI can still demo properly."""
    return {
        "dataset": slug,
        "csv_analyzed": "mock_data.csv",
        "total_rows": 1000,
        "total_cols": 6,
        "missing_rate": 2.5,
        "column_names": ["id", "date", "category", "value", "score", "description"],
        "columns": {
            "id": {"type": "numeric", "missing_pct": 0,
                   "stats": {"mean": 500, "median": 500, "std": 289, "min": 1, "max": 1000, "q25": 250, "q75": 750, "skewness": 0, "zeros_pct": 0},
                   "distribution": [{"bin": f"{i*100}-{(i+1)*100}", "count": 100} for i in range(10)],
                   "trend": list(range(1, 101)),
                   "sample_values": [1, 2, 3, 4, 5]},
            "date": {"type": "datetime", "missing_pct": 0,
                     "stats": {"min": "2024-01-01", "max": "2024-12-31", "range_days": 365},
                     "sample_values": ["2024-01-01", "2024-03-15", "2024-06-20"]},
            "category": {"type": "categorical", "missing_pct": 1.2, "unique_count": 5,
                         "distribution": [{"label": "A", "count": 300}, {"label": "B", "count": 250}, {"label": "C", "count": 200}, {"label": "D", "count": 150}, {"label": "E", "count": 100}],
                         "sample_values": ["A", "B", "C", "D", "E"]},
            "value": {"type": "numeric", "missing_pct": 3.5,
                      "stats": {"mean": 52.3, "median": 50.1, "std": 28.7, "min": 0.5, "max": 99.8, "q25": 26.1, "q75": 78.4, "skewness": 0.05, "zeros_pct": 0},
                      "distribution": [{"bin": f"{i*10}-{(i+1)*10}", "count": int(80 + 20 * (1 - abs(i-5)/5))} for i in range(10)],
                      "trend": [round(50 + 25 * np.sin(i / 10), 2) for i in range(100)],
                      "sample_values": [12.5, 45.2, 78.9, 23.1, 56.7]},
            "score": {"type": "numeric", "missing_pct": 0,
                      "stats": {"mean": 3.2, "median": 3.0, "std": 1.1, "min": 1, "max": 5, "q25": 2, "q75": 4, "skewness": -0.3, "zeros_pct": 0},
                      "distribution": [{"bin": "1-2", "count": 150}, {"bin": "2-3", "count": 250}, {"bin": "3-4", "count": 350}, {"bin": "4-5", "count": 250}],
                      "trend": [round(3 + np.random.randn() * 0.5, 2) for _ in range(100)],
                      "sample_values": [3, 4, 2, 5, 3]},
            "description": {"type": "text", "missing_pct": 5.0,
                            "avg_length": 85.3, "max_length": 250,
                            "top_words": [{"word": "product", "count": 120}, {"word": "quality", "count": 95}, {"word": "good", "count": 88}, {"word": "price", "count": 72}, {"word": "recommend", "count": 60}, {"word": "delivery", "count": 55}, {"word": "service", "count": 48}, {"word": "excellent", "count": 40}, {"word": "fast", "count": 35}, {"word": "satisfied", "count": 30}],
                            "sample_values": ["Great product with fast delivery", "Not satisfied with quality", "Best purchase ever"]},
        },
        "correlation": {
            "columns": ["id", "value", "score"],
            "matrix": [[1.0, 0.05, -0.02], [0.05, 1.0, 0.72], [-0.02, 0.72, 1.0]],
        },
        "error": error,
    }
