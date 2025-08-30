import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional

def init_db(db_path: str) -> None:
    """Initialize SQLite database with runs table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            input_format TEXT NOT NULL,
            output_format TEXT NOT NULL,
            backend_profile TEXT,
            metrics TEXT,
            alerts TEXT,
            artifact_png TEXT,
            artifact_pdf TEXT,
            notes TEXT,
            raw_input_hash TEXT UNIQUE NOT NULL,
            neutral_ir TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_run(conn: sqlite3.Connection, **fields) -> int:
    """Insert a new run record and return the run ID."""
    cursor = conn.cursor()
    
    # Prepare data
    data = {
        'created_at': datetime.utcnow().isoformat(),
        'input_format': fields.get('input_format', ''),
        'output_format': fields.get('output_format', ''),
        'backend_profile': json.dumps(fields.get('backend_profile')) if fields.get('backend_profile') else None,
        'metrics': json.dumps(fields.get('metrics', {})),
        'alerts': json.dumps(fields.get('alerts', [])),
        'artifact_png': fields.get('artifact_png'),
        'artifact_pdf': fields.get('artifact_pdf'),
        'notes': fields.get('notes'),
        'raw_input_hash': fields.get('raw_input_hash', ''),
        'neutral_ir': json.dumps(fields.get('neutral_ir', {}))
    }
    
    cursor.execute('''
        INSERT INTO runs (
            created_at, input_format, output_format, backend_profile,
            metrics, alerts, artifact_png, artifact_pdf, notes,
            raw_input_hash, neutral_ir
        ) VALUES (
            :created_at, :input_format, :output_format, :backend_profile,
            :metrics, :alerts, :artifact_png, :artifact_pdf, :notes,
            :raw_input_hash, :neutral_ir
        )
    ''', data)
    
    conn.commit()
    return cursor.lastrowid

def get_runs(conn: sqlite3.Connection, limit: int = 50, offset: int = 0) -> List[Dict]:
    """Get recent runs with pagination."""
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM runs 
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
    ''', (limit, offset))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def get_run(conn: sqlite3.Connection, run_id: int) -> Optional[Dict]:
    """Get a specific run by ID."""
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM runs WHERE id = ?', (run_id,))
    row = cursor.fetchone()
    
    return dict(row) if row else None

def get_runs_by_ids(conn: sqlite3.Connection, run_ids: List[int]) -> List[Dict]:
    """Get multiple runs by their IDs."""
    if not run_ids:
        return []
    
    cursor = conn.cursor()
    
    # Create placeholders for the IN clause
    placeholders = ','.join('?' * len(run_ids))
    cursor.execute(f'SELECT * FROM runs WHERE id IN ({placeholders})', run_ids)
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def get_run_by_hash(conn: sqlite3.Connection, input_hash: str) -> Optional[Dict]:
    """Get a run by its input hash (for deduplication)."""
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM runs WHERE raw_input_hash = ?', (input_hash,))
    row = cursor.fetchone()
    
    return dict(row) if row else None

def update_run_artifacts(conn: sqlite3.Connection, run_id: int, 
                        artifact_png: Optional[str], artifact_pdf: Optional[str]) -> None:
    """Update run record with artifact file paths."""
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE runs 
        SET artifact_png = ?, artifact_pdf = ?
        WHERE id = ?
    ''', (artifact_png, artifact_pdf, run_id))
    
    conn.commit()

def delete_run(conn: sqlite3.Connection, run_id: int) -> bool:
    """Delete a run by ID. Returns True if successful."""
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM runs WHERE id = ?', (run_id,))
    conn.commit()
    
    return cursor.rowcount > 0

def get_run_count(conn: sqlite3.Connection) -> int:
    """Get total number of runs."""
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM runs')
    return cursor.fetchone()[0]

def search_runs(conn: sqlite3.Connection, query: str, limit: int = 50) -> List[Dict]:
    """Search runs by notes or input format."""
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM runs 
        WHERE notes LIKE ? OR input_format LIKE ? OR output_format LIKE ?
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit))
    
    rows = cursor.fetchall()
    return [dict(row) for row in rows]
