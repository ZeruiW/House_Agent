# 🏠 House Design Agent

An AI-powered house design assistant built with LangGraph and Gradio. This intelligent agent helps you create floorplans, analyze budgets, and get design advice using Montreal construction standards.

## 🌟 Features

### 🏠 **Floorplan Management**
- Add, remove, and modify rooms with specific dimensions
- Real-time area calculations and cost updates
- Professional floorplan summaries with room details

### 💰 **Budget Analysis** 
- Montreal construction costs ($350/sq ft)
- Real-time budget vs. cost comparison
- Automatic constraint solving when over budget

### 🤖 **AI-Powered Assistance**
- Natural language room modifications
- Design advice and building code information
- Intelligent routing to specialized agents

### 🎨 **Web Interface**
- Clean, intuitive Gradio UI
- Real-time floorplan and cost displays  
- Interactive budget slider
- Chat-based interaction

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

## 🎯 Key Benefits

### **🔄 Automatic Feedback Loops**
Every floorplan change triggers automatic budget recalculation, ensuring you always know the cost impact.

### **💡 Intelligent Constraint Solving**
When designs exceed budget, the system provides specific, actionable suggestions with exact cost savings.

### **🎨 User-Driven Design**
No default layouts - the system only creates what you specifically request, ensuring diverse and personalized results.

### **📊 Professional Output**
Beautiful floorplan summaries formatted like architectural drafts with detailed cost breakdowns.

## 🛠️ Files Structure

```
House_Agent/
├── main.py           # Core LangGraph workflow and CLI
├── tools.py          # Floorplan and budget calculation tools
├── app.py            # Gradio web interface
├── launch_ui.py      # UI launcher with dependency checks
├── requirements.txt  # Python dependencies
├── .env              # Environment variables (create this)
└── README.md         # This file
```

## 🌍 Montreal Construction Standards

The system uses Montreal-specific construction costs and building practices:
- **Base cost**: $350 per square foot
- **Includes**: Montreal building codes and climate considerations
- **Currency**: Canadian dollars (CAD)

## 🤝 Contributing

This is a demo project showcasing LangGraph multi-agent workflows. Feel free to extend it with:
- Additional room types and layouts
- Different regional pricing models
- More sophisticated constraint solving
- Integration with CAD tools
- 3D visualization features

## 📄 License

Open source - feel free to use and modify as needed.

---

**Built with ❤️ using LangGraph, LangChain, and Gradio**