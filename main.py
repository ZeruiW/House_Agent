import os
import json
from typing import Dict, List, Any, Optional, Literal
from dataclasses import dataclass, field
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from typing_extensions import TypedDict

# Import tools from our tools.py module
from tools import (
    calculate_construction_cost,
    add_room,
    remove_room,
    update_room,
    summarize_floorplan,
    get_total_area
)

load_dotenv()

class AppState(TypedDict):
    conversation_history: List[str]
    floorplan: List[Dict[str, Any]]  # List of room dictionaries from tools.py
    total_sqft: float
    estimated_cost: Optional[float]
    user_budget: Optional[float]
    final_response: str
    last_message: str
    user_intent: str
    next_action: str  # Added for router functionality

# Initialize OpenAI model
llm = ChatOpenAI(model="gpt-4o", temperature=0.1)

# Node function implementations
def floorplan_architect_node(state: AppState) -> Dict[str, Any]:
    """Process floorplan modifications using LLM decision-making and tools."""
    history = "\n".join(state.get('conversation_history', []))
    current_floorplan = state.get('floorplan', [])
    last_message = state.get('last_message', '')
    user_budget = state.get('user_budget', 0)
    
    # Create floorplan summary for context
    floorplan_summary = "Empty floorplan"
    current_total_area = 0
    if current_floorplan:
        current_total_area = get_total_area(current_floorplan)
        floorplan_summary = summarize_floorplan(current_floorplan, current_total_area, 0, 0)
    
    budget_display = f"${user_budget:,.2f}" if user_budget else "Not set"
    
    prompt = f"""You are an expert Floorplan Architect. Your task is to interpret the user's request and create/modify floorplans with reasonable dimensions.

CONTEXT:
Conversation History: {history}
Current Floorplan: {floorplan_summary}
Current Total Area: {current_total_area} sq ft
User's Budget: {budget_display}
User Request: {last_message}

ROOM SIZE GUIDELINES (reasonable dimensions):
- Master Bedroom: 12x14 to 16x18 ft (168-288 sq ft)
- Regular Bedroom: 10x12 to 12x14 ft (120-168 sq ft)
- Living Room: 14x16 to 20x24 ft (224-480 sq ft)
- Kitchen: 10x12 to 14x16 ft (120-224 sq ft)
- Dining Room: 10x12 to 14x16 ft (120-224 sq ft)
- Bathroom: 5x8 to 8x10 ft (40-80 sq ft)
- Master Bathroom: 8x10 to 10x12 ft (80-120 sq ft)
- Garage (1-car): 12x20 ft (240 sq ft)
- Garage (2-car): 20x20 ft (400 sq ft)
- Garage (3-car): 30x20 ft (600 sq ft)
- Office/Study: 10x10 to 12x14 ft (100-168 sq ft)
- Laundry: 6x8 to 8x10 ft (48-80 sq ft)

COMPLEX REQUEST HANDLING:
If the user asks for:
- "Add another floor" or "second floor" or "three floor house" - add multiple rooms appropriate for additional floors
- "Add several rooms" or "add 2 more office rooms" - add multiple rooms in one response  
- "Redesign" or "start over" or "build a new house" - provide a complete new floorplan
- "Make it bigger" without specifying what - increase the largest room or add complementary rooms
- Complete house requests like "three floor house with X bedrooms, Y bathrooms" - design entire house layout

For requests like "add 2 more office rooms" or "add 3 bedrooms":
- Parse the number and room type
- Create multiple rooms with reasonable variations in size
- Use sequential naming (Office 2, Office 3, etc.)

For complete house design requests, distribute rooms logically across floors:
- First floor: Living room, kitchen, dining room, guest bathroom, garage
- Second floor: Master bedroom, master bathroom, additional bedrooms  
- Third floor: Office, additional bedrooms, storage spaces

Your response should be a JSON object with ONE of these formats:

SINGLE ROOM ACTION:
{{
    "action": "add_room|remove_room|update_room",
    "room_name": "Room Name",
    "room_type": "bedroom|bathroom|kitchen|living|dining|garage|office|laundry|other", 
    "length_ft": 12.0,
    "width_ft": 10.0,
    "new_length_ft": 14.0,  // for update_room only
    "new_width_ft": 12.0    // for update_room only
}}

MULTIPLE ROOMS ACTION (for "add 2 more office rooms" etc.):
{{
    "action": "add_multiple_rooms",
    "rooms": [
        {{"room_name": "Office 2", "room_type": "office", "length_ft": 12.0, "width_ft": 14.0}},
        {{"room_name": "Office 3", "room_type": "office", "length_ft": 10.0, "width_ft": 12.0}}
    ]
}}

COMPLETE REDESIGN (for full house design requests):
{{
    "action": "redesign_complete",
    "target_sqft": 3000,
    "rooms": [
        // First Floor
        {{"room_name": "Living Room", "room_type": "living", "length_ft": 18.0, "width_ft": 22.0}},
        {{"room_name": "Kitchen", "room_type": "kitchen", "length_ft": 12.0, "width_ft": 14.0}},
        {{"room_name": "Dining Room", "room_type": "dining", "length_ft": 12.0, "width_ft": 14.0}},
        {{"room_name": "Guest Bath", "room_type": "bathroom", "length_ft": 6.0, "width_ft": 8.0}},
        {{"room_name": "2-Car Garage", "room_type": "garage", "length_ft": 20.0, "width_ft": 20.0}},
        // Second Floor  
        {{"room_name": "Master Bedroom", "room_type": "bedroom", "length_ft": 14.0, "width_ft": 16.0}},
        {{"room_name": "Master Bath", "room_type": "bathroom", "length_ft": 8.0, "width_ft": 10.0}},
        {{"room_name": "Bedroom 2", "room_type": "bedroom", "length_ft": 12.0, "width_ft": 14.0}},
        {{"room_name": "Bedroom 3", "room_type": "bedroom", "length_ft": 10.0, "width_ft": 12.0}},
        {{"room_name": "Main Bath", "room_type": "bathroom", "length_ft": 8.0, "width_ft": 10.0}},
        // Third Floor
        {{"room_name": "Office", "room_type": "office", "length_ft": 12.0, "width_ft": 14.0}}
    ]
}}

Use reasonable dimensions based on the guidelines above. Consider the user's budget if provided."""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        # Clean the response content to extract JSON
        response_text = response.content.strip()
        
        # Sometimes LLM adds extra text, try to extract just the JSON part
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_text = response_text[json_start:json_end]
            # Clean up any comments in JSON
            import re
            json_text = re.sub(r'//.*?\n', '\n', json_text)
            decision = json.loads(json_text)
        else:
            decision = json.loads(response_text)
        
        updated_floorplan = current_floorplan.copy()
        
        if decision["action"] == "add_room":
            updated_floorplan = add_room(
                updated_floorplan,
                decision["room_name"],
                decision["room_type"],
                decision["length_ft"],
                decision["width_ft"]
            )
        elif decision["action"] == "remove_room":
            updated_floorplan = remove_room(updated_floorplan, decision["room_name"])
        elif decision["action"] == "update_room":
            updated_floorplan = update_room(
                updated_floorplan,
                decision["room_name"],
                decision["new_length_ft"],
                decision["new_width_ft"]
            )
        elif decision["action"] == "add_multiple_rooms":
            for room_data in decision["rooms"]:
                updated_floorplan = add_room(
                    updated_floorplan,
                    room_data["room_name"],
                    room_data["room_type"],
                    room_data["length_ft"],
                    room_data["width_ft"]
                )
        elif decision["action"] == "redesign_complete":
            # Clear existing floorplan and add new rooms
            updated_floorplan = []
            for room_data in decision["rooms"]:
                updated_floorplan = add_room(
                    updated_floorplan,
                    room_data["room_name"],
                    room_data["room_type"],
                    room_data["length_ft"],
                    room_data["width_ft"]
                )
        
        # Generate immediate response with updated floorplan
        if updated_floorplan:
            total_area = get_total_area(updated_floorplan)
            estimated_cost = calculate_construction_cost(total_area)
            user_budget = state.get('user_budget')
            
            # Create a brief acknowledgment with floorplan update
            floorplan_summary = summarize_floorplan(updated_floorplan, total_area, estimated_cost, user_budget)
            
            response_msg = f"✅ **Floorplan Updated Successfully!**\n\n{floorplan_summary}"
            
            return {
                "floorplan": updated_floorplan,
                "total_sqft": total_area,
                "estimated_cost": estimated_cost,
                "final_response": response_msg
            }
        else:
            return {"floorplan": updated_floorplan}
        
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        # If JSON parsing fails, try to create a simple fallback based on the request
        print(f"Debug: JSON parsing failed: {e}")
        print(f"Debug: LLM response was: {response.content}")
        
        # Simple fallback for complex requests
        if "three floor" in last_message.lower() and "bedroom" in last_message.lower():
            # Create a basic three-floor house
            fallback_rooms = [
                {"room_name": "Living Room", "room_type": "living", "length_ft": 18.0, "width_ft": 22.0},
                {"room_name": "Kitchen", "room_type": "kitchen", "length_ft": 12.0, "width_ft": 14.0},
                {"room_name": "2-Car Garage", "room_type": "garage", "length_ft": 20.0, "width_ft": 20.0},
                {"room_name": "Guest Bath", "room_type": "bathroom", "length_ft": 6.0, "width_ft": 8.0},
                {"room_name": "Master Bedroom", "room_type": "bedroom", "length_ft": 14.0, "width_ft": 16.0},
                {"room_name": "Master Bath", "room_type": "bathroom", "length_ft": 8.0, "width_ft": 10.0},
                {"room_name": "Bedroom 2", "room_type": "bedroom", "length_ft": 12.0, "width_ft": 14.0},
                {"room_name": "Bedroom 3", "room_type": "bedroom", "length_ft": 10.0, "width_ft": 12.0},
                {"room_name": "Office", "room_type": "office", "length_ft": 12.0, "width_ft": 14.0},
            ]
            
            updated_floorplan = []
            for room_data in fallback_rooms:
                updated_floorplan = add_room(
                    updated_floorplan,
                    room_data["room_name"],
                    room_data["room_type"],
                    room_data["length_ft"],
                    room_data["width_ft"]
                )
            
            # Generate response for fallback floorplan too
            total_area = get_total_area(updated_floorplan) 
            estimated_cost = calculate_construction_cost(total_area)
            user_budget = state.get('user_budget')
            
            floorplan_summary = summarize_floorplan(updated_floorplan, total_area, estimated_cost, user_budget)
            response_msg = f"✅ **Floorplan Created Successfully!**\n\n{floorplan_summary}"
            
            return {
                "floorplan": updated_floorplan,
                "total_sqft": total_area,
                "estimated_cost": estimated_cost,
                "final_response": response_msg
            }
        
        # Fallback to original floorplan
        return {"floorplan": current_floorplan}


