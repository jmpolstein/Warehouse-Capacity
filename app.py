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
        
    def fits_in_position(self, position, fixed_length):
        """Check if this item fits in the given position type"""
        return (self.height <= position.max_height and
                self.width <= position.width_capacity * fixed_length and
                self.length <= fixed_length and
                self.weight <= position.weight_capacity)

st.set_page_config(page_title="Warehouse Pallet Position Calculator", layout="wide")

# Title and introduction
st.title("Warehouse Pallet Position Calculator")
st.write("Calculate required pallet positions based on inventory items and position types")

# Sidebar for global settings
with st.sidebar:
    st.header("Global Settings")
    fixed_length = st.number_input("Fixed Length of All Pallet Positions (in inches)", 
                                 min_value=0.0, value=48.0, step=1.0)
    # Convert inches to meters for internal calculations (if needed)
    fixed_length_meters = fixed_length * 0.0254

# Main content divided into tabs
tab1, tab2, tab3 = st.tabs(["Define Pallet Positions", "Enter Inventory Items", "View Results"])

# Tab 1: Define Pallet Position Types
with tab1:
    st.header("Pallet Position Types")
    st.write("Define the different types of pallet positions in your warehouse")
    
    # Input for number of position types
    num_position_types = st.number_input("Number of position types", min_value=1, value=2, step=1)
    
    # Initialize session state for position types if not already done
    if 'position_types' not in st.session_state:
        # Create initial position types
        st.session_state.position_types = [
            PositionType('A', '1', 1.0, 1.0, 1000),
            PositionType('B', '2', 2.0, 0.8, 500)
        ]
    
    # Adjust length of position_types list based on num_position_types
    while len(st.session_state.position_types) < num_position_types:
        st.session_state.position_types.append(PositionType('', '1', 1.0, 1.0, 1000))
    
    if len(st.session_state.position_types) > num_position_types:
        st.session_state.position_types = st.session_state.position_types[:num_position_types]
    
    # Create input fields for each position type
    with st.form("position_types_form"):
        st.subheader("Define Each Position Type")
        
        updated_position_types = []
        
        for i in range(num_position_types):
            pos = st.session_state.position_types[i]
            st.markdown(f"### Position Type #{i+1}")
            
            col1, col2 = st.columns(2)
            with col1:
                aisle = st.text_input(f"Aisle #{i+1}", value=pos.aisle, key=f"aisle_{i}")
            with col2:
                level = st.text_input(f"Level #{i+1}", value=pos.level, key=f"level_{i}")
                
            col1, col2, col3 = st.columns(3)
            with col1:
                max_height = st.number_input(f"Max Height #{i+1} (inches)", 
                                           min_value=0.0, value=float(pos.max_height), key=f"height_{i}")
            with col2:
                width_capacity = st.number_input(f"Width Capacity #{i+1} (inches)", 
                                               min_value=0.0, value=float(pos.width_capacity), key=f"width_{i}")
            with col3:
                weight_capacity = st.number_input(f"Weight Capacity #{i+1} (lbs)", 
                                                min_value=0.0, value=float(pos.weight_capacity), key=f"weight_{i}")
            
            # Create a new PositionType object with the updated values
            updated_position_types.append(
                PositionType(aisle, level, max_height, width_capacity, weight_capacity)
            )
            
            st.divider()
        
        # Add a submit button to save the position types
        if st.form_submit_button("Save Position Types"):
            st.session_state.position_types = updated_position_types
            
            # Also update the pallet_positions DataFrame for compatibility with other parts of the app
            st.session_state.pallet_positions = pd.DataFrame([p.to_dict() for p in updated_position_types])
            
            st.success("Position types saved successfully!")

