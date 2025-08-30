# Prime Coherence

A full-stack quantum circuit analysis and conversion tool with Flask REST API backend and Streamlit frontend.

## Features

- **Circuit Upload & Analysis**: Upload QASM or neutral JSON circuits
- **Format Conversion**: Convert between Qiskit, Cirq, PyQuil, Braket, and neutral JSON
- **Metrics Computation**: Depth, gate counts, fidelity, energy efficiency, QES
- **Artifact Generation**: Circuit diagrams (PNG) and reports (PDF)
- **Database Persistence**: SQLite with deduplication
- **Web Interface**: Streamlit dashboard for easy interaction

## Quick Start

### Prerequisites

- Python 3.11+
- Git

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd prime-coherence
   ```

2. **Start the Backend**:
   ```bash
   cd backend
   make install
   make run
   ```
   The API will be available at http://localhost:8000

3. **Start the Frontend** (in a new terminal):
   ```bash
   cd frontend
   make install
   make run
   ```
   The web interface will be available at http://localhost:8501

4. **Test the Application**:
   - Open http://localhost:8501 in your browser
   - Upload a circuit file (QASM or JSON)
   - Click "Analyze Circuit"
   - View results, metrics, and generated artifacts

### Sample Circuit Files

The project includes sample circuit files for testing:

- `sample_circuit.qasm` - Sample QASM circuit
- `sample_circuit.json` - Sample neutral JSON circuit

## Project Structure

```
prime-coherence/
├── backend/                 # Flask REST API
│   ├── app.py              # Main Flask application
│   ├── src/                # Core modules
│   │   ├── circuit_converter.py
│   │   ├── metrics.py
│   │   ├── db.py
│   │   └── report.py
│   ├── tests/              # Unit tests
│   ├── artifacts/          # Generated files
│   ├── requirements.txt    # Python dependencies
│   └── Makefile           # Build commands
├── frontend/               # Streamlit web interface
│   ├── dashboard.py        # Main Streamlit app
│   ├── requirements.txt    # Python dependencies
│   └── Makefile           # Build commands
├── sample_circuit.qasm     # Sample QASM circuit
├── sample_circuit.json     # Sample neutral JSON circuit
└── README.md              # This file
```

## API Endpoints

### Health Check
- `GET /health` - Service health status

### Circuit Analysis
- `POST /upload` - Upload and analyze a circuit
- `POST /convert` - Convert circuit between formats

### Results
- `GET /results` - Get all analysis results (paginated)
- `GET /result/<id>` - Get specific analysis result
- `GET /compare?ids=1,2,3` - Compare multiple results

### Artifacts
- `GET /artifacts/<filename>` - Download generated files

## Circuit Formats

### QASM Format
Supports a minimal subset of OpenQASM 2.0:
```qasm
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
h q[0];
cx q[0],q[1];
rz(1.5708) q[2];
```

### Neutral JSON Format
Simple JSON representation:
```json
{
  "num_qubits": 3,
  "gates": [
    {"name": "h", "qubits": [0], "params": []},
    {"name": "cx", "qubits": [0, 1], "params": []},
    {"name": "rz", "qubits": [2], "params": [1.5708]}
  ]
}
```

## Metrics

The application computes various circuit metrics:

- **Depth**: Number of layers in the circuit
- **Gate Counts**: Count of each gate type
- **Fidelity**: Estimated circuit fidelity (toy model)
- **Energy**: Energy consumption estimate
- **E1**: Energy efficiency score
- **QES**: Quantum Efficiency Score (weighted aggregate)

## Development

### Running Tests

```bash
cd backend
make test
```

### Code Formatting

```bash
cd backend
make fmt
```

### Cleanup

```bash
cd backend
make clean
```

## Docker (Optional)

### Backend
```bash
cd backend
docker build -t prime-coherence-backend .
docker run -p 8000:8000 prime-coherence-backend
```

### Frontend
```bash
cd frontend
docker build -t prime-coherence-frontend .
docker run -p 8501:8501 prime-coherence-frontend
```

### Docker Compose
```bash
docker-compose up --build
```

## Configuration

### Environment Variables

- `FLASK_ENV`: Flask environment (development/production)
- `DATABASE_URL`: Database connection string
- `MAX_FILE_SIZE`: Maximum file upload size (default: 5MB)
- `CORS_ORIGINS`: Allowed CORS origins

## Troubleshooting

### Common Issues

1. **Backend not starting**: Check if port 8000 is available
2. **Frontend connection errors**: Verify backend is running at http://localhost:8000
3. **File upload errors**: Check file format and size limits
4. **Database errors**: Run `make clean` to reset the database

### Logs

- **Backend**: Check Flask logs in the terminal
- **Frontend**: Check Streamlit logs in the terminal

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Flask for the web framework
- Streamlit for the web interface
- Matplotlib for circuit visualization
- ReportLab for PDF generation
# PrimeCoherence