def budget_analyst_node(state: AppState) -> Dict[str, Any]:
    """Calculate total square footage and estimated cost."""
    floorplan = state.get('floorplan', [])
    
    if not floorplan:
        return {
            "total_sqft": 0.0,
            "estimated_cost": 0.0
        }
    
    total_sqft = get_total_area(floorplan)
    estimated_cost = calculate_construction_cost(total_sqft)
    
    return {
        "total_sqft": total_sqft,
        "estimated_cost": estimated_cost
    }


def constraint_solver_node(state: AppState) -> Dict[str, Any]:
    """Generate specific budget reduction suggestions."""
    floorplan = state.get('floorplan', [])
    estimated_cost = state.get('estimated_cost', 0)
    user_budget = state.get('user_budget', 0)
    
    if not user_budget or not estimated_cost:
        return {"final_response": "Insufficient budget data for constraint solving."}
    
    deficit = estimated_cost - user_budget
    total_sqft = get_total_area(floorplan)
    
    # Create detailed floorplan summary
    floorplan_summary = summarize_floorplan(floorplan, total_sqft, estimated_cost, user_budget)
    
    prompt = f"""You are a professional home design consultant helping a client reduce costs. 

IMPORTANT RESPONSE STYLE:
- Speak naturally and conversationally, as if consulting face-to-face
- NEVER use email formatting (no "Dear", "Best regards", signatures, etc.)
- Be supportive and solution-focused
- Present options clearly with specific cost savings
- Use friendly, professional tone

SITUATION:
Current design cost: ${estimated_cost:,.2f}
Client's budget: ${user_budget:,.2f} 
Amount over budget: ${deficit:,.2f}

Current floorplan:
{floorplan_summary}

TASK: Provide 2-3 specific, actionable suggestions to reduce costs. Make each suggestion clear with:
- What to change
- Approximate cost savings
- Impact on the design

Be encouraging and present these as practical options to explore together."""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    return {"final_response": response.content}


