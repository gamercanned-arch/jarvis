"""
Tool execution handlers for JARVIS
Uses:
- DDGS (duckduckgo-search) for web search
- IPython for code execution  
- MCP-style file operations
"""
import json
import subprocess
import os
from pathlib import Path
from ddgs import DDGS
from IPython import get_ipython
from toolshandling.ttsm import generate_speech

def execute_tool(tool_name, arguments):
    """
    Execute a tool based on the tool name and arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments for the tool
        
    Returns:
        Result of the tool execution as a string
    """
    if tool_name == "web_search":
        return web_search(arguments.get("query", ""), arguments.get("num_results", 5))
    elif tool_name == "IPython":
        return execute_ipython(arguments.get("command", ""))
    elif tool_name == "file_operations":
        return file_operations(
            arguments.get("operation", ""),
            arguments.get("file_path", ""),
            arguments.get("content", "")
        )
    elif tool_name == "TTSout":
        return tts_output(arguments.get("text", ""))
    else:
        return f"Error: Unknown tool '{tool_name}'"


def web_search(query, num_results=5):
    """
    Search the web for information using DuckDuckGo.
    """
    if not query:
        return "Error: No search query provided"
    
    try:
        ddgs = DDGS()
        results = ddgs.text(query, max_results=num_results)
        
        if not results:
            return f"No results found for '{query}'"
        
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(
                f"{i}. {result.get('title', 'No title')}\n"
                f"   URL: {result.get('href', 'No URL')}\n"
                f"   {result.get('body', 'No description')}\n"
            )
        
        return "\n".join(formatted_results)
    
    except Exception as e:
        return f"Error performing web search: {str(e)}"


def execute_ipython(command):
    """
    Execute Python code using IPython.
    """
    if not command:
        return "Error: No command provided"
    
    try:
        # Get or create IPython instance
        ipython = get_ipython()
        
        if ipython is None:
            # Run in a new IPython shell
            from IPython.core.interactiveshell import InteractiveShell
            ipython = InteractiveShell.instance()
        
        # Execute the command
        result = ipython.run_cell(command)
        
        if result.success:
            # Get the output
            if result.result is not None:
                return str(result.result)
            return "Command executed successfully (no output)"
        else:
            return f"Error: {result.error_in_exec or result.error_before_exec}"
    
    except Exception as e:
        return f"Error executing IPython command: {str(e)}"


def file_operations(operation, file_path, content=""):
    """
    Perform file operations using MCP fs-mcp-server.
    Supported operations: read, write, delete, list, create_directory, search, edit, info
    """
    from toolshandling.mcp_fs import mcp_file_operation
    
    if not file_path:
        return "Error: No file path provided"
    
    # Convert relative paths to absolute paths
    abs_path = os.path.abspath(os.path.expanduser(file_path))
    
    # Map operations to MCP operations
    op_mapping = {
        "read": "read",
        "write": "write",
        "delete": "delete",
        "list": "list",
        "create_directory": "mkdir",
        "get_file_info": "info",
        "search": "search",
        "edit": "edit",
    }
    
    mcp_op = op_mapping.get(operation)
    if not mcp_op:
        return f"Error: Unknown operation '{operation}'. Supported: {', '.join(op_mapping.keys())}"
    
    try:
        result = mcp_file_operation(mcp_op, abs_path, content)
        return result
    except Exception as e:
        return f"Error: {str(e)}"


def tts_output(text):
    """
    Convert text to speech using TTS (ljspeech model).
    
    Args:
        text: Text to convert to speech
        
    Returns:
        Status message
    """
    if not text:
        return "Error: No text provided"
    
    try:
        generate_speech(text)


def load_tools():
    """Load tool definitions from tools.json"""
    tools_path = Path("toolshandling/tools.json")
    if tools_path.exists():
        with open(tools_path, "r") as f:
            return json.load(f)
    return []


if __name__ == "__main__":
    # Test the tools
    print("Testing web_search:")
    print(web_search("Python programming", 2))
    
    print("\n" + "=" * 50)
    print("Testing IPython:")
    print(execute_ipython("print('Hello from JARVIS!')"))
    
    print("\n" + "=" * 50)
    print("Testing file_operations (read):")
    print(file_operations("read", "main/config.py"))
    
    print("\n" + "=" * 50)
    print("Testing file_operations (list):")
    print(file_operations("list", "."))
