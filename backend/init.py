import time
import pandas as pd
from weaviate.classes.config import Property, DataType, Configure


def initialize_ollama(get_llm, model_name):
    # Initializes ollama to pull and serve model.
    client = get_llm()
    list_response = client.list()

    if not model_name in [m.model for m in list_response.models]:
        print(f"Model {model_name} not found. Pulling (THIS CAN TAKE SEVERAL MINUTES)...")
        client.pull(model_name)
    else:
        print(f"Model {model_name} found.")

    client.chat(model="mistral:latest", messages=[
        {
            'role': 'user',
            'content': 'This is a healthcheck. Answer with "1".',
        },
    ])
    print(f"Model {model_name} is ready.")


def initialize_weaviate(csv_path: str, get_rag, embedder):
    client = get_rag()

    # Wait until Weaviate is ready
    for _ in range(30):
        try:
            if client.is_ready():
                break
        except Exception:
            print("Waiting for Weaviate to start...")
            time.sleep(2)

    # --- Check if collection already exists ---
    existing_collections = [c for c in client.collections.list_all()]
    if "Card" in existing_collections:
        print("'Card' collection already exists, skipping initialization.")
        client.close()
        return

    print("Creating 'Card' collection schema...")
    client.collections.create(
        name="Card",
        description="Trading cards with text and attributes for semantic search",
        vector_config=Configure.Vectors.self_provided(),
        properties=[
            Property(name="name", data_type=DataType.TEXT),
            Property(name="description", data_type=DataType.TEXT),
            Property(name="set_id", data_type=DataType.TEXT),
            Property(name="rarity", data_type=DataType.TEXT),
            Property(name="type", data_type=DataType.TEXT),
            Property(name="sub_type", data_type=DataType.TEXT),
            Property(name="attribute", data_type=DataType.TEXT),
            Property(name="set_name", data_type=DataType.TEXT),
            Property(name="set_release", data_type=DataType.TEXT),
            Property(name="price", data_type=DataType.TEXT),
            Property(name="attack", data_type=DataType.TEXT),
            Property(name="defense", data_type=DataType.TEXT),
        ],
    )

    df = pd.read_csv(csv_path)

    collection = client.collections.get("Card")

    print(f"Creating 'Card' collection with {len(df)} objects (THIS CAN TAKE SEVERAL MINUTES)...")
    counter = 0

    with collection.batch.dynamic() as batch:
        for _, row in df.iterrows():
            # Build text input for embedding (ignore numbers)
            text_parts = [
                str(row.get("name", "")),
                str(row.get("description", "")),
                str(row.get("rarity", "")),
                str(row.get("type", "")),
                str(row.get("sub_type", "")),
                str(row.get("attribute", "")),
                str(row.get("set_name", "")),
                str(row.get("rank", ""))
            ]
            text = ". ".join([t for t in text_parts if t.strip()])

            if not text.strip():
                continue  # skip empty

            vector = embedder.encode(text)

            properties = {
                "name": row.get("name"),
                "description": row.get("description"),
                "set_id": row.get("set_id"),
                "rarity": row.get("rarity"),
                "type": row.get("type"),
                "sub_type": row.get("sub_type"),
                "attribute": row.get("attribute"),
                "set_name": row.get("set_name"),
                "set_release": row.get("set_release"),
                "price": row.get("price"),
                "attack": row.get("attack"),
                "defense": row.get("defense"),
            }

            if counter % 1000 == 0:
                print(f"{counter}/{len(df)}...")
            counter += 1

            batch.add_object(properties=properties, vector=vector)


    print("Weaviate initialization complete.")
    client.close()
