# 🏠 House Design Agent

An AI-powered house design assistant built with LangGraph and Gradio. This intelligent agent helps you create floorplans, analyze budgets, and get design advice using Montreal construction standards.


## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment
Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

### 3. Launch the UI
```bash
python launch_ui.py
```

Or run directly:
```bash
python app.py
```

The web interface will open at `http://localhost:7860`

## 📋 Usage Examples

### **Adding Rooms**
- "Add a master bedroom 14x16 feet"
- "I need a 3-car garage, about 24x30"
- "Add a kitchen 12x14 and a dining room 10x12"

### **Modifying Rooms**
- "Make the living room bigger, change it to 18x22"
- "Remove the third bedroom"
- "Update the master bathroom to 8x10"

### **Budget & Design Questions**
- "My budget is $650,000"
- "What's the best flooring for kitchens?"
- "Are there any building code requirements for bathrooms?"

### **Constraint Solving**
When your design exceeds budget, the agent automatically provides specific suggestions:
- Room size reductions with cost savings
- Alternative design approaches
- Prioritization recommendations

## 🏗️ System Architecture

### **LangGraph Workflow**
```
User Input → Project Manager Router → Specialized Agents → Response
```

### **Specialized Agents**
- **Project Manager Router**: Classifies user intent and routes requests
- **Floorplan Architect**: Handles room modifications using specialized tools
- **Budget Analyst**: Calculates costs and analyzes budget constraints
- **Constraint Solver**: Provides solutions when over budget
- **Design Consultant**: Answers general design and building questions

### **Tools & Functions**
- `add_room()`: Add rooms with dimensions
- `remove_room()`: Remove rooms by name  
- `update_room()`: Modify room dimensions
- `calculate_construction_cost()`: Montreal pricing calculations
- `summarize_floorplan()`: Professional floorplan formatting

