"""
Tools for the House Design Agent System

This module contains utility functions for budget calculations and floorplan management
that will be used by the various agents in the LangGraph workflow.
"""

from typing import List, Dict, Any, Optional


def calculate_construction_cost(total_sqft: float) -> float:
    """
    Calculate the total construction cost based on square footage using Montreal pricing.
    
    Uses a mock cost of $350 per square foot which represents typical construction
    costs in the Montreal area for residential buildings.
    
    Args:
        total_sqft (float): Total square footage of the construction project
        
    Returns:
        float: Total estimated construction cost in Canadian dollars
        
    Example:
        >>> calculate_construction_cost(2000.0)
        700000.0
    """
    return total_sqft * 350.0


def add_room(floorplan: List[Dict[str, Any]], room_name: str, room_type: str, 
             length_ft: float, width_ft: float) -> List[Dict[str, Any]]:
    """
    Add a new room to the floorplan with calculated area.
    
    Creates a new room dictionary with the provided dimensions and adds it to the
    existing floorplan list. The area is automatically calculated from length and width.
    
    Args:
        floorplan (List[Dict]): Current list of room dictionaries
        room_name (str): Name/identifier for the new room (e.g., "Living Room")
        room_type (str): Type/category of room (e.g., "bedroom", "bathroom", "kitchen")
        length_ft (float): Length of the room in feet
        width_ft (float): Width of the room in feet
        
    Returns:
        List[Dict]: Updated floorplan list including the new room
        
    Example:
        >>> floorplan = []
        >>> updated = add_room(floorplan, "Living Room", "living", 16.0, 20.0)
        >>> len(updated)
        1
        >>> updated[0]['area_sqft']
        320.0
    """
    area_sqft = length_ft * width_ft
    
    new_room = {
        'name': room_name,
        'type': room_type,
        'length_ft': length_ft,
        'width_ft': width_ft,
        'area_sqft': area_sqft
    }
    
    # Create a copy of the floorplan to avoid modifying the original
    updated_floorplan = floorplan.copy()
    updated_floorplan.append(new_room)
    
    return updated_floorplan


def remove_room(floorplan: List[Dict[str, Any]], room_name: str) -> List[Dict[str, Any]]:
    """
    Remove a room from the floorplan by name.
    
    Searches for a room with the specified name and removes it from the floorplan.
    If the room is not found, returns the original floorplan unchanged.
    
    Args:
        floorplan (List[Dict]): Current list of room dictionaries
        room_name (str): Name of the room to remove
        
    Returns:
        List[Dict]: Updated floorplan list with the specified room removed,
                   or original list if room not found
                   
    Example:
        >>> floorplan = [{'name': 'Living Room', 'type': 'living', 'area_sqft': 320.0}]
        >>> updated = remove_room(floorplan, "Living Room")
        >>> len(updated)
        0
    """
    updated_floorplan = []
    
    for room in floorplan:
        if room.get('name') != room_name:
            updated_floorplan.append(room)
    
    return updated_floorplan


def update_room(floorplan: List[Dict[str, Any]], room_name: str, 
                new_length_ft: float, new_width_ft: float) -> List[Dict[str, Any]]:
    """
    Update the dimensions of an existing room in the floorplan.
    
    Finds the room with the specified name and updates its length, width, and
    recalculates the area. If the room is not found, returns the original floorplan.
    
    Args:
        floorplan (List[Dict]): Current list of room dictionaries
        room_name (str): Name of the room to update
        new_length_ft (float): New length in feet
        new_width_ft (float): New width in feet
        
    Returns:
        List[Dict]: Updated floorplan list with modified room dimensions,
                   or original list if room not found
                   
    Example:
        >>> floorplan = [{'name': 'Bedroom', 'length_ft': 10, 'width_ft': 12, 'area_sqft': 120}]
        >>> updated = update_room(floorplan, "Bedroom", 14.0, 16.0)
        >>> updated[0]['area_sqft']
        224.0
    """
    updated_floorplan = []
    
    for room in floorplan:
        if room.get('name') == room_name:
            # Create updated room with new dimensions
            updated_room = room.copy()
            updated_room['length_ft'] = new_length_ft
            updated_room['width_ft'] = new_width_ft
            updated_room['area_sqft'] = new_length_ft * new_width_ft
            updated_floorplan.append(updated_room)
        else:
            updated_floorplan.append(room)
    
    return updated_floorplan


