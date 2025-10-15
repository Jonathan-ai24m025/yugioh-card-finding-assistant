import streamlit as st
import psycopg2
import pandas as pd

# Database connection settings
DB_CONFIG = {
    "host": "postgres_db",
    "port": 5432,
    "dbname": "postgres",
    "user": "postgres",
    "password": "postgres"
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def fetch_table(table_name):
    conn = get_connection()
    try:
        query = f"SELECT * FROM {table_name};"
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Error fetching data from {table_name}: {e}")
        return None
    finally:
        conn.close()

def main():
    st.title("Yu-Gi-Oh Database Viewer")

    tables = {
        "Monsters": "monsters",
        "Spells": "spells",
        "Traps": "traps"
    }

    selection = st.selectbox("Select a table to view:", list(tables.keys()))
    table_name = tables[selection]

    st.write(f"### Showing contents of: {table_name}")
    df = fetch_table(table_name)

    if df is not None and not df.empty:
        st.dataframe(df)
    else:
        st.warning(f"No data found in table '{table_name}' or unable to retrieve it.")

if __name__ == "__main__":
    main()
