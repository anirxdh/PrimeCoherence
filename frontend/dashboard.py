import streamlit as st
import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import time
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Prime Coherence - Quantum Circuit Analyzer",
    page_icon="⚛️",
    layout="wide"
)

# Initialize session state
if 'api_base_url' not in st.session_state:
    # Use environment variable if available, otherwise default to localhost
    st.session_state.api_base_url = os.environ.get('API_BASE_URL', "http://localhost:8000")

def make_api_request(endpoint, method="GET", data=None, files=None):
    """Make API request with error handling."""
    try:
        url = f"{st.session_state.api_base_url}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, data=data, files=files, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            error_msg = response.json().get('error', 'Unknown error') if response.content else 'No response'
            st.error(f"API Error ({response.status_code}): {error_msg}")
            return None
            
    except requests.exceptions.ConnectionError:
        st.error("Connection error: Could not connect to the API server. Make sure the backend is running.")
        return None
    except requests.exceptions.Timeout:
        st.error("Request timeout: The API server took too long to respond.")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None

def main():
    st.title("⚛️ Prime Coherence - Quantum Circuit Analyzer")
    st.markdown("Upload and analyze quantum circuits in various formats")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Configuration")
        
        # API Base URL
        api_url = st.text_input(
            "API Base URL",
            value=st.session_state.api_base_url,
            help="URL of the Prime Coherence API server"
        )
        if api_url != st.session_state.api_base_url:
            st.session_state.api_base_url = api_url
            st.rerun()
        
        # Health check
        if st.button("Check API Health"):
            health = make_api_request("/health")
            if health:
                st.success("✅ API is healthy")
            else:
                st.error("❌ API is not responding")
        
        # Database Management
        st.subheader("🗄️ Database Management")
        
        # Show quick database stats
        stats = make_api_request("/database-stats")
        if stats and stats.get('total_records', 0) > 0:
            st.info(f"📊 Database has {stats.get('total_records', 0)} records ({stats.get('recent_activity_24h', 0)} in last 24h)")
        elif stats and stats.get('total_records', 0) == 0:
            st.info("📊 Database is empty")
        
        # Manual refresh button
        if st.button("🔄 Refresh Stats"):
            st.rerun()
        
        # Show detailed database statistics
        if st.button("📊 Show Detailed Stats"):
            if stats:
                st.write("**Database Statistics:**")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Records", stats.get('total_records', 0))
                    st.metric("With Artifacts", stats.get('records_with_artifacts', 0))
                
                with col2:
                    st.metric("Recent Activity (24h)", stats.get('recent_activity_24h', 0))
                    
                    # Format distribution
                    format_dist = stats.get('format_distribution', {})
                    if format_dist:
                        st.write("**Format Distribution:**")
                        for fmt, count in format_dist.items():
                            st.write(f"• {fmt}: {count}")
            else:
                st.error("Failed to load database statistics")
        
        # Clear Database
        st.write("**Clear Database:**")
        
        # Use session state to track confirmation
        if 'show_clear_confirmation' not in st.session_state:
            st.session_state.show_clear_confirmation = False
        
        # Quick clear button (for testing)
        if st.button("🗑️ Quick Clear (No Confirmation)", type="secondary"):
            with st.spinner("Clearing database..."):
                result = make_api_request("/clear-database", method="POST")
                if result:
                    st.success("✅ Database cleared successfully!")
                    st.write(f"Deleted {result.get('deleted_records', 0)} records and {result.get('deleted_files', 0)} files")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Failed to clear database")
        
        # Confirmation-based clear button
        if st.button("🗑️ Clear Database (With Confirmation)", type="secondary"):
            st.session_state.show_clear_confirmation = True
        
        if st.session_state.show_clear_confirmation:
            st.warning("⚠️ **Danger Zone**")
            st.write("This will permanently delete ALL analysis results and artifacts.")
            st.write("This action cannot be undone!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("❌ Cancel", key="cancel_clear"):
                    st.session_state.show_clear_confirmation = False
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Yes, Clear Everything", key="confirm_clear", type="primary"):
                    with st.spinner("Clearing database..."):
                        # Make API request to clear database
                        result = make_api_request("/clear-database", method="POST")
                        if result:
                            st.success("✅ Database cleared successfully!")
                            st.write(f"Deleted {result.get('deleted_records', 0)} records and {result.get('deleted_files', 0)} files")
                            # Reset confirmation state
                            st.session_state.show_clear_confirmation = False
                            # Add a delay and then refresh
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("❌ Failed to clear database")
                            st.write("Please check the backend logs for more details.")
                            st.session_state.show_clear_confirmation = False
        
        st.divider()
        
        # Upload section
        st.header("Upload & Analyze")
        
        uploaded_file = st.file_uploader(
            "Choose a circuit file",
            type=['qasm', 'json'],
            help="Upload QASM or neutral JSON circuit files"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            input_format = st.selectbox(
                "Input Format",
                ["auto", "qasm", "neutral_json"],
                help="Circuit input format (auto-detect recommended)"
            )
        
        with col2:
            output_format = st.selectbox(
                "Output Format",
                ["qiskit", "cirq", "pyquil", "braket", "neutral_json"],
                help="Target format for conversion"
            )
        
        # Backend profile
        backend_profile = st.text_area(
            "Backend Profile (JSON, optional)",
            height=100,
            help="JSON configuration for backend-specific parameters"
        )
        
        # Notes
        notes = st.text_input("Notes (optional)", help="Add notes about this circuit")
        
        # Analyze button
        if st.button("🚀 Analyze Circuit", type="primary"):
            if uploaded_file is not None:
                analyze_circuit(uploaded_file, input_format, output_format, backend_profile, notes)
            else:
                st.error("Please upload a circuit file first")
    
    # Main content area
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Results", "🔄 Convert", "📈 Compare", "ℹ️ About"])
    
    with tab1:
        show_results()
    
    with tab2:
        show_convert()
    
    with tab3:
        show_compare()
    
    with tab4:
        show_about()

def analyze_circuit(file, input_format, output_format, backend_profile, notes):
    """Analyze uploaded circuit."""
    with st.spinner("Analyzing circuit..."):
        # Prepare form data
        data = {
            'input_format': input_format,
            'output_format': output_format,
            'backend_profile': backend_profile if backend_profile.strip() else '',
            'notes': notes
        }
        
        files = {'file': (file.name, file.getvalue(), 'text/plain')}
        
        # Make API request
        result = make_api_request("/upload", method="POST", data=data, files=files)
        
        if result:
            if result.get('existing', False):
                st.warning(f"Circuit already analyzed (Run ID: {result['run_id']})")
            else:
                st.success("✅ Circuit analyzed successfully!")
                
                # Display results
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📊 Metrics")
                    metrics = result.get('metrics', {})
                    
                    if metrics:
                        # Create metrics dataframe
                        metrics_data = []
                        for key, value in metrics.items():
                            if key != 'gate_counts':  # Handle gate counts separately
                                metrics_data.append([key.replace('_', ' ').title(), value])
                        
                        if metrics_data:
                            metrics_df = pd.DataFrame(metrics_data, columns=['Metric', 'Value'])
                            st.dataframe(metrics_df, use_container_width=True)
                        
                        # Gate counts
                        gate_counts = metrics.get('gate_counts', {})
                        if gate_counts:
                            st.subheader("🔧 Gate Counts")
                            gate_df = pd.DataFrame(list(gate_counts.items()), columns=['Gate', 'Count'])
                            st.dataframe(gate_df, use_container_width=True)
                
                with col2:
                    st.subheader("⚠️ Alerts")
                    alerts = result.get('alerts', [])
                    if alerts:
                        for alert in alerts:
                            st.warning(alert)
                    else:
                        st.info("No alerts")
                
                # Show artifacts
                st.subheader("📁 Generated Artifacts")
                if result.get('artifacts'):
                    artifacts = result['artifacts']
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if artifacts.get('png'):
                            st.write("**Circuit Diagram:**")
                            png_url = f"{st.session_state.api_base_url}/artifacts/{artifacts['png']}"
                            st.image(png_url, caption="Circuit Diagram")
                    
                    with col2:
                        if artifacts.get('pdf'):
                            st.write("**PDF Report:**")
                            pdf_url = f"{st.session_state.api_base_url}/artifacts/{artifacts['pdf']}"
                            st.markdown(f"[📄 Download PDF Report]({pdf_url})")

def show_results():
    """Display recent analysis results."""
    st.header("📊 Recent Analysis Results")
    
    if st.button("🔄 Refresh Results"):
        st.rerun()
    
    # Get results from API
    results = make_api_request("/results?limit=20")
    
    if results and results.get('runs'):
        runs = results['runs']
        
        # Create results dataframe
        results_data = []
        for run in runs:
            metrics = run.get('metrics', {})
            results_data.append({
                'ID': run['id'],
                'Created': run['created_at'][:19] if run['created_at'] else '',
                'Input': run['input_format'],
                'Output': run['output_format'],
                'Depth': metrics.get('depth', 'N/A'),
                'QES': f"{metrics.get('qes', 0):.3f}" if metrics.get('qes') else 'N/A',
                'Fidelity': f"{metrics.get('fidelity', 0):.3f}" if metrics.get('fidelity') else 'N/A',
                'Qubits': metrics.get('num_qubits', 'N/A'),
                'Gates': metrics.get('num_gates', 'N/A')
            })
        
        if results_data:
            df = pd.DataFrame(results_data)
            st.dataframe(df, use_container_width=True)
            
            # Show detailed view
            st.subheader("📋 Detailed View")
            selected_id = st.selectbox(
                "Select a run to view details:",
                options=[run['id'] for run in runs],
                format_func=lambda x: f"Run {x}"
            )
            
            if selected_id:
                show_run_details(selected_id)
        else:
            st.info("No analysis results found")
    else:
        st.info("No analysis results found or API error")

def show_run_details(run_id):
    """Show detailed information for a specific run."""
    result = make_api_request(f"/result/{run_id}")
    
    if result:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Run Information")
            st.write(f"**Run ID:** {result['id']}")
            st.write(f"**Created:** {result['created_at']}")
            st.write(f"**Input Format:** {result['input_format']}")
            st.write(f"**Output Format:** {result['output_format']}")
            
            if result.get('notes'):
                st.write(f"**Notes:** {result['notes']}")
        
        with col2:
            st.subheader("📊 Metrics")
            metrics = result.get('metrics', {})
            if metrics:
                for key, value in metrics.items():
                    if key != 'gate_counts':
                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")
        
        # Alerts
        alerts = result.get('alerts', [])
        if alerts:
            st.subheader("⚠️ Alerts")
            for alert in alerts:
                st.warning(alert)
        
        # Artifacts
        if result.get('artifact_png') or result.get('artifact_pdf'):
            st.subheader("📁 Artifacts")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if result.get('artifact_png'):
                    st.write("**Circuit Diagram:**")
                    png_url = f"{st.session_state.api_base_url}/artifacts/{result['artifact_png']}"
                    st.image(png_url, caption="Circuit Diagram")
            
            with col2:
                if result.get('artifact_pdf'):
                    st.write("**PDF Report:**")
                    pdf_url = f"{st.session_state.api_base_url}/artifacts/{result['artifact_pdf']}"
                    st.markdown(f"[📄 Download PDF Report]({pdf_url})")

def show_compare():
    """Compare multiple analysis results."""
    st.header("📈 Compare Results")
    
    # Get recent results for selection
    results = make_api_request("/results?limit=50")
    
    if results and results.get('runs'):
        runs = results['runs']
        
        # Create selection interface
        st.write("Select runs to compare (2-10):")
        
        selected_runs = st.multiselect(
            "Choose runs:",
            options=[(run['id'], f"Run {run['id']} - {run['input_format']} → {run['output_format']}") for run in runs],
            format_func=lambda x: x[1],
            max_selections=10
        )
        
        if len(selected_runs) >= 2:
            if st.button("📊 Compare Selected Runs"):
                compare_runs([run_id for run_id, _ in selected_runs])
        else:
            st.info("Select at least 2 runs to compare")
    else:
        st.info("No analysis results found")

def compare_runs(run_ids):
    """Compare selected runs."""
    # Get detailed data for each run
    comparison_data = []
    
    for run_id in run_ids:
        result = make_api_request(f"/result/{run_id}")
        if result:
            metrics = result.get('metrics', {})
            comparison_data.append({
                'Run ID': run_id,
                'Input': result['input_format'],
                'Output': result['output_format'],
                'Depth': metrics.get('depth', 0),
                'QES': metrics.get('qes', 0),
                'Fidelity': metrics.get('fidelity', 0),
                'Energy': metrics.get('energy', 0),
                'E1': metrics.get('e1', 0),
                'Qubits': metrics.get('num_qubits', 0),
                'Gates': metrics.get('num_gates', 0)
            })
    
    if comparison_data:
        # Create comparison table
        st.subheader("📊 Comparison Table")
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True)
        
        # Create comparison charts
        st.subheader("📈 Comparison Charts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Depth comparison
            fig, ax = plt.subplots(figsize=(8, 6))
            run_ids = [row['Run ID'] for row in comparison_data]
            depths = [row['Depth'] for row in comparison_data]
            ax.bar(run_ids, depths, color='skyblue')
            ax.set_title('Circuit Depth Comparison')
            ax.set_xlabel('Run ID')
            ax.set_ylabel('Depth')
            st.pyplot(fig)
        
        with col2:
            # QES comparison
            fig, ax = plt.subplots(figsize=(8, 6))
            qes_values = [row['QES'] for row in comparison_data]
            ax.bar(run_ids, qes_values, color='lightgreen')
            ax.set_title('Quantum Efficiency Score Comparison')
            ax.set_xlabel('Run ID')
            ax.set_ylabel('QES')
            st.pyplot(fig)
        
        # Fidelity comparison
        fig, ax = plt.subplots(figsize=(10, 6))
        fidelity_values = [row['Fidelity'] for row in comparison_data]
        ax.bar(run_ids, fidelity_values, color='lightcoral')
        ax.set_title('Fidelity Comparison')
        ax.set_xlabel('Run ID')
        ax.set_ylabel('Fidelity')
        st.pyplot(fig)

def show_convert():
    """Show circuit conversion interface."""
    st.header("🔄 Circuit Conversion")
    st.write("Convert circuits between different formats without full analysis.")
    
    # File upload for conversion
    uploaded_file = st.file_uploader(
        "Choose a circuit file to convert",
        type=['qasm', 'json'],
        key="convert_uploader",
        help="Upload QASM or neutral JSON circuit files"
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns(2)
        
        with col1:
            input_format = st.selectbox(
                "Input Format",
                ["auto", "qasm", "neutral_json"],
                key="convert_input",
                help="Circuit input format (auto-detect recommended)"
            )
        
        with col2:
            output_format = st.selectbox(
                "Output Format",
                ["qiskit", "cirq", "pyquil", "braket", "neutral_json"],
                key="convert_output",
                help="Target format for conversion"
            )
        
        # Convert button
        if st.button("🔄 Convert Circuit", type="primary"):
            with st.spinner("Converting circuit..."):
                # Prepare form data
                data = {
                    'input_format': input_format,
                    'output_format': output_format
                }
                
                files = {'file': (uploaded_file.name, uploaded_file.getvalue(), 'text/plain')}
                
                # Make API request
                result = make_api_request("/convert", method="POST", data=data, files=files)
                
                if result:
                    st.success("✅ Circuit converted successfully!")
                    
                    # Display results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("📋 Conversion Info")
                        st.write(f"**Input Format:** {result.get('input_format', 'N/A')}")
                        st.write(f"**Output Format:** {result.get('output_format', 'N/A')}")
                        
                        # Show neutral IR
                        neutral_ir = result.get('neutral_ir', {})
                        if neutral_ir:
                            st.write("**Neutral IR:**")
                            st.json(neutral_ir)
                    
                    with col2:
                        st.subheader("📄 Converted Output")
                        converted_result = result.get('result', '')
                        if converted_result:
                            # Create a text area for the converted code
                            st.text_area(
                                "Converted Circuit",
                                value=converted_result,
                                height=400,
                                help="Copy the converted circuit code"
                            )
                            
                            # Add download button
                            # Handle both string and dictionary results
                            if isinstance(converted_result, dict):
                                download_data = json.dumps(converted_result, indent=2).encode('utf-8')
                            else:
                                download_data = str(converted_result).encode('utf-8')
                            
                            st.download_button(
                                label="📥 Download Converted File",
                                data=download_data,
                                file_name=f"converted_circuit.{output_format}",
                                mime="text/plain"
                            )
                else:
                    st.error("❌ Failed to convert circuit")


def show_about():
    """Show information about the application."""
    st.header("ℹ️ About Prime Coherence")
    
    st.markdown("""
    **Prime Coherence** is a quantum circuit analysis and conversion tool that helps researchers and developers:
    
    ### 🔧 Features
    - **Circuit Upload**: Support for QASM and neutral JSON formats
    - **Format Conversion**: Convert between Qiskit, Cirq, PyQuil, Braket, and neutral JSON
    - **Metrics Analysis**: Compute depth, fidelity, energy efficiency, and QES scores
    - **Artifact Generation**: Generate circuit diagrams and PDF reports
    - **Deduplication**: Avoid re-analyzing identical circuits
    
    ### 📊 Metrics Explained
    - **Depth**: Number of layers in the circuit
    - **QES**: Quantum Efficiency Score (weighted aggregate)
    - **Fidelity**: Estimated circuit fidelity based on gate errors
    - **Energy**: Energy consumption estimate
    - **E1**: Energy efficiency score
    
    ### 🚀 Getting Started
    1. Upload a quantum circuit file (QASM or JSON)
    2. Select input and output formats
    3. Optionally provide backend profile parameters
    4. Click "Analyze Circuit" to process
    5. View results, metrics, and generated artifacts
    
    ### 🔗 API Endpoints
    - `GET /health` - Health check
    - `POST /upload` - Upload and analyze circuit
    - `POST /convert` - Convert circuit format
    - `GET /results` - Get analysis results
    - `GET /result/{id}` - Get specific result
    - `GET /compare` - Compare multiple results
    - `GET /artifacts/{filename}` - Download artifacts
    
    ### 🛠️ Technology Stack
    - **Backend**: Flask REST API with SQLite
    - **Frontend**: Streamlit web interface
    - **Analysis**: Custom metrics computation
    - **Visualization**: Matplotlib for circuit diagrams
    - **Reports**: ReportLab for PDF generation
    """)

if __name__ == "__main__":
    main()
