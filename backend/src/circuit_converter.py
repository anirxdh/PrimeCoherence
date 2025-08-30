import json
import hashlib
import re
from typing import Dict, List, Union, Literal

def load_qasm_to_neutral(qasm_str: str) -> Dict:
    """Parse QASM string and convert to neutral IR."""
    lines = qasm_str.strip().split('\n')
    neutral_ir = {
        'num_qubits': 0,
        'gates': []
    }
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('//'):
            continue
            
        # Parse qreg declaration
        qreg_match = re.match(r'qreg\s+q\[(\d+)\];', line)
        if qreg_match:
            neutral_ir['num_qubits'] = int(qreg_match.group(1))
            continue
            
        # Parse gates
        # h gate
        h_match = re.match(r'h\s+q\[(\d+)\];', line)
        if h_match:
            neutral_ir['gates'].append({
                'name': 'h',
                'qubits': [int(h_match.group(1))],
                'params': []
            })
            continue
            
        # cx gate
        cx_match = re.match(r'cx\s+q\[(\d+)\],\s*q\[(\d+)\];', line)
        if cx_match:
            neutral_ir['gates'].append({
                'name': 'cx',
                'qubits': [int(cx_match.group(1)), int(cx_match.group(2))],
                'params': []
            })
            continue
            
        # rz gate
        rz_match = re.match(r'rz\(([^)]+)\)\s+q\[(\d+)\];', line)
        if rz_match:
            neutral_ir['gates'].append({
                'name': 'rz',
                'qubits': [int(rz_match.group(2))],
                'params': [float(rz_match.group(1))]
            })
            continue
    
    return neutral_ir

def load_neutral_json(obj_or_str: Union[Dict, str]) -> Dict:
    """Load neutral IR from JSON object or string."""
    if isinstance(obj_or_str, str):
        return json.loads(obj_or_str)
    return obj_or_str

def neutral_to_qiskit(neutral_ir: Dict) -> str:
    """Convert neutral IR to Qiskit QASM string."""
    qasm_lines = ['OPENQASM 2.0;', 'include "qelib1.inc";', f'qreg q[{neutral_ir["num_qubits"]}];']
    
    for gate in neutral_ir['gates']:
        if gate['name'] == 'h':
            qasm_lines.append(f'h q[{gate["qubits"][0]}];')
        elif gate['name'] == 'cx':
            qasm_lines.append(f'cx q[{gate["qubits"][0]}],q[{gate["qubits"][1]}];')
        elif gate['name'] == 'rz':
            qasm_lines.append(f'rz({gate["params"][0]}) q[{gate["qubits"][0]}];')
    
    return '\n'.join(qasm_lines)

def neutral_to_cirq(neutral_ir: Dict) -> str:
    """Convert neutral IR to Cirq code string."""
    cirq_lines = ['import cirq', 'import numpy as np', '', 'def create_circuit():']
    cirq_lines.append(f'    qubits = cirq.LineQubit.range({neutral_ir["num_qubits"]})')
    cirq_lines.append('    circuit = cirq.Circuit()')
    cirq_lines.append('')
    
    for gate in neutral_ir['gates']:
        if gate['name'] == 'h':
            cirq_lines.append(f'    circuit.append(cirq.H(qubits[{gate["qubits"][0]}]))')
        elif gate['name'] == 'cx':
            cirq_lines.append(f'    circuit.append(cirq.CNOT(qubits[{gate["qubits"][0]}], qubits[{gate["qubits"][1]}]))')
        elif gate['name'] == 'rz':
            cirq_lines.append(f'    circuit.append(cirq.rz({gate["params"][0]})(qubits[{gate["qubits"][0]}]))')
    
    cirq_lines.append('    return circuit')
    cirq_lines.append('')
    cirq_lines.append('# Usage:')
    cirq_lines.append('# circuit = create_circuit()')
    cirq_lines.append('# print(circuit)')
    
    return '\n'.join(cirq_lines)

