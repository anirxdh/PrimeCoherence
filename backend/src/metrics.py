"""
Metrics module for Prime Coherence.
Computes various circuit metrics and quality scores.
"""

import math
from typing import Dict, List, Tuple

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

def compute_gate_counts(neutral_ir: Dict) -> Dict[str, int]:
    """Compute count of each gate type."""
    counts = {}
    
    for gate in neutral_ir['gates']:
        gate_name = gate['name']
        counts[gate_name] = counts.get(gate_name, 0) + 1
    
    return counts

def compute_estimated_fidelity(neutral_ir: Dict, backend_profile: Dict = None) -> float:
    """Compute estimated circuit fidelity (toy model)."""
    # Default fidelity parameters
    default_fidelity_params = {
        "single_qubit_error": 0.001,
        "two_qubit_error": 0.01,
        "decoherence_time": 50.0  # microseconds
    }
    
    # Use provided backend_profile or defaults, merging with defaults for missing keys
    if backend_profile is None:
        fidelity_params = default_fidelity_params
    else:
        fidelity_params = {**default_fidelity_params, **backend_profile}
    
    gate_counts = compute_gate_counts(neutral_ir)
    depth = compute_depth(neutral_ir)
    
    # Calculate fidelity based on gate errors
    total_fidelity = 1.0
    
    # Single-qubit gate errors
    single_qubit_gates = sum(count for gate, count in gate_counts.items() 
                           if gate in ['h', 'rz'])
    total_fidelity *= (1 - fidelity_params["single_qubit_error"]) ** single_qubit_gates
    
    # Two-qubit gate errors
    two_qubit_gates = sum(count for gate, count in gate_counts.items() 
                         if gate in ['cx'])
    total_fidelity *= (1 - fidelity_params["two_qubit_error"]) ** two_qubit_gates
    
    # Decoherence effects
    decoherence_factor = math.exp(-depth / fidelity_params["decoherence_time"])
    total_fidelity *= decoherence_factor
    
    return round(total_fidelity, 4)

def compute_e1(neutral_ir: Dict, backend_profile: Dict = None) -> float:
    """Compute E1 energy efficiency score (toy model)."""
    # Default energy parameters
    default_energy_params = {
        "energy_per_gate": 1.0,
        "energy_per_qubit": 0.1
    }
    
    # Use provided backend_profile or defaults, merging with defaults for missing keys
    if backend_profile is None:
        energy_params = default_energy_params
    else:
        energy_params = {**default_energy_params, **backend_profile}
    
    gate_counts = compute_gate_counts(neutral_ir)
    num_qubits = neutral_ir['num_qubits']
    
    total_gates = sum(gate_counts.values())
    energy = (total_gates * energy_params["energy_per_gate"] + 
              num_qubits * energy_params["energy_per_qubit"])
    
    # Normalize to 0-1 scale (lower is better)
    e1_score = 1.0 / (1.0 + energy / 100.0)
    
    return round(e1_score, 4)

def compute_energy(neutral_ir: Dict) -> float:
    """Compute energy consumption (toy model)."""
    gate_counts = compute_gate_counts(neutral_ir)
    num_qubits = neutral_ir['num_qubits']
    
    # Simple energy model
    energy_weights = {
        'h': 1.0,
        'cx': 10.0,
        'rz': 2.0
    }
    
    total_energy = sum(count * energy_weights.get(gate, 1.0) 
                      for gate, count in gate_counts.items())
    total_energy += num_qubits * 0.5  # Static energy per qubit
    
    return round(total_energy, 4)

def compute_qes(neutral_ir: Dict, backend_profile: Dict = None) -> float:
    """Compute Quantum Efficiency Score (weighted aggregate)."""
    depth = compute_depth(neutral_ir)
    fidelity = compute_estimated_fidelity(neutral_ir, backend_profile)
    e1 = compute_e1(neutral_ir, backend_profile)
    energy = compute_energy(neutral_ir)
    
    # Weighted combination (normalized)
    depth_score = 1.0 / (1.0 + depth / 50.0)  # Lower depth is better
    energy_score = 1.0 / (1.0 + energy / 100.0)  # Lower energy is better
    
    qes = (0.3 * depth_score + 
           0.3 * fidelity + 
           0.2 * e1 + 
           0.2 * energy_score)
    
    return round(qes, 4)

def make_alerts(metrics: Dict) -> List[str]:
    """Generate alerts based on metrics."""
    alerts = []
    
    if metrics.get('depth', 0) > 100:
        alerts.append('Circuit depth is very high (>100)')
    
    if metrics.get('fidelity', 1.0) < 0.8:
        alerts.append('Estimated fidelity is low (<80%)')
    
    if metrics.get('qes', 0.0) < 0.5:
        alerts.append('Quantum efficiency score is low (<0.5)')
    
    gate_counts = metrics.get('gate_counts', {})
    if gate_counts.get('cx', 0) > 50:
        alerts.append('Many two-qubit gates detected (>50)')
    
    if not alerts:
        alerts.append('No significant issues detected')
    
    return alerts

def compute_all(neutral_ir: Dict, backend_profile: Dict = None) -> Tuple[Dict, List[str]]:
    """Compute all metrics and generate alerts."""
    depth = compute_depth(neutral_ir)
    gate_counts = compute_gate_counts(neutral_ir)
    fidelity = compute_estimated_fidelity(neutral_ir, backend_profile)
    e1 = compute_e1(neutral_ir, backend_profile)
    energy = compute_energy(neutral_ir)
    qes = compute_qes(neutral_ir, backend_profile)
    
    metrics = {
        'depth': depth,
        'gate_counts': gate_counts,
        'fidelity': fidelity,
        'e1': e1,
        'energy': energy,
        'qes': qes,
        'num_qubits': neutral_ir['num_qubits'],
        'num_gates': sum(gate_counts.values())
    }
    
    alerts = make_alerts(metrics)
    
    return metrics, alerts
