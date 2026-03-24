#main loop for ya

import time
from jinja2 import Template, Environment, FileSystemLoader
import json
import subprocess
import os
import requests
from main.config import serve, sys_prompt
from pathlib import Path
import threading
import tempfile

# API Configuration
API_BASE = "http://127.0.0.1:8080"
API_COMPLETIONS = f"{API_BASE}/v1/chat/completions"
API_MODELS = f"{API_BASE}/v1/models"

# vars
tools_file = "toolshandling/tools.json"
jinja_template = "main/template.jinja"

# Global conversation history
conversation = []

# Whisper model (lazy loaded)
_whisper_model = None

def get_whisper_model():
    """Load Whisper small model (lazy loading)"""
    global _whisper_model
    if _whisper_model is None:
        import whisper
        print("Loading Whisper small model...")
        _whisper_model = whisper.load_model("small")
        print("Whisper model loaded!")
    return _whisper_model

def record_and_transcribe(duration=300):
    """
    Record audio from microphone and transcribe using Whisper.
    Uses Voice Activity Detection (VAD) to automatically stop when user stops speaking.
    
    Args:
        duration: Maximum recording duration in seconds
    
    Returns:
        Transcribed text or None if failed
    """
    try:
        import sounddevice as sd
        import numpy as np
        import webrtcvad
        
        # VAD settings
        vad = webrtcvad.Vad(2)  # Aggressiveness mode (0-3)
        sample_rate = 16000
        frame_duration = 30  # ms
        frame_size = int(sample_rate * frame_duration / 1000)
        
        print("Listening... (speak now, will auto-detect when you stop)")
        
        # Collect audio frames
        audio_frames = []
        silence_count = 0
        max_silence_frames = 30  # ~1 second of silence to trigger stop
        
        # Create stream
        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype=np.int16,
            blocksize=frame_size
        ) as stream:
            start_time = time.time()
            
            while True:
                # Check max duration
                if time.time() - start_time > duration:
                    print("Max duration reached")
                    break
                
                # Read frame
                frame, _ = stream.read(frame_size)
                
                # Check for speech using VAD
                try:
                    is_speech = vad.is_speech(frame, sample_rate)
                except:
                    # Fallback: use energy-based detection
                    energy = np.abs(frame).mean()
                    is_speech = energy > 500
                
                if is_speech:
                    audio_frames.append(frame)
                    silence_count = 0
                else:
                    audio_frames.append(frame)
                    silence_count += 1
                    
                    # Stop if enough silence
                    if silence_count > max_silence_frames:
                        print("Speech ended, processing...")
                        break
        
        if not audio_frames:
            print("No audio detected")
            return None
        
        # Combine all frames
        audio_data = np.concatenate(audio_frames)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
        
        try:
            # Save as WAV
            import scipy.io.wavfile as wav
            wav.write(temp_path, sample_rate, audio_data)
            
            # Transcribe
            model = get_whisper_model()
            result = model.transcribe(temp_path)
            
            return result["text"].strip()
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except ImportError as e:
        print(f"Import error: {e}")
        print("Installing webrtcvad... run: pip install webrtcvad")
        # Fallback to simple recording
        return record_and_transcribe_simple(duration)
    except Exception as e:
        print(f"Voice input error: {e}")
        return None


def record_and_transcribe_simple(duration=5):
    """
    Simple fallback recording without VAD.
    """
    try:
        import sounddevice as sd
        import numpy as np
        
        print(f"Recording for {duration} seconds...")
        
        # Record audio
        audio_data = sd.rec(
            int(duration * 16000),
            samplerate=16000,
            channels=1,
            dtype=np.float32
        )
        sd.wait()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name
        
        try:
            # Save as WAV
            import scipy.io.wavfile as wav
            wav.write(temp_path, 16000, (audio_data * 32767).astype(np.int16))
            
            # Transcribe
            model = get_whisper_model()
            result = model.transcribe(temp_path)
            
            return result["text"].strip()
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        print(f"Voice input error: {e}")
        return None

# load shit
def load_shit(type):
    if type == "tools":
        with open(tools_file, "r") as file:
            tools = json.load(file)
            return tools
    elif type == "system":
        return sys_prompt()
    elif type == "template":
        env = Environment(loader=FileSystemLoader(Path(jinja_template).parent or "."))
        return env.get_template(Path(jinja_template).name)

#check for llama-server
def check_llama_server():
    try:
        response = requests.get(API_MODELS, timeout=2)
        return response.status_code == 200
    except:
        return False