# Tab 2: Enter Inventory Items
with tab2:
    st.header("Inventory Items")
    st.write("Enter details for each inventory item that needs to be stored")
    
    # Input for number of inventory items
    num_inventory_items = st.number_input("Number of inventory items", min_value=1, value=2, step=1)
    
    # Initialize session state for inventory items if not already done
    if 'inventory_items_list' not in st.session_state:
        # Create initial inventory items
        st.session_state.inventory_items_list = [
            Item('SKU001', 0.8, 0.6, 0.5, 300),
            Item('SKU002', 1.0, 0.8, 1.5, 700)
        ]
    
    # Adjust length of inventory_items_list based on num_inventory_items
    while len(st.session_state.inventory_items_list) < num_inventory_items:
        st.session_state.inventory_items_list.append(Item('SKU000', 0.8, 0.6, 1.0, 500))
    
    if len(st.session_state.inventory_items_list) > num_inventory_items:
        st.session_state.inventory_items_list = st.session_state.inventory_items_list[:num_inventory_items]
    
    # Create input fields for each inventory item
    with st.form("inventory_items_form"):
        st.subheader("Define Each Inventory Item")
        
        updated_inventory_items = []
        
        for i in range(num_inventory_items):
            item = st.session_state.inventory_items_list[i]
            st.markdown(f"### Item #{i+1}")
            
            # SKU input
            sku = st.text_input(f"SKU #{i+1}", value=item.sku, key=f"sku_{i}")
            
            # Create 3 columns for dimension inputs
            col1, col2, col3 = st.columns(3)
            with col1:
                length = st.number_input(f"Length #{i+1} (inches)", 
                                       min_value=0.0, value=float(item.length), key=f"item_length_{i}")
            with col2:
                width = st.number_input(f"Width #{i+1} (inches)", 
                                      min_value=0.0, value=float(item.width), key=f"item_width_{i}")
            with col3:
                height = st.number_input(f"Height #{i+1} (inches)", 
                                       min_value=0.0, value=float(item.height), key=f"item_height_{i}")
            
            # Weight input
            weight = st.number_input(f"Weight #{i+1} (lbs)", 
                                   min_value=0.0, value=float(item.weight), key=f"item_weight_{i}")
            
            # Create a new Item object with the updated values
            updated_inventory_items.append(
                Item(sku, length, width, height, weight)
            )
            
            st.divider()
        
        # Add a submit button to save the inventory items
        if st.form_submit_button("Save Inventory Items"):
            st.session_state.inventory_items_list = updated_inventory_items
            
            # Also update the inventory_items DataFrame for compatibility with other parts of the app
            st.session_state.inventory_items = pd.DataFrame([item.to_dict() for item in updated_inventory_items])
            
            st.success("Inventory items saved successfully!")

# Tab 3: Calculate and Display Results
with tab3:
    st.header("Results")
    st.write("Calculated pallet positions required for your inventory")
    
    # Changed button label to just 'Calculate'
    if st.button("Calculate"):
        # Ensure we have data to work with
        if 'position_types' not in st.session_state or 'inventory_items_list' not in st.session_state:
            st.error("Please define pallet positions and inventory items first!")
        else:
            # Use the assign_pallets function with user-provided data
            position_types = st.session_state.position_types
            items = st.session_state.inventory_items_list
            
            # Call the assign_pallets function
            assignments, unassigned_item_skus, item_assignments = assign_pallets(
                fixed_length, position_types, items
            )
            
            # Display results - Required Pallet Positions
            st.subheader("Required Pallet Positions")
            
            # Format and display each position type with count
            for position_type in position_types:
                position_key = f"Aisle {position_type.aisle} Level {position_type.level}"
                count = assignments.get(position_key, 0)
                st.write(f"Position Type {position_key}: {count} positions")
            
            # Display unassigned items with full details
            if unassigned_item_skus:
                st.subheader("Unassigned Items")
                
                # Find the full item details for each unassigned SKU
                unassigned_items = [item for item in items if item.sku in unassigned_item_skus]
                
                for item in unassigned_items:
                    st.write(f"Unassigned Item - SKU: {item.sku}, Length: {item.length}, Width: {item.width}, Height: {item.height}, Weight: {item.weight}")
                
                st.info("These items may be too large, too heavy, or require more than the available clearance in any defined pallet position.")
            else:
                st.subheader("Assignment Status")
                st.success("All items assigned successfully")
    else:
        st.info("Click the Calculate button above to determine required pallet positions based on your inventory items")

# Footer
st.divider()
st.write("© 2023 Warehouse Pallet Position Calculator")

def assign_pallets(fixed_length, position_types, items):
    """
    Assign items to appropriate pallet positions.
    
    Parameters:
    - fixed_length: float, the fixed length for all pallet positions
    - position_types: list of PositionType objects
    - items: list of Item objects
    
    Returns:
    - assignments: dict, counts of items assigned to each position type
    - unassigned_items: list, items that couldn't be assigned anywhere
    - item_assignments: list of dicts, details of where each item is assigned
    """
    # Initialize tracking structures
    assignments = {}  # Format: 'Aisle A Level 1': count
    unassigned_items = []
    item_assignments = []  # List of dictionaries with item SKU and assigned position
    
    # Sort position types by max_height (ascending) to optimize assignments
    # This ensures we try to fit items in the smallest suitable position first
    sorted_positions = sorted(position_types, key=lambda p: p.max_height)
    
    # Process each item
    for item in items:
        assigned = False
        
        # Check each position type (already sorted by max_height)
        for position in sorted_positions:
            # Create position key
            position_key = f"Aisle {position.aisle} Level {position.level}"
            
            # Check all constraints with 4-inch clearance for height
            if (item.length <= fixed_length and
                item.width <= position.width_capacity and
                item.height <= position.max_height - 4 and  # 4-inch clearance
                item.weight <= position.weight_capacity):
                
                # Add to assignments count
                if position_key not in assignments:
                    assignments[position_key] = 0
                assignments[position_key] += 1
                
                # Record individual item assignment
                item_assignments.append({
                    'sku': item.sku,
                    'assigned_to': position_key
                })
                
                assigned = True
                break  # Move to next item once assigned
        
        # If no suitable position found
        if not assigned:
            unassigned_items.append(item.sku)
    
    return assignments, unassigned_items, item_assignments 