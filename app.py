import streamlit as st
import pandas as pd
from math import floor, ceil

# Define classes
class PositionType:
    def __init__(self, aisle, level, max_height, width_capacity, weight_capacity):
        self.aisle = aisle
        self.level = level
        self.max_height = max_height
        self.width_capacity = width_capacity
        self.weight_capacity = weight_capacity

class Box:
    def __init__(self, sku, length, width, height, weight, total_boxes):
        self.sku = sku
        self.length = length
        self.width = width
        self.height = height
        self.weight = weight
        self.total_boxes = total_boxes

class Pallet:
    def __init__(self, sku, length, width, height, weight, boxes):
        self.sku = sku
        self.length = length
        self.width = width
        self.height = height
        self.weight = weight
        self.boxes = boxes  # Number of boxes on this pallet

# Function to configure pallets for a SKU
def configure_pallets(box, pallet_length, pallet_width, position_types, clearance):
    """
    Configures pallets for a given SKU by optimizing box placement to maximize space.
    
    Args:
        box: Box object with dimensions and total_boxes
        pallet_length: Fixed length of the pallet base
        pallet_width: Fixed width of the pallet base
        position_types: List of PositionType objects
        clearance: Height clearance required (e.g., 4 inches)
    
    Returns:
        List of Pallet objects, or None if boxes cannot be placed
    """
    # Calculate maximum boxes per layer by trying both orientations
    orientation1 = floor(pallet_length / box.length) * floor(pallet_width / box.width)
    orientation2 = floor(pallet_length / box.width) * floor(pallet_width / box.length)
    boxes_per_layer = max(orientation1, orientation2)
    if boxes_per_layer == 0:
        return None  # Boxes are too large to fit on the pallet
    
    # Determine maximum layers that fit in at least one position type
    max_layers = 0
    for position in position_types:
        if box.height > position.max_height - clearance:
            continue
        layers_height = floor((position.max_height - clearance) / box.height)
        if layers_height <= 0:
            continue
        weight_per_layer = boxes_per_layer * box.weight
        if weight_per_layer > position.weight_capacity:
            continue
        layers_weight = floor(position.weight_capacity / weight_per_layer)
        possible_layers = min(layers_height, layers_weight)
        max_layers = max(max_layers, possible_layers)
    
    if max_layers == 0:
        return None  # Cannot stack even one layer due to height or weight constraints
    
    # Calculate pallet dimensions and boxes per pallet
    boxes_per_pallet = boxes_per_layer * max_layers
    pallet_height = max_layers * box.height
    pallet_weight = boxes_per_pallet * box.weight
    
    # Create pallets, distributing boxes
    pallets = []
    remaining_boxes = box.total_boxes
    while remaining_boxes > 0:
        boxes_on_pallet = min(boxes_per_pallet, remaining_boxes)
        # Adjust height if fewer boxes are placed (e.g., partial layers)
        layers_on_pallet = ceil(boxes_on_pallet / boxes_per_layer)
        pallet_height_actual = layers_on_pallet * box.height
        pallet_weight_actual = boxes_on_pallet * box.weight
        pallets.append(Pallet(box.sku, pallet_length, pallet_width, pallet_height_actual, pallet_weight_actual, boxes_on_pallet))
        remaining_boxes -= boxes_on_pallet
    
    return pallets

# Function to assign pallets to positions
def assign_pallets(pallets, position_types, clearance):
    """
    Assigns pallets to warehouse positions.
    
    Args:
        pallets: List of Pallet objects
        position_types: List of PositionType objects
        clearance: Height clearance required
    
    Returns:
        assignments: List of dicts with position, sku, and boxes
        unassigned_pallets: List of unassigned pallet SKUs
    """
    assignments = []
    unassigned_pallets = []
    for pallet in pallets:
        assigned = False
        for position in sorted(position_types, key=lambda p: p.max_height):
            if (pallet.height <= position.max_height - clearance and 
                pallet.weight <= position.weight_capacity and 
                pallet.width <= position.width_capacity):
                position_key = f"Aisle {position.aisle} Level {position.level}"
                assignments.append({
                    'position': position_key,
                    'sku': pallet.sku,
                    'boxes': pallet.boxes
                })
                assigned = True
                break
        if not assigned:
            unassigned_pallets.append(pallet.sku)
    return assignments, unassigned_pallets

# Streamlit app
st.title("Warehouse Pallet Position Calculator")

# Input pallet base dimensions
st.subheader("Pallet Base Dimensions")
pallet_length = st.number_input("Pallet Length (inches)", min_value=0.0, value=48.0)
pallet_width = st.number_input("Pallet Width (inches)", min_value=0.0, value=40.0)

# Input position types
st.subheader("Position Types")
position_data = st.data_editor(
    pd.DataFrame({
        'Aisle': ['A', 'B'],
        'Level': [1, 1],
        'Max Height': [50.0, 60.0],
        'Width Capacity': [40.0, 40.0],
        'Weight Capacity': [2000.0, 2500.0]
    }),
    num_rows="dynamic",
    key="position_data"
)

# Input box details per SKU
st.subheader("Boxes per SKU")
box_data = st.data_editor(
    pd.DataFrame({
        'SKU': ['SKU001', 'SKU002'],
        'Box Length': [12.0, 15.0],
        'Box Width': [10.0, 12.0],
        'Box Height': [10.0, 15.0],
        'Box Weight': [50.0, 60.0],
        'Total Boxes': [100, 50]
    }),
    num_rows="dynamic",
    key="box_data"
)

if st.button("Calculate"):
    # Create position types
    position_types = [
        PositionType(row['Aisle'], row['Level'], row['Max Height'], 
                    row['Width Capacity'], row['Weight Capacity'])
        for _, row in position_data.iterrows()
    ]
    
    # Create boxes
    boxes = [
        Box(row['SKU'], row['Box Length'], row['Box Width'], 
            row['Box Height'], row['Box Weight'], row['Total Boxes'])
        for _, row in box_data.iterrows()
    ]
    
    # Configure pallets for each SKU
    all_pallets = []
    unassignable_skus = []
    clearance = 4.0  # Fixed clearance value
    for box in boxes:
        pallets = configure_pallets(box, pallet_length, pallet_width, position_types, clearance)
        if pallets is None:
            unassignable_skus.append(box.sku)
        else:
            all_pallets.extend(pallets)
    
    # Assign pallets to positions
    assignments, unassigned_pallets = assign_pallets(all_pallets, position_types, clearance)
    
    # Display results
    st.subheader("Pallet Assignments")
    if assignments:
        assignments_df = pd.DataFrame(assignments)
        st.write("Detailed assignments of pallets to positions:")
        st.dataframe(assignments_df)
    else:
        st.write("No pallets assigned.")
    
    st.subheader("Unassignable SKUs")
    if unassignable_skus:
        st.write("The following SKUs could not be placed on pallets due to size or weight constraints:")
        st.write(", ".join(unassignable_skus))
    else:
        st.write("All SKUs were successfully placed on