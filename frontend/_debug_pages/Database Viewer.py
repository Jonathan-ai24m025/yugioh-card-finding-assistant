import streamlit as st
import pandas as pd
import psycopg2
import os

st.set_page_config(
    page_title="View Cards",
    page_icon="📋",
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

def get_total_count(conn):
    """Get total number of cards"""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM cards;")
            return cur.fetchone()[0]
    except Exception as e:
        st.error(f"Error counting cards: {str(e)}")
        return 0

def get_all_cards(conn, search_term="", rarity_filter="", type_filter=""):
    """Get all cards with optional filters"""
    try:
        with conn.cursor() as cur:
            query = """
                SELECT index_id, name, description, set_id, rarity, price, 
                       type, sub_type, attribute, rank, attack, defense,
                       set_name, set_release
                FROM cards 
                WHERE 1=1
            """
            params = []
            
            if search_term:
                query += " AND (name ILIKE %s OR description ILIKE %s)"
                params.extend([f'%{search_term}%', f'%{search_term}%'])
            
            if rarity_filter:
                query += " AND rarity = %s"
                params.append(rarity_filter)
            
            if type_filter:
                query += " AND type = %s"
                params.append(type_filter)
            
            query += " ORDER BY name"
            
            cur.execute(query, params)
            columns = [desc[0] for desc in cur.description]
            results = cur.fetchall()
            
            return pd.DataFrame(results, columns=columns)
    except Exception as e:
        st.error(f"Error loading cards: {str(e)}")
        return pd.DataFrame()

def get_unique_values(conn, column_name):
    """Get unique values for a column (for filters)"""
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT DISTINCT {column_name} FROM cards WHERE {column_name} IS NOT NULL ORDER BY {column_name};")
            return [row[0] for row in cur.fetchall()]
    except:
        return []

# Streamlit page content
st.title("📋 View All Cards")

# Initialize connection
conn = None

try:
    conn = get_db_connection()
    
    # Get total count and show status
    total_cards = get_total_count(conn)
    
    if total_cards == 0:
        st.warning("No cards found in the database. Please load data first.")
        st.stop()
    
    st.success(f"Found {total_cards:,} cards in the database")
    
    # Filters
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search by name or description", placeholder="Enter card name or description...")
    
    with col2:
        rarities = [""] + get_unique_values(conn, "rarity")
        rarity_filter = st.selectbox("🎯 Rarity", rarities)
    
    with col3:
        types = [""] + get_unique_values(conn, "type")
        type_filter = st.selectbox("🃏 Type", types)
    
    # Apply filters button
    if st.button("Apply Filters", type="primary"):
        st.rerun()
    
    # Clear filters button
    if st.button("Clear Filters"):
        st.rerun()
    
    # Get all data (with filters applied)
    with st.spinner("Loading cards..."):
        df = get_all_cards(conn, search_term, rarity_filter, type_filter)
    
    if not df.empty:
        # Display results
        st.subheader(f"📄 Showing {len(df):,} cards")
        
        # Dataframe with better formatting - show all entries
        st.dataframe(
            df,
            use_container_width=True,
            height=800,  # Increased height to show more rows
            hide_index=True,
            column_config={
                "index_id": st.column_config.NumberColumn("ID", width="small"),
                "name": st.column_config.TextColumn("Name", width="medium"),
                "description": st.column_config.TextColumn("Description", width="large"),
                "rarity": st.column_config.TextColumn("Rarity", width="small"),
                "price": st.column_config.TextColumn("Price", width="small"),
                "type": st.column_config.TextColumn("Type", width="small"),
                "sub_type": st.column_config.TextColumn("Subtype", width="small"),
                "attribute": st.column_config.TextColumn("Attribute", width="small"),
                "rank": st.column_config.TextColumn("Rank", width="small"),
                "attack": st.column_config.TextColumn("ATK", width="small"),
                "defense": st.column_config.TextColumn("DEF", width="small"),
                "set_name": st.column_config.TextColumn("Set", width="medium"),
                "set_release": st.column_config.TextColumn("Release", width="small")
            }
        )
        
        # Download option for all filtered data
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download All Results as CSV",
            data=csv,
            file_name="all_cards.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    else:
        st.info("No cards found matching your filters.")
        
    # Statistics section
    with st.expander("📊 Database Statistics"):
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        try:
            with conn.cursor() as cur:
                # Total cards
                with col1:
                    cur.execute("SELECT COUNT(*) FROM cards;")
                    total = cur.fetchone()[0]
                    st.metric("Total Cards", f"{total:,}")
                
                # Unique rarities
                with col2:
                    cur.execute("SELECT COUNT(DISTINCT rarity) FROM cards;")
                    unique_rarities = cur.fetchone()[0]
                    st.metric("Unique Rarities", unique_rarities)
                
                # Unique types
                with col3:
                    cur.execute("SELECT COUNT(DISTINCT type) FROM cards;")
                    unique_types = cur.fetchone()[0]
                    st.metric("Card Types", unique_types)
                
                # Unique sets
                with col4:
                    cur.execute("SELECT COUNT(DISTINCT set_name) FROM cards;")
                    unique_sets = cur.fetchone()[0]
                    st.metric("Card Sets", unique_sets)
                
                # Cards with price
                with col5:
                    cur.execute("SELECT COUNT(*) FROM cards WHERE price IS NOT NULL AND price != '';")
                    priced_cards = cur.fetchone()[0]
                    st.metric("Priced Cards", f"{priced_cards:,}")
                
                # Average name length (fun stat)
                with col6:
                    cur.execute("SELECT AVG(LENGTH(name)) FROM cards;")
                    avg_name_length = cur.fetchone()[0]
                    st.metric("Avg Name Length", f"{avg_name_length:.1f}")
                    
        except Exception as e:
            st.error(f"Error loading statistics: {str(e)}")
            
    # Quick insights
    with st.expander("💡 Quick Insights"):
        col1, col2 = st.columns(2)
        
        try:
            with conn.cursor() as cur:
                with col1:
                    st.subheader("Top 5 Rarities")
                    cur.execute("""
                        SELECT rarity, COUNT(*) as count 
                        FROM cards 
                        WHERE rarity IS NOT NULL 
                        GROUP BY rarity 
                        ORDER BY count DESC 
                        LIMIT 5;
                    """)
                    rarity_stats = cur.fetchall()
                    for rarity, count in rarity_stats:
                        st.write(f"**{rarity}**: {count:,} cards")
                
                with col2:
                    st.subheader("Top 5 Card Types")
                    cur.execute("""
                        SELECT type, COUNT(*) as count 
                        FROM cards 
                        WHERE type IS NOT NULL 
                        GROUP BY type 
                        ORDER BY count DESC 
                        LIMIT 5;
                    """)
                    type_stats = cur.fetchall()
                    for card_type, count in type_stats:
                        st.write(f"**{card_type}**: {count:,} cards")
                        
        except Exception as e:
            st.error(f"Error loading insights: {str(e)}")

except Exception as e:
    st.error(f"❌ Cannot connect to database: {str(e)}")
    st.info("Make sure the database is running and contains card data.")

finally:
    if conn:
        conn.close()