def design_consultant_node(state: AppState) -> Dict[str, Any]:
    """Answer general design questions."""
    history = "\n".join(state.get('conversation_history', []))
    last_message = state.get('last_message', '')
    
    prompt = f"""You are a professional residential design consultant specializing in Montreal home construction. 

IMPORTANT RESPONSE STYLE:
- Always respond as a helpful, knowledgeable home design professional
- Use conversational, friendly tone but remain professional
- NEVER use email formatting (no "Dear...", "Best regards", "Sincerely", etc.)
- NEVER include email signatures or contact information
- Focus on practical, actionable advice
- Use bullet points and clear structure when helpful

User's Question: {last_message}

Conversation Context: {history}

Provide helpful, practical advice about:
- Design styles and aesthetics
- Building materials and finishes
- Montreal/Quebec building codes and regulations
- Construction best practices
- Cost-effective solutions
- Regional climate considerations

Respond naturally as if you're having a face-to-face consultation with a client."""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    
    return {"final_response": response.content}


def response_generation_node(state: AppState) -> Dict[str, Any]:
    """Generate final response when cost is within budget."""
    floorplan = state.get('floorplan', [])
    total_sqft = state.get('total_sqft', 0)
    estimated_cost = state.get('estimated_cost', 0)
    user_budget = state.get('user_budget')
    
    if not floorplan:
        return {"final_response": "No floorplan available to summarize."}
    
    summary = summarize_floorplan(floorplan, total_sqft, estimated_cost, user_budget)
    
    return {"final_response": summary}

