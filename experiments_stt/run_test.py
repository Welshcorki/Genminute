import sys
import os
from pathlib import Path

# 현재 디렉토리 설정
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))

from local_stt_pipeline import LocalSTTPipeline

def main():
    print("🎤 Genminute Local STT Experiment Runner")
    
    # 테스트할 오디오 파일 찾기
    # 1. 명령줄 인자로 받거나
    # 2. uploads 폴더의 최신 파일 사용
    target_file = None
    
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
    else:
        uploads_dir = root_dir / "uploads"
        if uploads_dir.exists():
            files = sorted(
                [f for f in uploads_dir.iterdir() if f.is_file()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            # 오디오/비디오 파일 필터링
            audio_exts = {'.mp3', '.wav', '.m4a', '.flac', '.webm', '.mp4'}
            for f in files:
                if f.suffix.lower() in audio_exts:
                    target_file = str(f)
                    break
    
    if not target_file:
        print("❌ No audio file found in 'uploads/' directory.")
        print("Usage: python run_test.py <path_to_audio_file>")
        return

    print(f"📂 Target File: {target_file}")
    
    # 파이프라인 실행
    try:
        pipeline = LocalSTTPipeline()
        results = pipeline.run(target_file)
        
        print("\n" + "="*30 + " RESULT " + "="*30)
        for segment in results:
            start_fmt = f"{segment['start']:.1f}"
            end_fmt = f"{segment['end']:.1f}"
            print(f"[{start_fmt}s ~ {end_fmt}s] {segment['speaker']}: {segment['text']}")
        print("="*68)
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
