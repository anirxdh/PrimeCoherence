import os
import json
from typing import Dict, List
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

def render_circuit_png(neutral_ir: Dict, out_path: str) -> str:
    """Render circuit diagram as PNG using matplotlib."""
    num_qubits = neutral_ir['num_qubits']
    gates = neutral_ir['gates']
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, max(4, num_qubits * 0.8)))
    
    # Draw qubit lines
    for i in range(num_qubits):
        y = num_qubits - 1 - i  # Invert y-axis for top-to-bottom numbering
        ax.plot([0, len(gates) + 1], [y, y], 'k-', linewidth=2, alpha=0.7)
        ax.text(-0.5, y, f'q[{i}]', ha='right', va='center', fontsize=10, fontweight='bold')
    
    # Draw gates
    gate_x = 1
    for gate in gates:
        gate_name = gate['name']
        qubits = gate['qubits']
        
        # Determine gate color and shape
        if gate_name == 'h':
            color = 'lightblue'
            shape = 'circle'
        elif gate_name == 'cx':
            color = 'lightgreen'
            shape = 'rectangle'
        elif gate_name == 'rz':
            color = 'lightcoral'
            shape = 'diamond'
        else:
            color = 'lightgray'
            shape = 'circle'
        
        # Draw gate symbols
        for qubit in qubits:
            y = num_qubits - 1 - qubit
            
            if shape == 'circle':
                circle = plt.Circle((gate_x, y), 0.3, color=color, ec='black', linewidth=1)
                ax.add_patch(circle)
                ax.text(gate_x, y, gate_name.upper(), ha='center', va='center', fontsize=8, fontweight='bold')
            elif shape == 'rectangle':
                rect = patches.Rectangle((gate_x - 0.3, y - 0.3), 0.6, 0.6, 
                                       color=color, ec='black', linewidth=1)
                ax.add_patch(rect)
                ax.text(gate_x, y, gate_name.upper(), ha='center', va='center', fontsize=8, fontweight='bold')
            elif shape == 'diamond':
                diamond = patches.RegularPolygon((gate_x, y), 4, radius=0.3, 
                                               color=color, ec='black', linewidth=1)
                ax.add_patch(diamond)
                ax.text(gate_x, y, gate_name.upper(), ha='center', va='center', fontsize=8, fontweight='bold')
        
        # Draw control lines for cx gates
        if gate_name == 'cx' and len(qubits) == 2:
            q1, q2 = qubits
            y1 = num_qubits - 1 - q1
            y2 = num_qubits - 1 - q2
            
            # Control dot
            control_circle = plt.Circle((gate_x, y1), 0.1, color='black')
            ax.add_patch(control_circle)
            
            # Target cross
            ax.plot([gate_x - 0.2, gate_x + 0.2], [y2 - 0.2, y2 + 0.2], 'k-', linewidth=2)
            ax.plot([gate_x - 0.2, gate_x + 0.2], [y2 + 0.2, y2 - 0.2], 'k-', linewidth=2)
            
            # Control line
            ax.plot([gate_x, gate_x], [y1, y2], 'k-', linewidth=1, alpha=0.7)
        
        gate_x += 1
    
    # Set plot properties
    ax.set_xlim(-1, len(gates) + 1)
    ax.set_ylim(-0.5, num_qubits - 0.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Quantum Circuit Diagram', fontsize=14, fontweight='bold', pad=20)
    
    # Save the plot
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return os.path.basename(out_path)

def build_pdf_report(run_record: Dict, out_path: str) -> str:
    """Build PDF report for a circuit analysis run."""
    doc = SimpleDocTemplate(out_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center
    )
    story.append(Paragraph("Prime Coherence - Circuit Analysis Report", title_style))
    story.append(Spacer(1, 20))
    
    # Run information
    story.append(Paragraph("Run Information", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    run_info_data = [
        ['Run ID', str(run_record['id'])],
        ['Created', run_record['created_at']],
        ['Input Format', run_record['input_format']],
        ['Output Format', run_record['output_format']]
    ]
    
    if run_record.get('notes'):
        run_info_data.append(['Notes', run_record['notes']])
    
    run_info_table = Table(run_info_data, colWidths=[2*inch, 4*inch])
    run_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.grey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(run_info_table)
    story.append(Spacer(1, 20))
    
    # Metrics
    story.append(Paragraph("Circuit Metrics", styles['Heading2']))
    story.append(Spacer(1, 12))
    
    metrics = json.loads(run_record['metrics']) if run_record['metrics'] else {}
    
    metrics_data = [
        ['Metric', 'Value']
    ]
    
    if 'depth' in metrics:
        metrics_data.append(['Circuit Depth', str(metrics['depth'])])
    if 'num_qubits' in metrics:
        metrics_data.append(['Number of Qubits', str(metrics['num_qubits'])])
    if 'num_gates' in metrics:
        metrics_data.append(['Total Gates', str(metrics['num_gates'])])
    if 'fidelity' in metrics:
        metrics_data.append(['Estimated Fidelity', f"{metrics['fidelity']:.4f}"])
    if 'qes' in metrics:
        metrics_data.append(['Quantum Efficiency Score', f"{metrics['qes']:.4f}"])
    if 'energy' in metrics:
        metrics_data.append(['Energy Consumption', f"{metrics['energy']:.4f}"])
    if 'e1' in metrics:
        metrics_data.append(['E1 Score', f"{metrics['e1']:.4f}"])
    
    # Gate counts
    if 'gate_counts' in metrics:
        gate_counts = metrics['gate_counts']
        for gate, count in gate_counts.items():
            metrics_data.append([f'{gate.upper()} Gates', str(count)])
    
    metrics_table = Table(metrics_data, colWidths=[2*inch, 2*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(metrics_table)
    story.append(Spacer(1, 20))
    
    # Alerts
    alerts = json.loads(run_record['alerts']) if run_record['alerts'] else []
    if alerts:
        story.append(Paragraph("Alerts", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        for alert in alerts:
            story.append(Paragraph(f"• {alert}", styles['Normal']))
            story.append(Spacer(1, 6))
        
        story.append(Spacer(1, 20))
    
    # Circuit diagram
    if run_record.get('artifact_png'):
        png_path = os.path.join(os.path.dirname(out_path), run_record['artifact_png'])
        if os.path.exists(png_path):
            story.append(Paragraph("Circuit Diagram", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            img = Image(png_path, width=6*inch, height=4*inch)
            story.append(img)
            story.append(Spacer(1, 20))
    
    # Footer
    story.append(Paragraph(f"Report generated on {run_record['created_at']}", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    
    return os.path.basename(out_path)
