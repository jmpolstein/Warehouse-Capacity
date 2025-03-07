import streamlit as st
import pandas as pd
import numpy as np

# Define classes for data modeling
class PositionType:
    def __init__(self, aisle, level, max_height, width_capacity, weight_capacity):
        self.aisle = aisle
        self.level = level
        self.max_height = max_height
        self.width_capacity = width_capacity
        self.weight_capacity = weight_capacity
    
    def to_dict(self):
        return {
            'aisle': self.aisle,
            'level': self.level,
            'max_height': self.max_height,
            'width_capacity': self.width_capacity,
            'weight_capacity': self.weight_capacity
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            aisle=data['aisle'],
            level=data['level'],
            max_height=data['max_height'],
            width_capacity=data['width_capacity'],
            weight_capacity=data['weight_capacity']
        )

class Item:
    def __init__(self, sku, length, width, height, weight):
        self.sku = sku
        self.length = length
        self.width = width
        self.height = height
        self.weight = weight
    
    def to_dict(self):
        return {
            'sku': self.sku,
            'length': self.length,
            'width': self.width,
            'height': self.height,
            'weight': self.weight
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            sku=data['sku'],
            length=data['length'],
            width=data['width'],
            height=data['height'],
            weight=data['weight']
        )
    
    def fits_in_position(self, position, fixed_length, clearance=0.0):
        """Check if this item fits in the given position type with clearance."""
        return (self.length <= fixed_length and
                self.width <= position.width_capacity and
                self.height <= position.max_height - clearance and
                self.weight <= position.weight_capacity)

# Core assignment function with improvements
def assign_pallets(fixed_length, position_types, items, clearance=4.0):
    """
    Assign items to appropriate pallet positions.
    
    Parameters:
    - fixed_length (float): The fixed length for all pallet positions.
    - position_types (list): List of PositionType objects.
    - items (list): List of Item objects.
    - clearance (float): Required height clearance in inches (default: 4.0).
    
    Returns:
    - assignments (dict): Counts of items assigned to each position type.
    - unassigned_items (list): SKUs of items that couldn’t be assigned.
    - item_assignments (list): List of dicts with item SKU and assigned position.
    """
    # Input validation
    if fixed_length <= 0:
        raise ValueError("Fixed length must be positive.")
    if clearance < 0:
        raise ValueError("Clearance cannot be negative.")
    for pos in position_types:
        if pos.max_height <= 0 or pos.width_capacity <= 0 or pos.weight_capacity <= 0:
            raise ValueError("Position capacities must be positive.")
    for item in items:
        if item.length <= 0 or item.width <= 0 or item.height <= 0 or item.weight <= 0:
            raise ValueError("Item dimensions and weight must be positive.")
    
    # Initialize tracking structures
    assignments = {}  # Format: 'Aisle A Level 1': count
    unassigned_items = []
    item_assignments = []
    
    # Sort position types by max_height (ascending) to optimize assignments
    sorted_positions = sorted(position_types, key=lambda p: p.max_height)
    
    # Process each item
    for item in items:
        assigned = False
        for position in sorted_positions:
            position_key = f"Aisle {position.aisle} Level {position.level}"
            # Use fits_in_position method with clearance
            if item.fits_in_position(position, fixed_length, clearance):
                # Update assignments count
                assignments[position_key] = assignments.get(position_key, 0) + 1
                # Record individual assignment
                item_assignments.append({
                    'sku': item.sku,
                    'assigned_to': position_key
                })
                assigned = True
                break
        
        if not assigned:
            unassigned_items.append(item.sku)
    
    return assignments, unassigned_items, item_assignments

# Streamlit app setup
st.set_page_config(page_title="Warehouse Pallet Position Calculator", layout="wide")

# Example UI (since original UI was incomplete)
st.title("Pallet Position Assignment Tool")

# Input for fixed length
fixed_length = st.number_input("Fixed Length (inches)", min_value=0.1, value=48.0)

# Placeholder for position types input
st.subheader("Position Types")
position_data = st.data_editor(
    pd.DataFrame({
        'Aisle': ['A', 'B'],
        'Level': [1, 1],
        'Max Height': [50.0, 60.0],
        'Width Capacity': [40.0, 40.0],
        'Weight Capacity': [2000.0, 2500.0]
    }),
    num_rows="dynamic"
)

# Placeholder for items input
st.subheader("Items")
item_data = st.data_editor(
    pd.DataFrame({
        'SKU': ['SKU001', 'SKU002'],
        'Length': [48.0, 48.0],
        'Width': [36.0, 38.0],
        'Height': [45.0, 55.0],
        'Weight': [1500.0, 1800.0]
    }),
    num_rows="dynamic"
)

if st.button("Assign Pallets"):
    # Convert input data to objects
    position_types = [
        PositionType(row['Aisle'], row['Level'], row['Max Height'], 
                    row['Width Capacity'], row['Weight Capacity'])
        for _, row in position_data.iterrows()
    ]
    items = [
        Item(row['SKU'], row['Length'], row['Width'], row['Height'], row['Weight'])
        for _, row in item_data.iterrows()
    ]
    
    # Run assignment
    try:
        assignments, unassigned_items, item_assignments = assign_pallets(
            fixed_length, position_types, items
        )
        
        # Display results
        st.subheader("Assignments")
        st.write(assignments)
        
        st.subheader("Unassigned Items")
        st.write(unassigned_items)
        
        st.subheader("Detailed Item Assignments")
        st.dataframe(item_assignments)
    except ValueError as e:
        st.error(f"Error: {e}")