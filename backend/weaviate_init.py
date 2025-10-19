import os
import time
import pandas as pd
import weaviate
from weaviate.classes.config import Property, DataType
from transformers import AutoTokenizer

WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "weaviate")
WEAVIATE_PORT = os.getenv("WEAVIATE_PORT", "8080")
#WEAVIATE_URL = f"http://{WEAVIATE_HOST}:{WEAVIATE_PORT}"

# TODO: Doesn't work yet
async def initialize_weaviate(csv_path: str):
    """Check if Weaviate has data; if empty, load from CSV."""
    client = weaviate.connect_to_local(host=WEAVIATE_HOST, port=WEAVIATE_PORT)

    # Wait until Weaviate is ready
    for _ in range(30):
        try:
            if client.is_ready():
                break
        except Exception:
            print("⏳ Waiting for Weaviate to start...")
            time.sleep(2)

    # Check if collection exists
    existing_collections = [c["name"] for c in client.collections.get_all()]
    if COLLECTION_NAME not in existing_collections:
        print(f"Creating collection '{COLLECTION_NAME}'...")

        # Use free HuggingFace model integration for vectorization
        # Here we configure text2vec-transformers
        vector_config = Configure.Vectors.text2vec_transformers(
            model="sentence-transformers/all-MiniLM-L6-v2"
        )

        collection = client.collections.create(
            name=COLLECTION_NAME,
            vector_config=vector_config
        )
    else:
        collection = client.collections.use(COLLECTION_NAME)

    # Check if collection already has data
    if collection.count() > 0:
        print(f"Collection '{COLLECTION_NAME}' already populated ({collection.count()} objects). Skipping.")
        client.close()
        return

    print("Populating Weaviate with card data...")
    df = pd.read_csv(csv_path)

    # Batch import
    with collection.batch.fixed_size(batch_size=200) as batch:
        for _, row in df.iterrows():
            obj = {
                "name": row["name"],
                "description": row["description"],
                "set_name": row["set_name"],
                "type": row["type"],
                "attribute": row["attribute"]
            }
            batch.add_object(obj)
            if batch.number_errors > 10:
                print("Batch import stopped due to excessive errors.")
                break

    failed_objects = collection.batch.failed_objects
    if failed_objects:
        print(f"Number of failed imports: {len(failed_objects)}")
        print(f"First failed object: {failed_objects[0]}")

    print("Weaviate initialization complete.")
    client.close()