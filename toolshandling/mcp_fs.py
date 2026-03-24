"""
MCP File Operations wrapper using mcp-filesystem
https://github.com/yangjiacheng1996/mcp_filesystem
"""
import json
import os
from pathlib import Path

# Allowed directories for file operations
ALLOWED_DIRS = [
    os.path.abspath("."),
    os.path.abspath("./main"),
    os.path.abspath("./toolshandling"),
    os.path.abspath("./setup"),
]


def _check_path_allowed(path):
    """Check if the path is within allowed directories"""
    abs_path = os.path.abspath(path)
    for allowed_dir in ALLOWED_DIRS:
        if abs_path.startswith(allowed_dir):
            return True
    raise PermissionError(f"Path '{path}' is not within allowed directories: {ALLOWED_DIRS}")


def _format_result(result, extract_key=None):
    """Format the result from mcp_filesystem functions"""
    if not isinstance(result, dict):
        return str(result)
    
    if not result.get("success", False):
        error = result.get("error", "Unknown error")
        return f"Error: {error}"
    
    if extract_key:
        data = result.get(extract_key)
        if data is not None:
            if isinstance(data, (list, dict)):
                return json.dumps(data, indent=2)
            return str(data)
    
    # Default: return the whole result formatted
    return json.dumps(result, indent=2)


def mcp_file_operation(operation, path, content="", **kwargs):
    """
    Execute a file operation using mcp_filesystem.
    
    Args:
        operation: Operation to perform (list, read, write, mkdir, delete, copy, move, info, search)
        path: File/directory path
        content: Content for write operations
        **kwargs: Additional parameters for specific operations
    
    Returns:
        Result of the operation as a string
    """
    from mcp_filesystem import (
        directory_list,
        file_read,
        file_write,
        directory_create,
        file_delete,
        directory_delete,
        file_copy,
        directory_copy,
        file_move,
        directory_move,
        file_info,
        directory_info,
        file_find,
        directory_find,
    )
    
    try:
        # Check path is allowed
        _check_path_allowed(path)
        
        if operation == "list":
            result = directory_list(
                directory_path=path,
                sort_by=kwargs.get("sort_by", "name"),
                reverse=kwargs.get("reverse", False),
                filter_type=kwargs.get("filter_type")
            )
            return _format_result(result, "items")
        
        elif operation == "read":
            result = file_read(
                file_path=path,
                start_line=kwargs.get("start_line"),
                end_line=kwargs.get("end_line"),
                max_file_size=kwargs.get("max_size", 104857600),
                encoding=kwargs.get("encoding", "utf8")
            )
            return _format_result(result, "content")
        
        elif operation == "write":
            result = file_write(
                file_path=path,
                content=content
            )
            return _format_result(result)
        
        elif operation == "mkdir":
            result = directory_create(
                directory_path=path
            )
            return _format_result(result)
        
        elif operation == "delete":
            # Check if it's a file or directory
            if os.path.isfile(path):
                result = file_delete(file_path=path)
            elif os.path.isdir(path):
                result = directory_delete(directory_path=path)
            else:
                return f"Error: Path '{path}' does not exist"
            return _format_result(result)
        
        elif operation == "copy":
            source = kwargs.get("source", "")
            destination = kwargs.get("destination", "")
            _check_path_allowed(source)
            _check_path_allowed(destination)
            
            if os.path.isfile(source):
                result = file_copy(source=source, destination=destination)
            elif os.path.isdir(source):
                result = directory_copy(source=source, destination=destination)
            else:
                return f"Error: Source '{source}' does not exist"
            return _format_result(result)
        
        elif operation == "move":
            source = kwargs.get("source", "")
            destination = kwargs.get("destination", "")
            _check_path_allowed(source)
            _check_path_allowed(destination)
            
            if os.path.isfile(source):
                result = file_move(source=source, destination=destination)
            elif os.path.isdir(source):
                result = directory_move(source=source, destination=destination)
            else:
                return f"Error: Source '{source}' does not exist"
            return _format_result(result)
        
        elif operation == "info":
            if os.path.isfile(path):
                result = file_info(file_path=path)
            elif os.path.isdir(path):
                result = directory_info(directory_path=path)
            else:
                return f"Error: Path '{path}' does not exist"
            return _format_result(result)
        
        elif operation == "search":
            # file_find searches for files by name pattern
            result = file_find(
                root_dir=path,
                pattern=kwargs.get("pattern", "*"),
                case_sensitive=kwargs.get("case_sensitive", False)
            )
            return _format_result(result, "matches")
        
        else:
            return f"Error: Unknown operation '{operation}'"
    
    except PermissionError as e:
        return str(e)
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    # Test the MCP file operations
    print("Testing MCP file operations...")
    
    print("\n1. List current directory:")
    try:
        print(mcp_file_operation("list", "."))
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n2. Read a file:")
    try:
        print(mcp_file_operation("read", "main/config.py"))
    except Exception as e:
        print(f"Error: {e}")
