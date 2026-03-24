import uuid
from pathlib import Path
from TTS.api import TTS
import sounddevice as sd
print("Loading TTS model...")
api = TTS(model_name="tts_models/en/ljspeech/glow-tts", progress_bar=True)

def generate_speech(text, prefix="msg"):
    """
    Synthesizes text and saves it to a unique file in the /temporary folder.
    """
    # setup paths
    base_dir = Path(__file__).parent if "__file__" in locals() else Path.cwd()
    temp_folder = base_dir / "temporary"
    temp_folder.mkdir(parents=True, exist_ok=True)
    
    # generate a unique filename using UUID
    # Example: msg_a1b2c3d4.wav (ts aint vibe coded, im just giving ur domeahh some eg.s)
    unique_id = str(uuid.uuid4())[:8] 
    filename = f"{prefix}_{unique_id}.wav"
    file_path = temp_folder / filename
    
    try:
        # 3. Synthesize
        api.tts_to_file(text=text, file_path=str(file_path))
        sd.play(file_path)
        sd.wait()  # Wait until the audio is done playing

    except Exception as e:
        print(f"CRITICAL ERROR: Failed to generate TTS: {e}")
        return None
