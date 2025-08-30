# Prime Coherence Frontend

Streamlit web interface for the Prime Coherence quantum circuit analyzer.

## Features

- **Circuit Upload**: Upload QASM or neutral JSON circuit files
- **Format Conversion**: Convert between quantum SDK formats
- **Metrics Visualization**: View circuit metrics and analysis results
- **Results Comparison**: Compare multiple circuit analyses
- **Artifact Display**: View generated circuit diagrams and reports

## Quick Start

### Installation

```bash
make install
```

### Running the Frontend

```bash
make run
```

The frontend will be available at http://localhost:8501

## Usage

1. **Configure API**: Set the API base URL in the sidebar (default: http://localhost:8000)
2. **Upload Circuit**: Choose a QASM or JSON circuit file
3. **Select Formats**: Choose input and output formats
4. **Analyze**: Click "Analyze Circuit" to process
5. **View Results**: Check the Results tab for analysis output
6. **Compare**: Use the Compare tab to compare multiple runs

## API Integration

The frontend communicates with the Prime Coherence backend API:

- **Health Check**: Verify API connectivity
- **Circuit Upload**: Send circuits for analysis
- **Results Retrieval**: Fetch analysis results and artifacts
- **Comparison**: Compare multiple analysis runs

## Dependencies

- **Streamlit**: Web application framework
- **Requests**: HTTP client for API communication
- **Matplotlib**: Chart generation for comparisons
- **Pandas**: Data manipulation and display
- **NumPy**: Numerical operations

## Configuration

### Environment Variables

- `API_BASE_URL`: Backend API server URL (default: http://localhost:8000)

### File Types

- **QASM**: OpenQASM 2.0 circuit files
- **JSON**: Neutral JSON circuit format

## Development

### Project Structure

```
frontend/
├── dashboard.py      # Main Streamlit application
├── requirements.txt  # Python dependencies
├── Makefile         # Build and run commands
└── README.md        # This file
```

### Adding Features

1. **New Pages**: Add new tabs to the main interface
2. **API Integration**: Extend API request functions
3. **Visualization**: Add new chart types for metrics
4. **File Handling**: Support additional circuit formats

## Troubleshooting

### Common Issues

1. **Connection Errors**: Ensure backend API is running
2. **File Upload Issues**: Check file format and size
3. **Display Problems**: Verify matplotlib backend configuration

### Logs

Check Streamlit logs for detailed error information:
```bash
streamlit run dashboard.py --logger.level debug
```

## License

MIT License - see LICENSE file for details.
