"""
Main server initialization script for MCP Flask server
"""
from app import app, agent

if __name__ == '__main__':
    print("\n" + "="*80)
    print("SMART AI AGENT WITH NLP-POWERED TOOL SELECTION")
    print("="*80)
    print("FEATURES:")
    print("- Advanced entity extraction (dates, names, categories, etc.)")
    print("- Smart tool categorization and selection")
    print("- Optimized context for LLM efficiency")
    print("- Intent recognition and mapping")
    print("="*80)
    print("STARTING: Starting initialization...")
    
    # Initialize the agent
    if agent.initialize():
        print(f"\nSUCCESS: Smart Agent ready with {agent.status['tools']} tools!")
        print(f"NLP Available: {agent.tool_selector.entity_extractor.spacy_available if agent.tool_selector else False}")
        print("STARTING: Starting Flask server on http://localhost:5001")
        print("\nNEW ENDPOINTS:")
        print("   POST /analyze           - Analyze query entities and tool selection")
        print("   GET  /tools             - List tools by category")
        print("\nEXAMPLE QUERIES:")
        print('   "Show me recent sports news"')
        print('   "Find articles by John Smith from last month"')  
        print('   "Get technology news from January 2024"')
        print('   "List all authors in politics category"')
        print("\nEXAMPLE CURL:")
        print('   curl -X POST http://localhost:5001/analyze \\')
        print('        -H "Content-Type: application/json" \\')
        print('        -d \'{"message": "Show me recent sports news"}\'')
        print("\n" + "="*80)

        app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
    else:
        print("\nERROR: Initialization failed!")
        agent._print_diagnostics()
        print("\nADDITIONAL SETUP (Optional for better NLP):")
        print("pip install spacy")
        print("python -m spacy download en_core_web_sm")
        sys.exit(1)
