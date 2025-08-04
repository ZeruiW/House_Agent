#!/usr/bin/env python3
"""
Launch script for the House Design Agent Gradio UI.
Run this script to start the web interface.
"""

import os
import sys
from dotenv import load_dotenv

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import gradio
        import langgraph
        import langchain
        import langchain_openai
        print("✅ All dependencies found!")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False

def check_env_vars():
    """Check if required environment variables are set."""
    load_dotenv()
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY not found in environment variables!")
        print("Please add your OpenAI API key to the .env file:")
        print("OPENAI_API_KEY=your_api_key_here")
        return False
    
    print("✅ Environment variables configured!")
    return True

def main():
    """Main launch function."""
    print("🏠 House Design Agent - Gradio UI Launcher")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment variables
    if not check_env_vars():
        sys.exit(1)
    
    # Import and launch the app
    try:
        from app import main as launch_app
        print("\n🚀 Starting Gradio interface...")
        print("📱 The web interface will open in your browser")
        print("🌐 Default URL: http://localhost:7860")
        print("\n💡 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        launch_app()
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"\n❌ Error launching application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()