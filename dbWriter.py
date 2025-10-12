import pandas as pd
import psycopg2
from psycopg2 import sql

# ==== CONFIGURE THIS IF NEEDED ====
CSV_FILE_PATH = "cards.csv"  # Change if your file has a different name

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgres"
}

# Table names
MONSTERS_TABLE = "monsters"
SPELLS_TABLE = "spells"
TRAPS_TABLE = "traps"

def create_tables(cursor):
    # All tables share the same column layout — some fields just won't be used for spells/traps
    for table in [MONSTERS_TABLE, SPELLS_TABLE, TRAPS_TABLE]:
        cursor.execute(sql.SQL(f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id SERIAL PRIMARY KEY,
                name TEXT,
                description TEXT,
                set_id TEXT,
                rarity TEXT,
                price TEXT,
                volatility TEXT,
                sub_type TEXT,
                attribute TEXT,
                rank TEXT,
                attack TEXT,
                defense TEXT,
                set_name TEXT,
                set_release TEXT,
                name_official TEXT,
                index TEXT,
                index_market TEXT,
                join_id TEXT
            );
        """))

def insert_dataframe(cursor, df, table_name):
    # Only insert columns that exist
    columns = [
        "name", "description", "set_id", "rarity", "price",
        "volatility", "sub_type", "attribute", "rank", "attack",
        "defense", "set_name", "set_release", "name_official",
        "index", "index_market", "join_id"
    ]
    df = df[columns]  # Ensure correct column order

    for _, row in df.iterrows():
        values = [row[col] if pd.notna(row[col]) else None for col in columns]
        insert_query = sql.SQL("""
            INSERT INTO {table} ({fields})
            VALUES ({placeholders})
        """).format(
            table=sql.Identifier(table_name),
            fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
            placeholders=sql.SQL(", ").join(sql.Placeholder() * len(columns))
        )
        cursor.execute(insert_query, values)


def main():
    # Read the CSV
    print("Reading CSV...")
    df = pd.read_csv(CSV_FILE_PATH)

    # Connect to Postgres
    print("Connecting to Postgres...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Create the tables if they don't exist
    print("Creating tables (if not exist)...")
    create_tables(cursor)
    conn.commit()

    # Split the dataframe
    print("Splitting data by card type...")
    monsters_df = df[df["type"] == "MONSTER"]
    spells_df = df[df["type"] == "SPELL"]
    traps_df = df[df["type"] == "TRAP"]

    print(f"Monsters: {len(monsters_df)}")
    print(f"Spells: {len(spells_df)}")
    print(f"Traps: {len(traps_df)}")

    # Insert each group
    print("Inserting monsters...")
    insert_dataframe(cursor, monsters_df, MONSTERS_TABLE)
    conn.commit()

    print("Inserting spells...")
    insert_dataframe(cursor, spells_df, SPELLS_TABLE)
    conn.commit()

    print("Inserting traps...")
    insert_dataframe(cursor, traps_df, TRAPS_TABLE)
    conn.commit()

    # Cleanup
    cursor.close()
    conn.close()
    print("Done!")


if __name__ == "__main__":
    main()