def project_manager_router(state: AppState) -> Dict[str, Any]:
    """Router function to classify user intent and determine next action."""
    last_message = state.get('last_message', '')
    floorplan = state.get('floorplan', [])
    user_budget = state.get('user_budget')
    
    # Check if user is setting budget and extract it
    budget_keywords = ['budget', 'afford', 'spend', '$', 'dollar', 'cost limit', 'max cost']
    is_budget_message = any(keyword in last_message.lower() for keyword in budget_keywords)
    
    extracted_budget = None
    if is_budget_message:
        # Try to extract budget amount from message
        import re
        # Look for dollar amounts like $500,000 or 500000 or 500k or 800000 CAD
        budget_patterns = [
            r'\$[\d,]+',  # $500,000
            r'(\d+)k',    # 500k  
            r'(\d{6,7})\s*(?:CAD|USD|\$|dollars?)?',  # 800000 CAD or 500000
            r'(\d+),(\d{3})',  # 500,000
        ]
        
        for pattern in budget_patterns:
            matches = re.findall(pattern, last_message)
            if matches:
                try:
                    if 'k' in pattern:
                        extracted_budget = float(matches[0]) * 1000
                    elif '6,7' in pattern:  # 6-7 digit pattern for 800000 CAD
                        extracted_budget = float(matches[0])
                    elif isinstance(matches[0], tuple):  # comma separated like (500, 000)
                        amount_str = ''.join(matches[0])
                        extracted_budget = float(amount_str)
                    else:
                        # Clean up the match and convert
                        amount_str = matches[0] if isinstance(matches[0], str) else str(matches[0])
                        amount_str = amount_str.replace('$', '').replace(',', '')
                        extracted_budget = float(amount_str)
                    break
                except:
                    continue
    
    budget_display = f"${user_budget:,.2f}" if user_budget else "Not set"
    
    prompt = f"""As a Project Manager, analyze the user's message and classify it into one of these categories:

Categories:
- modify_floorplan: User wants to add, remove, change rooms/spaces, add floors, redesign, etc.
- ask_question: User is asking for design advice, information, or general questions
- set_budget: User is setting or changing their budget (contains money amounts)
- other: Anything else

User message: "{last_message}"
Current floorplan: {len(floorplan)} rooms
Current budget: {budget_display}

Examples:
- "My budget is $650,000" → set_budget
- "Add a master bedroom" → modify_floorplan  
- "Add another floor with 3 bedrooms" → modify_floorplan
- "Redesign the whole house" → modify_floorplan
- "What's the best flooring?" → ask_question

Respond with only the category name."""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    next_action = response.content.strip().lower()
    
    # Ensure we have a valid action
    valid_actions = ['modify_floorplan', 'ask_question', 'set_budget', 'other']
    if next_action not in valid_actions:
        next_action = 'other'
    
    # If we extracted a budget amount, update the state
    result = {"next_action": next_action}
    if extracted_budget and extracted_budget > 0:
        result["user_budget"] = extracted_budget
    
    return result


