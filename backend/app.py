"""
Prime Coherence - Flask REST API
Quantum circuit analysis and conversion service.
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from src.circuit_converter import (
    detect_input_format, to_neutral, from_neutral, compute_input_hash
)
from src.metrics import compute_all
from src.db import init_db, insert_run, get_runs, get_run, get_runs_by_ids, get_run_by_hash, update_run_artifacts
from src.report import render_circuit_png, build_pdf_report


# Configuration
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), 'artifacts')
DB_PATH = os.path.join(os.path.dirname(__file__), 'prime_coherence.db')
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Ensure artifacts directory exists
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Enable CORS for Streamlit frontend
CORS(app, origins=['http://localhost:8501'])

# Initialize database
init_db(DB_PATH)


def json_error(message: str, code: int = 400) -> tuple:
    """Return JSON error response."""
    return jsonify({'error': message}), code


def parse_backend_profile(profile_str: str) -> Dict[str, Any]:
    """Parse backend profile from request field."""
    if not profile_str:
        return None
    
    try:
        return json.loads(profile_str)
    except json.JSONDecodeError:
        return None


def get_db_connection():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()})


@app.route('/upload', methods=['POST'])
def upload_circuit():
    """Upload and analyze a quantum circuit."""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return json_error('No file provided')
        
        file = request.files['file']
        if file.filename == '':
            return json_error('No file selected')
        
        # Get form parameters
        input_format = request.form.get('input_format', 'qasm')
        output_format = request.form.get('output_format', 'qiskit')
        backend_profile_str = request.form.get('backend_profile', '')
        notes = request.form.get('notes', '')
        
        # Read file content first (needed for auto-detection)
        file_bytes = file.read()
        if len(file_bytes) > MAX_FILE_SIZE:
            return json_error('File too large (max 5MB)')
        
        # Auto-detect format if specified
        if input_format == 'auto':
            input_format = detect_input_format(file_bytes)
        
        # Validate formats after auto-detection
        valid_input_formats = ['qasm', 'neutral_json']
        valid_output_formats = ['qiskit', 'cirq', 'pyquil', 'braket', 'neutral_json']
        
        if input_format not in valid_input_formats:
            return json_error(f'Invalid input_format. Must be one of: {valid_input_formats}')
        
        if output_format not in valid_output_formats:
            return json_error(f'Invalid output_format. Must be one of: {valid_output_formats}')
        
        # Parse backend profile
        backend_profile = parse_backend_profile(backend_profile_str)
        
        # Convert to neutral IR
        try:
            neutral_ir = to_neutral(file_bytes, input_format)
        except Exception as e:
            return json_error(f'Failed to parse circuit: {str(e)}')
        
        # Compute input hash (for reference only, duplicates allowed)
        input_hash = compute_input_hash(file_bytes)
        
        # Allow duplicates - no deduplication check
        conn = get_db_connection()
        
        # Compute metrics
        metrics, alerts = compute_all(neutral_ir, backend_profile)
        
        # Generate artifacts
        run_id = None
        artifact_png = None
        artifact_pdf = None
        
        try:
            # Insert run record
            run_id = insert_run(
                conn=conn,
                input_format=input_format,
                output_format=output_format,
                backend_profile=backend_profile,
                metrics=metrics,
                alerts=alerts,
                raw_input_hash=input_hash,
                neutral_ir=neutral_ir,
                notes=notes
            )
            
            # Generate circuit diagram
            png_filename = f"{run_id}-diagram.png"
            png_path = os.path.join(ARTIFACTS_DIR, png_filename)
            render_circuit_png(neutral_ir, png_path)
            artifact_png = png_filename
            
            # Generate PDF report
            pdf_filename = f"{run_id}-report.pdf"
            pdf_path = os.path.join(ARTIFACTS_DIR, pdf_filename)
            
            # Get the run record for PDF generation
            run_record = get_run(conn, run_id)
            build_pdf_report(run_record, pdf_path)
            artifact_pdf = pdf_filename
            
            # Update run with artifact paths
            update_run_artifacts(conn, run_id, artifact_png, artifact_pdf)
            
        except Exception as e:
            conn.close()
            return json_error(f'Failed to generate artifacts: {str(e)}')
        
        conn.close()
        
        # Return results
        return jsonify({
            'run_id': run_id,
            'metrics': metrics,
            'alerts': alerts,
            'artifacts': {
                'png': artifact_png,
                'pdf': artifact_pdf
            },
            'neutral_ir': neutral_ir
        })
        
    except Exception as e:
        return json_error(f'Internal server error: {str(e)}', 500)


@app.route('/convert', methods=['POST'])
def convert_circuit():
    """Convert circuit between formats without persistence."""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return json_error('No file provided')
        
        file = request.files['file']
        if file.filename == '':
            return json_error('No file selected')
        
        # Get form parameters
        input_format = request.form.get('input_format', 'qasm')
        output_format = request.form.get('output_format', 'qiskit')
        
        # Read file content first (needed for auto-detection)
        file_bytes = file.read()
        if len(file_bytes) > MAX_FILE_SIZE:
            return json_error('File too large (max 5MB)')
        
        # Auto-detect format if specified
        if input_format == 'auto':
            input_format = detect_input_format(file_bytes)
        
        # Validate formats after auto-detection
        valid_input_formats = ['qasm', 'neutral_json']
        valid_output_formats = ['qiskit', 'cirq', 'pyquil', 'braket', 'neutral_json']
        
        if input_format not in valid_input_formats:
            return json_error(f'Invalid input_format. Must be one of: {valid_input_formats}')
        
        if output_format not in valid_output_formats:
            return json_error(f'Invalid output_format. Must be one of: {valid_output_formats}')
        
        # Convert to neutral IR
        try:
            neutral_ir = to_neutral(file_bytes, input_format)
        except Exception as e:
            return json_error(f'Failed to parse circuit: {str(e)}')
        
        # Convert to output format
        try:
            result = from_neutral(neutral_ir, output_format)
        except Exception as e:
            return json_error(f'Failed to convert circuit: {str(e)}')
        
        return jsonify({
            'input_format': input_format,
            'output_format': output_format,
            'result': result,
            'neutral_ir': neutral_ir
        })
        
    except Exception as e:
        return json_error(f'Internal server error: {str(e)}', 500)


@app.route('/results', methods=['GET'])
def get_results():
    """Get recent analysis results with pagination."""
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        # Validate parameters
        if limit < 1 or limit > 100:
            return json_error('Limit must be between 1 and 100')
        if offset < 0:
            return json_error('Offset must be non-negative')
        
        conn = get_db_connection()
        runs = get_runs(conn, limit, offset)
        conn.close()
        
        # Parse JSON fields
        for run in runs:
            if run['metrics']:
                run['metrics'] = json.loads(run['metrics'])
            if run['alerts']:
                run['alerts'] = json.loads(run['alerts'])
            if run['backend_profile']:
                run['backend_profile'] = json.loads(run['backend_profile'])
            if run['neutral_ir']:
                run['neutral_ir'] = json.loads(run['neutral_ir'])
        
        return jsonify({
            'runs': runs,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'count': len(runs)
            }
        })
        
    except ValueError:
        return json_error('Invalid pagination parameters')
    except Exception as e:
        return json_error(f'Internal server error: {str(e)}', 500)


@app.route('/result/<int:run_id>', methods=['GET'])
def get_result(run_id):
    """Get specific analysis result."""
    try:
        conn = get_db_connection()
        run = get_run(conn, run_id)
        conn.close()
        
        if not run:
            return json_error('Run not found', 404)
        
        # Parse JSON fields
        if run['metrics']:
            run['metrics'] = json.loads(run['metrics'])
        if run['alerts']:
            run['alerts'] = json.loads(run['alerts'])
        if run['backend_profile']:
            run['backend_profile'] = json.loads(run['backend_profile'])
        if run['neutral_ir']:
            run['neutral_ir'] = json.loads(run['neutral_ir'])
        
        return jsonify(run)
        
    except Exception as e:
        return json_error(f'Internal server error: {str(e)}', 500)


@app.route('/compare', methods=['GET'])
def compare_results():
    """Compare multiple analysis results."""
    try:
        ids_param = request.args.get('ids', '')
        if not ids_param:
            return json_error('No run IDs provided')
        
        # Parse run IDs
        try:
            run_ids = [int(id.strip()) for id in ids_param.split(',')]
        except ValueError:
            return json_error('Invalid run IDs format')
        
        if len(run_ids) < 2:
            return json_error('At least 2 run IDs required for comparison')
        
        if len(run_ids) > 10:
            return json_error('Maximum 10 runs can be compared')
        
        conn = get_db_connection()
        runs = get_runs_by_ids(conn, run_ids)
        conn.close()
        
        if len(runs) != len(run_ids):
            return json_error('Some run IDs not found', 404)
        
        # Parse JSON fields and prepare comparison data
        comparison_data = []
        for run in runs:
            metrics = json.loads(run['metrics']) if run['metrics'] else {}
            comparison_data.append({
                'id': run['id'],
                'created_at': run['created_at'],
                'input_format': run['input_format'],
                'output_format': run['output_format'],
                'depth': metrics.get('depth', 0),
                'qes': metrics.get('qes', 0.0),
                'fidelity': metrics.get('fidelity', 0.0),
                'energy': metrics.get('energy', 0.0),
                'e1': metrics.get('e1', 0.0),
                'gate_counts': metrics.get('gate_counts', {})
            })
        
        return jsonify({
            'comparison': comparison_data,
            'run_ids': run_ids
        })
        
    except Exception as e:
        return json_error(f'Internal server error: {str(e)}', 500)


@app.route('/artifacts/<path:filename>', methods=['GET'])
def get_artifact(filename):
    """Serve saved artifacts (PNG/PDF files)."""
    try:
        # Validate filename
        if not filename or '..' in filename or '/' in filename:
            return json_error('Invalid filename')
        
        # Check if file exists
        file_path = os.path.join(ARTIFACTS_DIR, filename)
        if not os.path.exists(file_path):
            return json_error('Artifact not found', 404)
        
        return send_from_directory(ARTIFACTS_DIR, filename)
        
    except Exception as e:
        return json_error(f'Internal server error: {str(e)}', 500)


@app.route('/database-stats', methods=['GET'])
def get_database_stats():
    """Get database statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total records
        cursor.execute('SELECT COUNT(*) FROM runs')
        total_records = cursor.fetchone()[0]
        
        # Get records with artifacts
        cursor.execute('SELECT COUNT(*) FROM runs WHERE artifact_png IS NOT NULL OR artifact_pdf IS NOT NULL')
        records_with_artifacts = cursor.fetchone()[0]
        
        # Get format distribution
        cursor.execute('SELECT input_format, COUNT(*) FROM runs GROUP BY input_format')
        format_distribution = dict(cursor.fetchall())
        
        # Get recent activity
        cursor.execute('SELECT COUNT(*) FROM runs WHERE created_at >= datetime("now", "-1 day")')
        recent_activity = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'total_records': total_records,
            'records_with_artifacts': records_with_artifacts,
            'format_distribution': format_distribution,
            'recent_activity_24h': recent_activity
        })
        
    except Exception as e:
        return json_error(f'Failed to get database stats: {str(e)}', 500)


