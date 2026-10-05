import os
import glob
import base64
from io import BytesIO
import pandas as pd
from fastapi import HTTPException

# Ensure kaggle is installed
try:
    # If credentials are not set, importing kaggle might raise OSError or ValueError
    import kaggle
except Exception:
    kaggle = None

def analyze_kaggle_dataset(dataset_slug: str, text_column: str = None) -> dict:
    """
    Downloads a Kaggle dataset, finds the first CSV, and performs basic NLP analysis.
    dataset_slug: e.g., 'kazanova/sentiment140'
    """
    if not kaggle:
        raise HTTPException(status_code=500, detail="Kaggle library not installed or failed to initialize (missing/invalid credentials).")

    # Check for credentials
    if not os.environ.get('KAGGLE_USERNAME') or not os.environ.get('KAGGLE_KEY'):
        raise HTTPException(
            status_code=400, 
            detail="KAGGLE_USERNAME and KAGGLE_KEY environment variables are not set. "
                   "Please configure them in your environment or Vercel dashboard."
        )

    download_path = "/tmp/kaggle_data"
    os.makedirs(download_path, exist_ok=True)

    try:
        # Download and unzip
        kaggle.api.dataset_download_cli(dataset_slug, path=download_path, unzip=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download dataset: {str(e)}")

    # Find CSV
    csv_files = glob.glob(f"{download_path}/*.csv")
    if not csv_files:
        raise HTTPException(status_code=400, detail="No CSV files found in the dataset.")
    
    target_csv = csv_files[0]
    
    try:
        # Read a sample to avoid memory/timeout issues on serverless
        df = pd.read_csv(target_csv, nrows=1000)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read CSV: {str(e)}")
        
    if df.empty:
        raise HTTPException(status_code=400, detail="The CSV file is empty.")

    # Determine text column
    if text_column and text_column in df.columns:
        col = text_column
    else:
        # Fallback to finding the first column that contains strings
        str_cols = df.select_dtypes(include=['object']).columns
        if len(str_cols) == 0:
            raise HTTPException(status_code=400, detail="No text columns found for analysis.")
        col = str_cols[0]

    texts = df[col].dropna().astype(str).tolist()
    
    # Perform Basic Analysis
    total_analyzed = len(texts)
    
    # Mocking a basic sentiment classification based on keywords for speed
    positive_words = ['good', 'great', 'awesome', 'excellent', 'happy', 'love', 'best', 'win']
    negative_words = ['bad', 'terrible', 'awful', 'sad', 'hate', 'worst', 'lose', 'fail']
    
    pos_count = 0
    neg_count = 0
    neutral_count = 0
    
    word_freq = {}
    
    for text in texts:
        lower_text = text.lower()
        
        # Sentiment
        is_pos = any(w in lower_text for w in positive_words)
        is_neg = any(w in lower_text for w in negative_words)
        
        if is_pos and not is_neg: pos_count += 1
        elif is_neg and not is_pos: neg_count += 1
        else: neutral_count += 1
            
        # Word freq
        words = lower_text.split()
        for w in words:
            w = "".join(c for c in w if c.isalpha())
            if len(w) > 4: # basic stopword filter
                word_freq[w] = word_freq.get(w, 0) + 1

    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "dataset": dataset_slug,
        "csv_analyzed": os.path.basename(target_csv),
        "column_analyzed": col,
        "total_rows_sampled": total_analyzed,
        "sentiment_distribution": {
            "positive": pos_count,
            "negative": neg_count,
            "neutral": neutral_count
        },
        "top_keywords": [{"word": k, "count": v} for k, v in top_words]
    }