def budget_handler_node(state: AppState) -> Dict[str, Any]:
    """Handle budget setting and provide confirmation."""
    user_budget = state.get('user_budget')
    last_message = state.get('last_message', '')
    floorplan = state.get('floorplan', [])
    
    if user_budget:
        response = f"✅ **Budget Set Successfully!**\n\n💰 Your budget: ${user_budget:,.2f}\n\n"
        
        if floorplan:
            total_area = get_total_area(floorplan)
            estimated_cost = calculate_construction_cost(total_area)
            
            if estimated_cost <= user_budget:
                savings = user_budget - estimated_cost
                response += f"🎉 Great news! Your current floorplan (${estimated_cost:,.2f}) fits within your budget with ${savings:,.2f} to spare.\n\n"
            else:
                overage = estimated_cost - user_budget
                response += f"⚠️ Your current floorplan (${estimated_cost:,.2f}) exceeds your budget by ${overage:,.2f}. I can help you adjust the design to fit your budget.\n\n"
            
            response += "What would you like to do next? You can:\n"
            response += "• Add or modify rooms\n"
            response += "• Ask for design suggestions\n"
            response += "• Request a complete redesign"
        else:
            response += "Now let's start designing your house! You can:\n"
            response += "• Tell me what rooms you need: 'I need 3 bedrooms and 2 bathrooms'\n"
            response += "• Ask for a complete design: 'Design me a 2000 sq ft house'\n"
            response += "• Add specific rooms: 'Add a master bedroom 14x16 feet'"
    else:
        response = f"I noticed you mentioned budget in: '{last_message}'\n\nPlease specify your budget amount, for example:\n• 'My budget is $650,000'\n• 'I can spend up to $500k'\n• 'Budget: $750,000'"
    
    return {"final_response": response}

def route_from_router(state: AppState) -> Literal["floorplan_architect", "design_consultant", "budget_handler", "__end__"]:
    """Route from project manager router based on next_action."""
    next_action = state.get("next_action", "other")
    
    if next_action == "modify_floorplan":
        return "floorplan_architect"
    elif next_action == "ask_question":
        return "design_consultant"
    elif next_action == "set_budget":
        return "budget_handler"
    elif next_action == "other":
        return "design_consultant"  # Handle as general question
    else:
        return "design_consultant"

def route_from_budget_analyst(state: AppState) -> Literal["constraint_solver", "response_generation"]:
    """Route from budget analyst based on budget constraints."""
    estimated_cost = state.get("estimated_cost", 0)
    user_budget = state.get("user_budget", 0)
    
    if user_budget and estimated_cost > user_budget:
        return "constraint_solver"
    else:
        return "response_generation"

