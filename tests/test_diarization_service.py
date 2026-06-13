import sys
import os
from pathlib import Path
import json

# 프로젝트 루트 경로 설정 (tests/ 의 상위 디렉토리가 루트)
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))

from services.diarization import diarization_service

def main():
    print("🧪 Testing DiarizationService...")

    # 테스트할 파일 찾기 (uploads 폴더의 최신 파일)
    uploads_dir = root_dir / "uploads"
    target_file = None
    
    if uploads_dir.exists():
        files = sorted(
            [f for f in uploads_dir.iterdir() if f.is_file()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        audio_exts = {'.mp3', '.wav', '.m4a', '.flac', '.webm', '.mp4'}
        for f in files:
            if f.suffix.lower() in audio_exts:
                target_file = str(f)
                break
    
    if not target_file:
        print("⚠️ No audio file found in 'uploads/'. Generating dummy silent WAV for testing...")
        import wave
        import struct
        
        dummy_path = uploads_dir / "test_silence.wav"
        # 폴더가 없으면 생성
        uploads_dir.mkdir(exist_ok=True)
        
        # 1초짜리 무음 16kHz Mono WAV 생성
        with wave.open(str(dummy_path), 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            # 16000 프레임 (1초)
            data = struct.pack('<h', 0) * 16000
            wav_file.writeframes(data)
            
        target_file = str(dummy_path)
        print(f"✅ Created dummy file: {target_file}")

    print(f"📂 Target: {target_file}")

    try:
        # 서비스 호출
        print(f"⏳ Processing {target_file}...")
        results = diarization_service.transcribe_and_diarize(target_file)
        
        # 결과 파일로 저장 (인코딩 문제 해결)
        output_path = root_dir / "test_result.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        print("\n" + "="*30 + " RESULT SAVED " + "="*30)
        print(f"✅ Result saved to: {output_path}")
        print(f"📊 Total segments: {len(results)}")
        if results:
            print(f"🗣️  First segment preview: [{results[0]['start']:.1f}s] {results[0]['speaker']}: {results[0]['text']}")
        print("="*68)
        
    except Exception as e:
        print(f"\n❌ Service test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
