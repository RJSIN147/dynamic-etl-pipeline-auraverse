"""Streamlit frontend for ETL Pipeline System."""
import streamlit as st
import requests
import json
import os
from pathlib import Path

# Configuration
API_URL = os.environ.get('API_URL', 'http://localhost:8000/api')

# Page config
st.set_page_config(
    page_title="ETL Pipeline System",
    page_icon="🔄",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
        color: #667eea;
    }
    .info-box {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .success-box {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
        margin-bottom: 1rem;
    }
    .error-box {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #f5c6cb;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">🔄 Dynamic ETL Pipeline System</h1>', unsafe_allow_html=True)

st.markdown("""
**Ingest files containing HTML, JSON, and CSV data | Auto-generate schemas | Query with Natural Language**
""")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Upload & Process", "View Schema", "Query Data", "History"])

# Initialize session state
if 'source_id' not in st.session_state:
    st.session_state.source_id = "default_source"
if 'last_upload_result' not in st.session_state:
    st.session_state.last_upload_result = None

# Source ID input (persistent across pages)
st.sidebar.markdown("---")
st.sidebar.markdown("### Source Configuration")
st.session_state.source_id = st.sidebar.text_input(
    "Source ID",
    value=st.session_state.source_id,
    help="Unique identifier for your data source"
)

# Page: Upload & Process
if page == "Upload & Process":
    st.markdown('<div class="section-header">📁 Upload & Process File</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <strong>Supported Formats:</strong> .txt, .pdf, .md<br>
    <strong>Supported Data Types:</strong> HTML, JSON, CSV (can be mixed in a single file)<br>
    <strong>Pipeline Steps:</strong> Extract → Clean → Schema Generation → Load → Query Ready
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['txt', 'pdf', 'md'],
            help="Upload a file containing HTML, JSON, or CSV data"
        )
    
    with col2:
        st.markdown("### Upload Info")
        st.info(f"**Source ID:** {st.session_state.source_id}")
        if uploaded_file:
            st.success(f"**File:** {uploaded_file.name}")
            st.write(f"**Size:** {uploaded_file.size / 1024:.2f} KB")
    
    if st.button("🚀 Process File", type="primary", disabled=not uploaded_file):
        if uploaded_file:
            with st.spinner("Processing file through ETL pipeline..."):
                try:
                    # Prepare multipart form data
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    data = {'source_id': st.session_state.source_id}
                    
                    # Upload file
                    response = requests.post(
                        f"{API_URL}/upload",
                        files=files,
                        data=data,
                        timeout=120
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.last_upload_result = result
                        
                        if result.get('status') == 'success':
                            st.markdown('<div class="success-box">✅ File processed successfully!</div>', unsafe_allow_html=True)
                            
                            # Display summary
                            summary = result.get('parsed_summary', {})
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Fragments", summary.get('total_fragments', 0))
                            with col2:
                                st.metric("Total Records", summary.get('total_records', 0))
                            with col3:
                                data_types = summary.get('data_types', [])
                                st.metric("Data Types", len(data_types))
                            
                            # Fragment details
                            st.markdown("### 📊 Extracted Fragments")
                            for frag in summary.get('fragments', []):
                                with st.expander(f"{frag['type'].upper()} (Lines {frag['start_line']}-{frag['end_line']}) - {frag['record_count']} records"):
                                    if frag.get('sample'):
                                        st.json(frag['sample'])
                            
                            # Schema info
                            st.markdown("### 🗂️ Schema Generated")
                            schema = result.get('schema', {})
                            st.write(f"**Version:** {schema.get('version', 'N/A')}")
                            st.write(f"**Collections:** {len(schema.get('collections', {}))}")
                            
                            with st.expander("View Full Schema"):
                                st.json(schema)
                        else:
                            st.markdown(f'<div class="error-box">❌ Error: {result.get("error_message")}</div>', unsafe_allow_html=True)
                    else:
                        st.error(f"Upload failed: {response.status_code} - {response.text}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Page: View Schema
elif page == "View Schema":
    st.markdown('<div class="section-header">🗂️ View Schema</div>', unsafe_allow_html=True)
    
    if st.button("🔄 Fetch Schema"):
        with st.spinner("Fetching schema..."):
            try:
                response = requests.get(
                    f"{API_URL}/schema",
                    params={'source_id': st.session_state.source_id}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    schema = result.get('schema', {})
                    
                    st.success("Schema fetched successfully!")
                    
                    # Schema metadata
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Version", schema.get('version', 'N/A'))
                    with col2:
                        st.metric("Collections", len(schema.get('collections', {})))
                    with col3:
                        data_types = schema.get('data_types_present', [])
                        st.metric("Data Types", ', '.join(data_types))
                    
                    # Collection details
                    st.markdown("### Collections")
                    collections = schema.get('collections', {})
                    
                    for coll_name, coll_info in collections.items():
                        with st.expander(f"📦 {coll_name} ({coll_info.get('record_count', 0)} records)"):
                            st.write(f"**Source Type:** {coll_info.get('source_type', 'N/A')}")
                            
                            st.markdown("**Fields:**")
                            fields = coll_info.get('fields', {})
                            
                            # Create fields table
                            field_data = []
                            for field_name, field_info in fields.items():
                                field_data.append({
                                    "Field": field_name,
                                    "Type": field_info.get('type', 'unknown'),
                                    "Required": "✓" if field_info.get('required') else "✗",
                                    "Sample": str(field_info.get('sample', ''))[:50]
                                })
                            
                            st.table(field_data)
                    
                    # Full schema JSON
                    with st.expander("📄 View Raw Schema JSON"):
                        st.json(schema)
                
                elif response.status_code == 404:
                    st.warning(f"No schema found for source_id: {st.session_state.source_id}")
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Page: Query Data
elif page == "Query Data":
    st.markdown('<div class="section-header">🔍 Query Data</div>', unsafe_allow_html=True)
    
    # Query type selection
    query_type = st.radio(
        "Query Type",
        ["Natural Language", "Direct MongoDB Query"],
        horizontal=True
    )
    
    if query_type == "Natural Language":
        st.markdown("""
        <div class="info-box">
        <strong>Natural Language Query:</strong> Ask questions in plain English, and the system will convert them to MongoDB queries using AI.
        </div>
        """, unsafe_allow_html=True)
        
        nl_query = st.text_area(
            "Enter your question",
            placeholder="Example: Show me all records where price is greater than 100",
            height=100
        )
        
        if st.button("🚀 Execute Query", type="primary", disabled=not nl_query):
            with st.spinner("Translating and executing query..."):
                try:
                    response = requests.post(
                        f"{API_URL}/query",
                        json={
                            "source_id": st.session_state.source_id,
                            "query_type": "NL",
                            "query_text": nl_query
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result.get('error'):
                            st.error(f"Query Error: {result['error']['message']}")
                        else:
                            st.success("Query executed successfully!")
                            
                            # Show translated query
                            st.markdown("### 🔄 Translated MongoDB Query")
                            st.code(result.get('db_query_translated', ''), language='json')
                            
                            # Show results
                            st.markdown("### 📊 Results")
                            results = result.get('execution_result', [])
                            st.write(f"**Found {len(results)} records**")
                            
                            if results:
                                st.json(results)
                            else:
                                st.info("No results found")
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    else:  # Direct MongoDB Query
        st.markdown("""
        <div class="info-box">
        <strong>Direct MongoDB Query:</strong> Write MongoDB queries in JSON format.
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**Example Query:**")
        st.code('''{"operation": "find", "filter": {"price": {"$gt": 100}}, "projection": {"_id": 0}}''', language='json')
        
        db_query = st.text_area(
            "Enter MongoDB query (JSON)",
            placeholder='{"operation": "find", "filter": {}, "projection": {"_id": 0}}',
            height=150
        )
        
        if st.button("🚀 Execute Query", type="primary", disabled=not db_query):
            with st.spinner("Executing query..."):
                try:
                    response = requests.post(
                        f"{API_URL}/query",
                        json={
                            "source_id": st.session_state.source_id,
                            "query_type": "DB",
                            "query_text": db_query
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if result.get('error'):
                            st.error(f"Query Error: {result['error']['message']}")
                        else:
                            st.success("Query executed successfully!")
                            
                            # Show results
                            st.markdown("### 📊 Results")
                            results = result.get('execution_result', [])
                            st.write(f"**Found {len(results)} records**")
                            
                            if results:
                                st.json(results)
                            else:
                                st.info("No results found")
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Page: History
elif page == "History":
    st.markdown('<div class="section-header">📜 History</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Upload History", "Query History"])
    
    with tab1:
        if st.button("🔄 Fetch Upload History"):
            with st.spinner("Fetching history..."):
                try:
                    response = requests.get(
                        f"{API_URL}/history/uploads",
                        params={'source_id': st.session_state.source_id}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        uploads = result.get('uploads', [])
                        
                        if uploads:
                            st.success(f"Found {len(uploads)} uploads")
                            
                            for i, upload in enumerate(uploads, 1):
                                with st.expander(f"Upload #{i} - {upload.get('file_path')} ({upload.get('timestamp')})"):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**File Type:** {upload.get('file_type')}")
                                        st.write(f"**Fragments:** {upload.get('fragments_count')}")
                                    with col2:
                                        st.write(f"**Records:** {upload.get('record_count')}")
                                        st.write(f"**Data Types:** {', '.join(upload.get('data_types', []))}")
                        else:
                            st.info("No upload history found")
                    else:
                        st.error(f"Error: {response.status_code}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with tab2:
        if st.button("🔄 Fetch Query History"):
            with st.spinner("Fetching history..."):
                try:
                    response = requests.get(
                        f"{API_URL}/history/queries",
                        params={'source_id': st.session_state.source_id}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        queries = result.get('queries', [])
                        
                        if queries:
                            st.success(f"Found {len(queries)} queries")
                            
                            for i, query in enumerate(queries, 1):
                                with st.expander(f"Query #{i} - {query.get('query_type')} ({query.get('timestamp')})"):
                                    st.write(f"**Type:** {query.get('query_type')}")
                                    st.write(f"**Original Query:**")
                                    st.code(query.get('original_query', ''))
                                    
                                    if query.get('translated_query'):
                                        st.write(f"**Translated Query:**")
                                        st.code(query.get('translated_query', ''))
                                    
                                    st.write(f"**Result Count:** {query.get('result_count', 0)}")
                                    
                                    if query.get('error'):
                                        st.error(f"Error: {query['error']}")
                        else:
                            st.info("No query history found")
                    else:
                        st.error(f"Error: {response.status_code}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
### About
**ETL Pipeline System**  
Dynamic data ingestion and querying  
Powered by Ollama & FastAPI
""")
