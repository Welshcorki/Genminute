from pyannote.audio import Pipeline
import inspect

print("🔍 Inspecting Pipeline.from_pretrained signature:")
try:
    sig = inspect.signature(Pipeline.from_pretrained)
    print(sig)
except Exception as e:
    print(f"Error: {e}")

print("\n🔍 Checking docstring:")
print(Pipeline.from_pretrained.__doc__)
