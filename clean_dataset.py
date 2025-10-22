import pandas as pd
import numpy as np

# -------------------------
# Step 0: Load CSV
# -------------------------
df = pd.read_csv("backend/cards.csv")

# -------------------------
# Step 1: Clean string columns
# -------------------------
df['name'] = df['name'].str.replace('"', '').str.strip()
df['name'] = df['name'].fillna("NONE")
df['description'] = df['description'].str.replace('"', '').str.strip()
df['description'] = df['description'].fillna("NONE")
df['sub_type'] = df['sub_type'].str.replace('"', '').str.strip()
df['sub_type'] = df['sub_type'].fillna("NONE")
df['rarity'] = df['rarity'].str.replace('"', '').str.strip()
df['rarity'] = df['rarity'].fillna("NONE")
df['rank'] = df['rank'].str.replace('"', '').str.strip()
df['rank'] = df['rank'].fillna("NONE")


# -------------------------
# Step 2: Convert numeric columns
# -------------------------
df['price'] = df['price'].str.replace("$", "")

df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['price'] = df['price'].fillna(0)
df['attack'] = pd.to_numeric(df['attack'], errors='coerce')
df['attack'] = df['attack'].fillna(0)
df['defense'] = pd.to_numeric(df['defense'], errors='coerce')
df['defense'] = df['defense'].fillna(0)

# -------------------------
# Step 3: Map categories to IDs for PostgreSQL
# -------------------------
# type_id
df['type'] = df['type'].fillna("NONE")
type_map = {t: i+1 for i, t in enumerate(df['type'].dropna().unique())}
df['type_id'] = df['type'].map(type_map)

# attribute_id
df['attribute'] = df['attribute'].fillna("NONE")
attr_map = {a: i+1 for i, a in enumerate(df['attribute'].dropna().unique())}
df['attribute_id'] = df['attribute'].map(attr_map).astype(int)

# volatility_id
df['volatility'] = df['volatility'].fillna("NONE")
vol_map = {v: i+1 for i, v in enumerate(df['volatility'].dropna().unique())}
df['volatility_id'] = df['volatility'].map(vol_map).astype(int)

# -------------------------
# Step 4: Convert dates
# -------------------------
df['set_release'] = pd.to_datetime(df['set_release'], errors='coerce')

# -------------------------
# Step 5: Create card_sets table
# -------------------------

card_sets = df[['set_id', 'set_name', 'set_release', 'join_id']].drop_duplicates(subset=["set_id"]).reset_index(drop=True)
#card_sets = card_sets.rename(columns={'Unnamed: 0': 'card_id'}) # foreign key
card_sets['card_set_id'] = range(1, len(card_sets)+1)  # primary key

# Merge card_set_id back using only set_id
df = df.merge(
    card_sets[['card_set_id', 'set_id']],
    on='set_id',
    how='left'
)

#df = df.merge(card_sets[['card_set_id', 'set_id', 'set_name', 'set_release', 'rarity', 'price', 'volatility_id', 'join_id']],
#              on=['set_id', 'set_name', 'set_release', 'rarity', 'price', 'volatility_id', 'join_id'],
#              how='left')

# -------------------------
# Step 6: Create cards table
# -------------------------
cards = df[['Unnamed: 0', 'card_set_id', 'name', 'description', 'rarity', 'price', 'volatility_id', 'type_id', 'sub_type', 'attribute_id', 'rank', 'attack', 'defense']].copy()
cards = cards.rename(columns={'Unnamed: 0': 'card_id'}) # primary key


# -------------------------
# Step 7: Save to CSV (ready for PostgreSQL COPY)
# -------------------------
cards.to_csv("db/initdb/cleaned_cards.csv", index=False)
card_sets.to_csv("db/initdb/cleaned_card_sets.csv", index=False)
cards.to_csv("backend/cleaned_cards.csv", index=False)
card_sets.to_csv("backend/cleaned_card_sets.csv", index=False)