def summarize_floorplan(floorplan: List[Dict[str, Any]], total_sqft: float, 
                       estimated_cost: float, user_budget: Optional[float] = None) -> str:
    """
    Generate a formatted summary of the current floorplan with budget analysis.
    
    Creates a professional-looking summary similar to architectural draft plans,
    including room details, total area, cost estimates, and budget comparison.
    
    Args:
        floorplan (List[Dict]): List of room dictionaries
        total_sqft (float): Total square footage of all rooms
        estimated_cost (float): Estimated construction cost
        user_budget (Optional[float]): User's budget for comparison, if available
        
    Returns:
        str: Formatted floorplan summary with room details and budget analysis
        
    Example:
        >>> rooms = [{'name': 'Living Room', 'length_ft': 16, 'width_ft': 20, 'area_sqft': 320}]
        >>> summary = summarize_floorplan(rooms, 320.0, 112000.0, 150000.0)
        >>> "Living room: 16' × 20'" in summary
        True
    """
    if not floorplan:
        return "❌ **No rooms in current floorplan**"
    
    # Calculate floors estimate (assuming average 1000 sq ft per floor)
    estimated_floors = max(1, round(total_sqft / 1000))
    avg_sqft_per_floor = total_sqft / estimated_floors
    
    # Start building the summary
    summary = "✅ **Draft Floorplan v1 (simulation)**\n"
    summary += f"- Floors: {estimated_floors}\n"
    summary += f"- Total area: {total_sqft:,.0f} ft²"
    
    if estimated_floors > 1:
        summary += f" (approx. {avg_sqft_per_floor:,.0f} ft² per floor)"
    
    summary += "\n"
    
    # Add lot shape estimate (rough calculation for visualization)
    lot_width = int((total_sqft / estimated_floors) ** 0.5 * 1.2)  # Rough estimate
    lot_depth = int(total_sqft / estimated_floors / lot_width * 2.5)  # Rough estimate
    summary += f"- Lot shape: {lot_width}' × {lot_depth}' rectangle\n"
    
    # Add rooms section
    summary += "- Rooms:\n"
    
    # Group rooms by type for better organization
    room_types = {}
    for room in floorplan:
        room_type = room.get('type', 'other')
        if room_type not in room_types:
            room_types[room_type] = []
        room_types[room_type].append(room)
    
    # Display rooms in a logical order - include ALL room types
    type_order = ['living', 'kitchen', 'dining', 'bedroom', 'bathroom', 'office', 'garage', 'laundry', 'other']
    
    # First, display rooms in the preferred order
    for room_type in type_order:
        if room_type in room_types:
            for room in room_types[room_type]:
                room_name = room.get('name', 'Unknown Room')
                length = room.get('length_ft', 0)
                width = room.get('width_ft', 0)
                
                # Format room name for display (keep original case for proper nouns)
                display_name = room_name
                
                summary += f"  - {display_name}: {length}' × {width}'\n"
    
    # Then display any room types not in our predefined order
    for room_type, rooms in room_types.items():
        if room_type not in type_order:
            for room in rooms:
                room_name = room.get('name', 'Unknown Room')
                length = room.get('length_ft', 0)
                width = room.get('width_ft', 0)
                
                summary += f"  - {room_name}: {length}' × {width}'\n"
    
    # Add cost analysis
    summary += f"\n💰 **Budget Analysis:**\n"
    summary += f"- Estimated cost: ${estimated_cost:,.2f}\n"
    summary += f"- Cost per sq ft: ${estimated_cost/total_sqft:.2f}\n"
    
    if user_budget:
        budget_status = "✅ Within budget" if estimated_cost <= user_budget else "⚠️ Over budget"
        difference = abs(estimated_cost - user_budget)
        summary += f"- Your budget: ${user_budget:,.2f}\n"
        summary += f"- Status: {budget_status}\n"
        
        if estimated_cost > user_budget:
            summary += f"- Over by: ${difference:,.2f} ({((estimated_cost - user_budget) / user_budget * 100):.1f}%)\n"
        else:
            summary += f"- Under by: ${difference:,.2f} ({((user_budget - estimated_cost) / user_budget * 100):.1f}%)\n"
    
    return summary


def get_total_area(floorplan: List[Dict[str, Any]]) -> float:
    """
    Calculate the total area of all rooms in the floorplan.
    
    Utility function to sum up the area_sqft of all rooms in the floorplan.
    
    Args:
        floorplan (List[Dict]): List of room dictionaries
        
    Returns:
        float: Total area in square feet
        
    Example:
        >>> rooms = [{'area_sqft': 320}, {'area_sqft': 150}]
        >>> get_total_area(rooms)
        470.0
    """
    return sum(room.get('area_sqft', 0) for room in floorplan)


def validate_room_data(room_name: str, room_type: str, length_ft: float, width_ft: float) -> bool:
    """
    Validate room data before adding to floorplan.
    
    Checks if the provided room data is valid and reasonable for construction.
    
    Args:
        room_name (str): Name of the room
        room_type (str): Type of the room
        length_ft (float): Length in feet
        width_ft (float): Width in feet
        
    Returns:
        bool: True if room data is valid, False otherwise
        
    Example:
        >>> validate_room_data("Living Room", "living", 16.0, 20.0)
        True
        >>> validate_room_data("", "living", -5.0, 20.0)
        False
    """
    if not room_name or not room_name.strip():
        return False
    
    if not room_type or not room_type.strip():
        return False
    
    if length_ft <= 0 or width_ft <= 0:
        return False
    
    # Check for reasonable room sizes (between 4ft and 50ft for each dimension)
    if length_ft < 4 or length_ft > 50 or width_ft < 4 or width_ft > 50:
        return False
    
    return True