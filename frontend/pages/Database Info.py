import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import sys
import os

st.set_page_config(
    page_title="Load Card Data",
    page_icon="📊",
    layout="wide"
)

def get_db_connection():
    """Get database connection using environment variables"""
    return psycopg2.connect(
        host=os.getenv('DATABASE_HOST', 'postgres'),
        database=os.getenv('DATABASE_NAME', 'postgres'),
        user=os.getenv('DATABASE_USER', 'postgres'),
        password=os.getenv('DATABASE_PASSWORD', 'postgres'),
        port=5432
    )

def table_exists(conn):
    """Check if cards table exists and has data"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'cards'
                );
            """)
            table_exists = cur.fetchone()[0]
            
            if table_exists:
                cur.execute("SELECT COUNT(*) FROM cards;")
                count = cur.fetchone()[0]
                return True, count
            return False, 0
    except Exception as e:
        st.error(f"Error checking table: {str(e)}")
        return False, 0

def create_table(conn):
    """Create cards table"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS cards (
                    index_id INTEGER,
                    name TEXT,
                    description TEXT,
                    set_id TEXT,
                    rarity TEXT,
                    price TEXT,
                    volatility TEXT,
                    type TEXT,
                    sub_type TEXT,
                    attribute TEXT,
                    rank TEXT,
                    attack TEXT,
                    defense TEXT,
                    set_name TEXT,
                    set_release TEXT,
                    name_official TEXT,
                    index INTEGER,
                    index_market INTEGER,
                    join_id TEXT
                );
            """)
        conn.commit()
        st.success("✅ Cards table created successfully")
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"❌ Error creating table: {str(e)}")
        return False

def load_csv_data(conn, csv_file):
    """Load data from CSV file"""
    try:
        # Read CSV
        df = pd.read_csv(csv_file)
        
        # Show preview
        st.subheader("📋 Data Preview")
        st.dataframe(df.head(10), use_container_width=True)
        
        st.info(f"📊 Found {len(df):,} records in CSV file")
        
        # Validate required columns (basic check)
        expected_columns = ['index_id', 'name', 'description']
        missing_columns = [col for col in expected_columns if col not in df.columns]
        
        if missing_columns:
            st.warning(f"⚠️ Missing expected columns: {missing_columns}")
            st.warning("The import may still work if your CSV has different column names")
        
        # Create table if it doesn't exist
        if not create_table(conn):
            return False, "Failed to create table"
        
        # Insert data with progress
        with conn.cursor() as cur:
            # Clear existing data
            cur.execute("TRUNCATE TABLE cards;")
            
            # Insert new data with progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Convert DataFrame to list of tuples
            data_tuples = [tuple(row) for row in df.to_numpy()]
            
            # Batch insert (you can adjust batch size for large files)
            batch_size = 1000
            total_batches = (len(data_tuples) + batch_size - 1) // batch_size
            
            for i in range(0, len(data_tuples), batch_size):
                batch = data_tuples[i:i + batch_size]
                insert_query = """
                    INSERT INTO cards (
                        index_id, name, description, set_id, rarity, price, volatility,
                        type, sub_type, attribute, rank, attack, defense, set_name,
                        set_release, name_official, index, index_market, join_id
                    ) VALUES %s
                """
                execute_values(cur, insert_query, batch)
                
                # Update progress
                progress = min((i + len(batch)) / len(data_tuples), 1.0)
                progress_bar.progress(progress)
                status_text.text(f"Loading... {i + len(batch)}/{len(data_tuples)} records")
        
        conn.commit()
        progress_bar.empty()
        status_text.empty()
        
        return True, f"✅ Successfully loaded {len(df):,} records into the database!"
        
    except Exception as e:
        conn.rollback()
        return False, f"❌ Error loading data: {str(e)}"

def validate_data(conn):
    """Validate the loaded data"""
    try:
        with conn.cursor() as cur:
            # Get some basic stats
            cur.execute("SELECT COUNT(*) as total_count FROM cards;")
            total_count = cur.fetchone()[0]
            
            cur.execute("""
                SELECT 
                    COUNT(DISTINCT name) as unique_names,
                    COUNT(DISTINCT type) as unique_types,
                    COUNT(DISTINCT rarity) as unique_rarities
                FROM cards;
            """)
            stats = cur.fetchone()
            
        return total_count, stats
    except Exception as e:
        st.error(f"Error validating data: {str(e)}")
        return 0, (0, 0, 0)

