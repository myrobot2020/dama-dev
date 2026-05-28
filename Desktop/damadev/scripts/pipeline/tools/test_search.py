import lancedb
import json
import pathlib
import pandas as pd
from sentence_transformers import SentenceTransformer

root = pathlib.Path.cwd()
db_path = root / "data" / "damalance"
db = lancedb.connect(str(db_path))
tbl = db.open_table("manga_knowledge")

model = SentenceTransformer('all-MiniLM-L6-v2')
query = "purification of moral conduct"
query_vec = model.encode(query).tolist()

results = tbl.search(query_vec).limit(5).to_pandas()
print("Search results for:", query)
print(results.drop(columns=['vector']).to_json(orient='records'))