def start_llama_server():
    if not check_llama_server():
        print("llama-server is not running, starting it now...")
        serve()
        # Wait for server to start
        time.sleep(5)
        # Check again
        max_retries = 10
        for i in range(max_retries):
            if check_llama_server():
                print("llama-server started successfully!")
                return True
            time.sleep(2)
        print("Warning: Could not verify llama-server is running")
        return False
    else:
        print("llama-server is already running, continuing...")
        return True

# Format messages for Qwen3.5
def format_conversation(messages, system_prompt, tools=None):
    """Format conversation using the Jinja template"""
    template = load_shit("template")
    return template.render(
        messages=messages,
        system_prompt=system_prompt,
        tools=tools,
        add_generation_prompt=True,
        enable_thinking=True
    )

# Call the API
def chat_completion(messages, tools=None, temperature=0.7):
    """Send a chat completion request to llama-server"""
    payload = {
        "messages": messages,
        "temperature": temperature,
        "stream": False
    }
    
    if tools:
        payload["tools"] = tools
    
    try:
        response = requests.post(API_COMPLETIONS, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return None

# Handle tool calls from model response
def handle_tool_calls(tool_calls):
    """Execute tool calls and return results"""
    results = []
    
    for tool_call in tool_calls:
        # Handle both formats (raw and parsed)
        if isinstance(tool_call, dict):
            func_name = tool_call.get("function", {}).get("name") if "function" in tool_call else tool_call.get("name")
            arguments = tool_call.get("function", {}).get("arguments") if "function" in tool_call else tool_call.get("arguments", {})
            
            # Parse arguments if they're a string
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except:
                    arguments = {}
        else:
            func_name = tool_call.name
            arguments = tool_call.arguments
        
        print(f"\n[TOOL CALL] {func_name}: {arguments}")
        
        # Import and execute the tool
        from toolshandling.tools import execute_tool
        result = execute_tool(func_name, arguments)
        
        # Handle potential None result
        result_str = str(result) if result else ""
        results.append({
            "tool_call_id": tool_call.get("id", "unknown"),
            "function": func_name,
            "result": result_str
        })
        print(f"[TOOL RESULT] {result_str[:200]}...")  # Print first 200 chars
    
    return results

# Main conversation loop
def main_loop():
    """Main conversation loop"""
    # Start llama-server
    if not start_llama_server():
        print("Failed to start llama-server. Exiting.")
        return
    
    # Load system prompt and tools
    system_prompt = load_shit("system")
    tools = load_shit("tools")
    
    print(f"\nLoaded {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")
    
    # Initialize conversation with system prompt
    conversation.append({
        "role": "system",
        "content": system_prompt
    })
    
    print("\n" + "=" * 50)
    print("JARVIS is ready! Type 'exit' to quit.")
    print("         Type 'voice' to use voice input")
    print("=" * 50 + "\n")
    
    # Main interaction loop
    while True:
        try:
            user_input = input("You: ")
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("JARVIS: Goodbye! Shutting down...")
                break
            
            # Voice input mode
            if user_input.lower() == "voice":
                print("Activating voice mode...")
                transcribed = record_and_transcribe(duration=5)
                if transcribed:
                    print(f"Heard: {transcribed}")
                    user_input = transcribed
                else:
                    continue
            
            if not user_input.strip():
                continue
            
            # Add user message to conversation
            conversation.append({
                "role": "user", 
                "content": user_input
            })
            
            # Get response from API
            print("JARVIS: Thinking...")
            response = chat_completion(conversation, tools=tools)
            
            if response and "choices" in response:
                assistant_message = response["choices"][0]["message"]
                
                # Check for tool calls
                if "tool_calls" in assistant_message and assistant_message["tool_calls"]:
                    # Add assistant message with tool calls to conversation
                    conversation.append(assistant_message)
                    
                    # Execute tools
                    tool_results = handle_tool_calls(assistant_message["tool_calls"])
                    
                    # Add tool results to conversation
                    for result in tool_results:
                        conversation.append({
                            "role": "tool",
                            "tool_call_id": result["tool_call_id"],
                            "content": result["result"]
                        })
                    
                    # Get final response after tool execution
                    print("JARVIS: Processing tool results...")
                    final_response = chat_completion(conversation, tools=tools)
                    
                    if final_response and "choices" in final_response:
                        final_message = final_response["choices"][0]["message"]
                        conversation.append(final_message)
                        print(f"JARVIS: {final_message.get('content', '')}")
                else:
                    # Regular response
                    conversation.append(assistant_message)
                    content = assistant_message.get("content", "")
                    print(f"JARVIS: {content}")
            else:
                print("JARVIS: Sorry, I didn't get a response. Is llama-server running?")
                
        except KeyboardInterrupt:
            print("\nJARVIS: Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue


if __name__ == "__main__":
    main_loop()