# Streamlit page content
st.title("📊 Load Card Data")

st.markdown("""
Use this page to load card data from a CSV file into the database. 
The data will be stored in a PostgreSQL database and can be used by all applications.
""")

# Initialize connection
conn = None

try:
    # Check current database state
    conn = get_db_connection()
    exists, count = table_exists(conn)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if exists:
            st.success(f"✅ Cards table exists with {count:,} records")
        else:
            st.warning("❌ Cards table doesn't exist or is empty")
    
    with col2:
        if conn:
            st.success("✅ Connected to database")
        else:
            st.error("❌ Cannot connect to database")
    
    # File upload section
    st.subheader("📁 Upload CSV File")
    uploaded_file = st.file_uploader(
        "Choose cards.csv file", 
        type=['csv'],
        help="Upload the cards.csv file to populate the database"
    )
    
    if uploaded_file is not None:
        st.success(f"📄 File uploaded: {uploaded_file.name} ({uploaded_file.size:,} bytes)")
        
        # Show file info
        file_details = st.expander("📋 File Details")
        with file_details:
            try:
                df_preview = pd.read_csv(uploaded_file)
                st.write(f"**Columns:** {len(df_preview.columns)}")
                st.write(f"**Rows:** {len(df_preview):,}")
                st.write("**Columns:**", list(df_preview.columns))
            except:
                st.warning("Could not read CSV file for preview")
        
        # Load data button
        if st.button("🚀 Load Data into Database", type="primary", use_container_width=True):
            with st.spinner("Loading data into database..."):
                success, message = load_csv_data(conn, uploaded_file)
                
                if success:
                    st.success(message)
                    
                    # Show validation after successful load
                    st.subheader("✅ Data Validation")
                    total_count, stats = validate_data(conn)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Records", f"{total_count:,}")
                    with col2:
                        st.metric("Unique Names", f"{stats[0]:,}")
                    with col3:
                        st.metric("Card Types", f"{stats[1]:,}")
                    with col4:
                        st.metric("Rarity Levels", f"{stats[2]:,}")
                    
                    st.balloons()
                else:
                    st.error(message)

    # Database management section
    with st.expander("⚙️ Database Management"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Create Table Only", help="Create the cards table without loading data"):
                if create_table(conn):
                    st.success("Table created successfully")
                else:
                    st.error("Failed to create table")
        
        with col2:
            if st.button("🗑️ Clear All Data", type="secondary", help="Delete all data from cards table"):
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("TRUNCATE TABLE cards;")
                    conn.commit()
                    st.success("All data cleared from cards table")
    
    # Expected format help section
    with st.expander("📋 Expected CSV Format"):
        st.markdown("""
        Your CSV file should have the following columns (in any order):
        
        | Column | Type | Description |
        |--------|------|-------------|
        | index_id | INTEGER | Unique identifier |
        | name | TEXT | Card name |
        | description | TEXT | Card description |
        | set_id | TEXT | Set identifier |
        | rarity | TEXT | Card rarity |
        | price | TEXT | Price information |
        | volatility | TEXT | Price volatility |
        | type | TEXT | Card type |
        | sub_type | TEXT | Card subtype |
        | attribute | TEXT | Card attribute |
        | rank | TEXT | Card rank |
        | attack | TEXT | Attack points |
        | defense | TEXT | Defense points |
        | set_name | TEXT | Set name |
        | set_release | TEXT | Release date |
        | name_official | TEXT | Official name |
        | index | INTEGER | Index number |
        | index_market | INTEGER | Market index |
        | join_id | TEXT | Join identifier |
        """)
        
        st.code("""
index_id,name,description,set_id,rarity,price,volatility,type,sub_type,attribute,rank,attack,defense,set_name,set_release,name_official,index,index_market,join_id
1,"Blue-Eyes White Dragon","This legendary dragon...","LOB","Ultra Rare","$850","High","Dragon","Normal","LIGHT","8","3000","2500","Legend of Blue Eyes","2002-03-08","Blue-Eyes White Dragon",1,1,"LOB-001"
        """, language="csv")
        
except Exception as e:
    st.error(f"❌ Cannot connect to database: {str(e)}")
    st.info("""
    **Troubleshooting tips:**
    - Make sure the database container is running
    - Check if database credentials are correct
    - Verify network connectivity between containers
    - Run `docker-compose ps` to check container status
    """)

finally:
    if conn:
        conn.close()