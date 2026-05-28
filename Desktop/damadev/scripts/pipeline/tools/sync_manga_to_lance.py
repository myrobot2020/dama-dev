import sqlite3
import lancedb
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer
import json
import numpy as np

# Paths
MANGA_DB = Path("C:/Users/ADMIN/Desktop/damamanga/data/manga.db")
LANCE_DB_PATH = Path("C:/Users/ADMIN/Desktop/damadev/data/damalance")
MODEL_NAME = 'all-MiniLM-L6-v2'

def main():
    if not MANGA_DB.exists():
        print(f"Error: Manga DB not found at {MANGA_DB}")
        return

    print(f"-> Loading model {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    print("-> Connecting to databases...")
    sqlite_conn = sqlite3.connect(MANGA_DB)
    # Get all columns to be sure
    df_manga = pd.read_sql_query("SELECT * FROM panels WHERE status != 'REJECTED'", sqlite_conn)
    sqlite_conn.close()

    if df_manga.empty:
        print("No panels found in SQLite.")
        return

    print(f"Found {len(df_manga)} panels. Processing...")

    records = []
    for _, row in df_manga.iterrows():
        panel_id = str(row['panel_id'])

        # Rigorous volume extraction
        volume = str(row.get('volume') or "")
        if (not volume or volume == "None" or volume == "nan") and '_' in panel_id:
            # buddha_v01_p0019_panel05 -> buddha_v01
            parts = panel_id.split('_')
            if len(parts) >= 2:
                volume = f"{parts[0]}_{parts[1]}"

        if not volume or volume == "nan":
            volume = "buddha_v01" # Default fallback

        # Combine descriptions
        m_desc = str(row.get('modern_desc') or "")
        s_desc = str(row.get('suttic_desc') or "")
        full_text = f"{m_desc}\n\n{s_desc}".strip()

        if not full_text:
            continue

        records.append({
            "id": panel_id,
            "volume": volume,
            "text": full_text,
            "type": "manga_panel",
            "vector": model.encode(full_text).tolist()
        })

    df_lance = pd.DataFrame(records)

    print(f"-> Saving {len(df_lance)} records to LanceDB at {LANCE_DB_PATH}...")
    LANCE_DB_PATH.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(LANCE_DB_PATH))

    table_name = "manga_knowledge"
    # Overwrite table
    db.create_table(table_name, data=df_lance, mode="overwrite")
    print(f"[OK] Synced {len(df_lance)} panels to LanceDB.")

if __name__ == "__main__":
    main()