def create_graph():
    """Create and compile the LangGraph workflow."""
    # Instantiate StatefulGraph with AppState
    graph = StateGraph(AppState)
    
    # Add all node functions
    graph.add_node("project_manager_router", project_manager_router)
    graph.add_node("floorplan_architect", floorplan_architect_node)
    graph.add_node("budget_analyst", budget_analyst_node)
    graph.add_node("constraint_solver", constraint_solver_node)
    graph.add_node("design_consultant", design_consultant_node)
    graph.add_node("budget_handler", budget_handler_node)
    graph.add_node("response_generation", response_generation_node)
    
    # Set entry point to the router
    graph.set_entry_point("project_manager_router")
    
    # Add conditional edges from router based on next_action
    graph.add_conditional_edges(
        "project_manager_router",
        route_from_router,
        {
            "floorplan_architect": "floorplan_architect",
            "design_consultant": "design_consultant",
            "budget_handler": "budget_handler",
            "__end__": END
        }
    )
    
    # Conditional edge from floorplan_architect - can now terminate directly
    def route_from_floorplan_architect(state: AppState) -> Literal["budget_analyst", "__end__"]:
        # If floorplan_architect already generated a final_response, we can end
        if state.get("final_response"):
            return "__end__"
        else:
            return "budget_analyst"
    
    graph.add_conditional_edges(
        "floorplan_architect",
        route_from_floorplan_architect,
        {
            "budget_analyst": "budget_analyst",
            "__end__": END
        }
    )
    
    # Conditional edge from budget_analyst based on budget constraints
    graph.add_conditional_edges(
        "budget_analyst",
        route_from_budget_analyst,
        {
            "constraint_solver": "constraint_solver",
            "response_generation": "response_generation"
        }
    )
    
    # Terminal edges - all end nodes terminate the workflow
    graph.add_edge("constraint_solver", END)
    graph.add_edge("design_consultant", END)
    graph.add_edge("budget_handler", END)
    graph.add_edge("response_generation", END)
    
    # Compile the graph
    return graph.compile()

def main():
    """Command-line interface loop."""
    # Create and compile the graph
    graph = create_graph()
    
    # Initialize state
    state = AppState(
        conversation_history=[],
        floorplan=[],
        total_sqft=0.0,
        estimated_cost=None,
        user_budget=None,
        final_response="",
        last_message="",
        user_intent="",
        next_action=""
    )
    
    print("🏠 House Design Agent System - Ready!")
    print("You can:")
    print("- Modify floorplans (add/remove/change rooms)")
    print("- Ask design questions and get building advice")
    print("- Set your budget and get cost analysis")
    print("- Get constraint solving when over budget")
    print("\nCommands:")
    print("- 'exit' to quit")
    print("- Examples: 'Add a master bedroom', 'What's the best flooring?', 'My budget is $500,000'")
    print("\n" + "="*60 + "\n")
    
    while True:
        # Prompt user for input
        user_input = input("👤 User: ").strip()
        
        # Check for exit condition
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("👋 Goodbye! Thanks for using the House Design Agent!")
            break
        
        if not user_input:
            continue
        
        # Update conversation history and last message in state
        state["conversation_history"].append(f"User: {user_input}")
        state["last_message"] = user_input
        
        try:
            # Invoke the compiled graph with updated state
            result = graph.invoke(state)
            
            # Print the final response from the resulting state
            if result.get("final_response"):
                print(f"\n🤖 Agent: {result['final_response']}\n")
                # Add agent response to conversation history
                state["conversation_history"].append(f"Agent: {result['final_response']}")
            else:
                print("\n🤖 Agent: I'm processing your request...\n")
            
            # Update state with all results for next iteration
            for key, value in result.items():
                if value is not None:
                    state[key] = value
        
        except Exception as e:
            print(f"\n❌ Error processing your request: {str(e)}\n")
            print("Please try rephrasing your request.\n")
        
        print("-" * 60)

if __name__ == "__main__":
    main()