def neutral_to_braket(neutral_ir: Dict) -> str:
    """Convert neutral IR to Amazon Braket code string."""
    braket_lines = ['import braket.circuits as circuits', 'from braket.circuits import Circuit', '', 'def create_circuit():']
    braket_lines.append(f'    circuit = Circuit()')
    braket_lines.append('')
    
    for gate in neutral_ir['gates']:
        if gate['name'] == 'h':
            braket_lines.append(f'    circuit.h({gate["qubits"][0]})')
        elif gate['name'] == 'cx':
            braket_lines.append(f'    circuit.cnot({gate["qubits"][0]}, {gate["qubits"][1]})')
        elif gate['name'] == 'rz':
            braket_lines.append(f'    circuit.rz({gate["qubits"][0]}, {gate["params"][0]})')
    
    braket_lines.append('    return circuit')
    braket_lines.append('')
    braket_lines.append('# Usage:')
    braket_lines.append('# circuit = create_circuit()')
    braket_lines.append('# print(circuit)')
    
    return '\n'.join(braket_lines)

def neutral_to_pyquil(neutral_ir: Dict) -> str:
    """Convert neutral IR to PyQuil code string."""
    pyquil_lines = ['from pyquil import Program', 'from pyquil.gates import H, CNOT, RZ', '', 'def create_circuit():']
    pyquil_lines.append('    program = Program()')
    pyquil_lines.append('')
    
    for gate in neutral_ir['gates']:
        if gate['name'] == 'h':
            pyquil_lines.append(f'    program += H({gate["qubits"][0]})')
        elif gate['name'] == 'cx':
            pyquil_lines.append(f'    program += CNOT({gate["qubits"][0]}, {gate["qubits"][1]})')
        elif gate['name'] == 'rz':
            pyquil_lines.append(f'    program += RZ({gate["params"][0]}, {gate["qubits"][0]})')
    
    pyquil_lines.append('    return program')
    pyquil_lines.append('')
    pyquil_lines.append('# Usage:')
    pyquil_lines.append('# program = create_circuit()')
    pyquil_lines.append('# print(program)')
    
    return '\n'.join(pyquil_lines)

def estimate_swaps(neutral_ir: Dict, backend_profile: Dict = None) -> int:
    """Estimate number of SWAP operations needed for backend topology."""
    # Simple estimation based on circuit depth and qubit count
    depth = compute_depth(neutral_ir)
    num_qubits = neutral_ir['num_qubits']
    
    # Rough estimate: more qubits and depth = more SWAPs needed
    estimated_swaps = max(0, (depth * num_qubits) // 10)
    
    return estimated_swaps

def compute_depth(neutral_ir: Dict) -> int:
    """Compute circuit depth (number of layers)."""
    if not neutral_ir['gates']:
        return 0
    
    # Simple layering: increment depth when gates share qubits
    depth = 1
    current_layer_qubits = set()
    
    for gate in neutral_ir['gates']:
        gate_qubits = set(gate['qubits'])
        
        # Check if this gate shares qubits with current layer
        if current_layer_qubits & gate_qubits:
            depth += 1
            current_layer_qubits = gate_qubits
        else:
            current_layer_qubits.update(gate_qubits)
    
    return depth

def detect_input_format(file_bytes: bytes) -> Literal["qasm", "neutral_json"]:
    """Detect input format from file content."""
    content = file_bytes.decode('utf-8', errors='ignore').strip()
    
    if content.startswith('OPENQASM'):
        return 'qasm'
    else:
        try:
            json.loads(content)
            return 'neutral_json'
        except json.JSONDecodeError:
            # Default to QASM if can't parse as JSON
            return 'qasm'

def to_neutral(file_bytes: bytes, input_format: str) -> Dict:
    """Convert file content to neutral IR."""
    content = file_bytes.decode('utf-8')
    
    if input_format == 'qasm':
        return load_qasm_to_neutral(content)
    elif input_format == 'neutral_json':
        return load_neutral_json(content)
    else:
        raise ValueError(f'Unsupported input format: {input_format}')

def from_neutral(neutral_ir: Dict, output_format: str) -> Union[str, Dict]:
    """Convert neutral IR to target format."""
    if output_format == 'qiskit':
        return neutral_to_qiskit(neutral_ir)
    elif output_format == 'cirq':
        return neutral_to_cirq(neutral_ir)
    elif output_format == 'braket':
        return neutral_to_braket(neutral_ir)
    elif output_format == 'pyquil':
        return neutral_to_pyquil(neutral_ir)
    elif output_format == 'neutral_json':
        return neutral_ir
    else:
        raise ValueError(f'Unsupported output format: {output_format}')

def compute_input_hash(file_bytes: bytes) -> str:
    """Compute SHA256 hash of input file for deduplication."""
    return hashlib.sha256(file_bytes).hexdigest()
