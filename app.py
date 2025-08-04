import gradio as gr
import os
from typing import List, Tuple, Optional
from main import create_graph, AppState
from tools import get_total_area, summarize_floorplan

class HouseDesignApp:
    def __init__(self):
        """Initialize the House Design Agent Gradio app."""
        self.graph = create_graph()
        self.reset_state()
    
    def reset_state(self):
        """Reset the application state."""
        self.state = AppState(
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
    
    def process_message(self, message: str, history: List[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], str, str, str]:
        """
        Process user message through the LangGraph workflow.
        
        Args:
            message: User input message
            history: Chat history as list of (user_msg, bot_msg) tuples
        
        Returns:
            Tuple of (updated_history, floorplan_display, budget_status, cost_display)
        """
        if not message.strip():
            return history, self.get_floorplan_display(), self.get_budget_status(), self.get_cost_display()
        
        # Update state with new message
        self.state["last_message"] = message
        self.state["conversation_history"].append(f"User: {message}")
        
        try:
            # Invoke the compiled graph with updated state
            result = self.graph.invoke(self.state)
            
            # Get the agent's response
            agent_response = result.get("final_response", "I'm processing your request...")
            
            # Update state with all results
            for key, value in result.items():
                if value is not None:
                    self.state[key] = value
            
            # Add agent response to conversation history
            self.state["conversation_history"].append(f"Agent: {agent_response}")
            
            # Update chat history
            new_history = history + [(message, agent_response)]
            
            return (
                new_history, 
                self.get_floorplan_display(),
                self.get_budget_status(),
                self.get_cost_display()
            )
            
        except Exception as e:
            error_msg = f"❌ Error processing your request: {str(e)}\nPlease try rephrasing your request."
            new_history = history + [(message, error_msg)]
            return (
                new_history,
                self.get_floorplan_display(),
                self.get_budget_status(),
                self.get_cost_display()
            )
    
    def get_floorplan_display(self) -> str:
        """Get formatted floorplan display."""
        floorplan = self.state.get('floorplan', [])
        if not floorplan:
            return "📋 **No rooms in current floorplan**\n\nStart by asking me to add some rooms!"
        
        total_area = get_total_area(floorplan)
        estimated_cost = self.state.get('estimated_cost', 0)
        user_budget = self.state.get('user_budget')
        
        return summarize_floorplan(floorplan, total_area, estimated_cost, user_budget)
    
    def get_budget_status(self) -> str:
        """Get budget status indicator."""
        user_budget = self.state.get('user_budget')
        estimated_cost = self.state.get('estimated_cost')
        
        if not user_budget:
            return "💰 **Budget:** Not set\n\nSet your budget using the slider above!"
        
        if not estimated_cost:
            return f"💰 **Budget:** ${user_budget:,.2f}\n\n⏳ Add some rooms to see cost analysis!"
        
        if estimated_cost <= user_budget:
            return f"✅ **Within Budget**\n💰 Budget: ${user_budget:,.2f}\n💸 Estimated: ${estimated_cost:,.2f}\n💚 Under by: ${user_budget - estimated_cost:,.2f}"
        else:
            overage = estimated_cost - user_budget
            overage_percent = (overage / user_budget) * 100
            return f"⚠️ **Over Budget**\n💰 Budget: ${user_budget:,.2f}\n💸 Estimated: ${estimated_cost:,.2f}\n🔴 Over by: ${overage:,.2f} ({overage_percent:.1f}%)"
    
    def get_cost_display(self) -> str:
        """Get cost breakdown display."""
        floorplan = self.state.get('floorplan', [])
        estimated_cost = self.state.get('estimated_cost')
        total_sqft = get_total_area(floorplan) if floorplan else 0
        
        if not floorplan:
            return "📊 **Cost Analysis**\n\nNo rooms to analyze yet."
        
        cost_per_sqft = 350  # Montreal pricing
        
        display = f"📊 **Cost Breakdown**\n\n"
        display += f"🏠 Total Area: {total_sqft:,.0f} sq ft\n"
        display += f"💲 Cost per sq ft: ${cost_per_sqft}\n"
        if estimated_cost:
            display += f"💰 Total Estimated Cost: ${estimated_cost:,.2f}\n\n"
        
        # Room breakdown
        if len(floorplan) > 0:
            display += "**Room Details:**\n"
            for room in floorplan:
                room_cost = room.get('area_sqft', 0) * cost_per_sqft
                display += f"• {room.get('name', 'Unknown')}: {room.get('area_sqft', 0):,.0f} sq ft (${room_cost:,.0f})\n"
        
        return display
    
    def clear_conversation(self):
        """Clear conversation and reset state."""
        self.reset_state()
        return [], self.get_floorplan_display(), self.get_budget_status(), self.get_cost_display()

def create_interface():
    """Create and configure the Gradio interface."""
    app = HouseDesignApp()
    
    # Custom CSS for better styling
    css = """
    .gradio-container {
        max-width: 1200px !important;
    }
    .chat-message {
        padding: 10px;
        margin: 5px;
        border-radius: 10px;
    }
    .status-panel {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }
    """
    
    with gr.Blocks(css=css, title="🏠 House Design Agent", theme=gr.themes.Soft()) as interface:
        gr.Markdown(
            """
            # 🏠 House Design Agent
            
            Welcome to your AI-powered house design assistant! I can help you:
            - **Create and modify floorplans** (add, remove, or change rooms)
            - **Handle complex requests** (add floors, redesign, multiple rooms)
            - **Analyze budgets** with Montreal construction costs ($350/sq ft)
            - **Solve constraints** when designs exceed your budget
            - **Answer design questions** about materials, styles, and building codes
            """
        )
        
        with gr.Row():
            with gr.Column(scale=2):
                # Main chat interface
                chatbot = gr.Chatbot(
                    label="💬 Chat with your House Design Agent",
                    height=500,
                    show_label=True,
                    container=True,
                    bubble_full_width=False
                )
                
                with gr.Row():
                    msg_textbox = gr.Textbox(
                        placeholder="Ask me about floorplans, budgets, or design questions...",
                        label="Your Message",
                        show_label=False,
                        scale=4
                    )
                    send_btn = gr.Button("Send 📤", variant="primary")
                
                with gr.Row():
                    clear_btn = gr.Button("🗑️ Clear Chat", variant="secondary")
                    
            with gr.Column(scale=1):
                # Status displays
                budget_status = gr.Markdown(
                    app.get_budget_status(),
                    label="💰 Budget Status"
                )
                
                floorplan_display = gr.Markdown(
                    app.get_floorplan_display(),
                    label="🏠 Current Floorplan"
                )
                
                cost_display = gr.Markdown(
                    app.get_cost_display(),
                    label="📊 Cost Analysis"
                )
        
        # Event handlers
        def handle_message(message, history):
            return app.process_message(message, history) + ("",)  # Clear textbox
        
        def handle_clear():
            return app.clear_conversation() + ([],)  # Clear chatbot
        
        # Connect events
        send_btn.click(
            fn=handle_message,
            inputs=[msg_textbox, chatbot],
            outputs=[chatbot, floorplan_display, budget_status, cost_display, msg_textbox]
        )
        
        msg_textbox.submit(
            fn=handle_message,
            inputs=[msg_textbox, chatbot],
            outputs=[chatbot, floorplan_display, budget_status, cost_display, msg_textbox]
        )
        
        clear_btn.click(
            fn=handle_clear,
            outputs=[chatbot, floorplan_display, budget_status, cost_display]
        )
        
        # Footer
        # gr.Markdown(
        #     """
        #     ---
        #     **💡 Tips:**
        #     - **Set your budget**: "My budget is $650,000" or "I can spend $500k"
        #     - **Be specific with rooms**: "Add a 12x14 living room"
        #     - **Complex requests**: "Add another floor with 3 bedrooms" or "Redesign everything"
        #     - **Ask for advice**: "What's the best layout for a small kitchen?"
        #     - **All costs**: Montreal construction standards ($350/sq ft)
        #     """
        # )
    
    return interface

def main():
    """Launch the Gradio application."""
    interface = create_interface()
    
    # Launch with public sharing disabled by default
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        show_error=True,
        quiet=False
    )

if __name__ == "__main__":
    main()