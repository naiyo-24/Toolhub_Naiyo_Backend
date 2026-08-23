import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import os
import uuid

def generate_income_pie_chart(verified_income: float, proposed_emi: float, existing_emi: float) -> str:
    """
    Generates a matplotlib pie chart showing Income breakdown.
    Saves it to a temporary PNG file and returns the file path.
    """
    disposable = verified_income - proposed_emi - existing_emi
    if disposable < 0:
        disposable = 0
        
    labels = ['Proposed EMI', 'Existing EMI', 'Disposable Income']
    sizes = [proposed_emi, existing_emi, disposable]
    colors = ['#1E88E5', '#FFCA28', '#43A047'] # Blue, Yellow, Green
    
    # Filter out 0 values for cleaner chart
    filtered_labels = []
    filtered_sizes = []
    filtered_colors = []
    for l, s, c in zip(labels, sizes, colors):
        if s > 0:
            filtered_labels.append(l)
            filtered_sizes.append(s)
            filtered_colors.append(c)

    # Set up the plot
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.pie(
        filtered_sizes, 
        labels=filtered_labels, 
        colors=filtered_colors, 
        autopct='%1.1f%%',
        startangle=90,
        textprops={'fontsize': 10, 'weight': 'bold'}
    )
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    
    # Title
    plt.title('Monthly Income Utilization', fontweight='bold', pad=20)
    
    # Ensure dir exists
    charts_dir = os.path.join("uploads", "temp_charts")
    os.makedirs(charts_dir, exist_ok=True)
    
    file_path = os.path.join(charts_dir, f"chart_{uuid.uuid4().hex}.png")
    plt.savefig(file_path, format='png', bbox_inches='tight', dpi=150)
    plt.close(fig)
    
    return file_path