@app.route('/clear-database', methods=['POST'])
def clear_database():
    """Clear all data from the database and artifacts directory."""
    try:
        conn = get_db_connection()
        
        # Get all artifact files to delete
        cursor = conn.cursor()
        cursor.execute('SELECT artifact_png, artifact_pdf FROM runs WHERE artifact_png IS NOT NULL OR artifact_pdf IS NOT NULL')
        artifacts = cursor.fetchall()
        
        # Delete artifact files
        deleted_files = 0
        for row in artifacts:
            if row[0]:  # artifact_png
                png_path = os.path.join(ARTIFACTS_DIR, row[0])
                if os.path.exists(png_path):
                    os.remove(png_path)
                    deleted_files += 1
            
            if row[1]:  # artifact_pdf
                pdf_path = os.path.join(ARTIFACTS_DIR, row[1])
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)
                    deleted_files += 1
        
        # Clear all records from database
        cursor.execute('DELETE FROM runs')
        deleted_records = cursor.rowcount
        
        # Reset the autoincrement counter - multiple approaches for reliability
        try:
            cursor.execute('DELETE FROM sqlite_sequence WHERE name="runs"')
        except:
            pass  # sqlite_sequence might not exist
        
        # Force reset autoincrement by recreating the table
        cursor.execute('PRAGMA foreign_keys=OFF')
        
        # Get table schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='runs'")
        create_sql = cursor.fetchone()[0]
        
        # Create new table with same schema but reset autoincrement
        cursor.execute('DROP TABLE runs')
        cursor.execute(create_sql)
        
        cursor.execute('PRAGMA foreign_keys=ON')
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Database cleared successfully',
            'deleted_records': deleted_records,
            'deleted_files': deleted_files
        })
        
    except Exception as e:
        return json_error(f'Failed to clear database: {str(e)}', 500)


# Error handlers
@app.errorhandler(413)
def too_large(e):
    return json_error('File too large (max 5MB)', 413)


@app.errorhandler(404)
def not_found(e):
    return json_error('Endpoint not found', 404)


@app.errorhandler(500)
def internal_error(e):
    return json_error('Internal server error', 500)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
