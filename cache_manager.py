#!/usr/bin/env python3
"""
캐시 관리 스크립트
PDF 파일의 해시 기반 캐싱 시스템을 관리합니다.
"""

import os
import sys
from rag_utils import (
    get_cache_status, 
    force_rebuild_cache, 
    clear_cache,
    PDF_PATH,
    CHROMA_PATH
)

def print_cache_status():
    """캐시 상태를 출력합니다."""
    print("=== 캐시 상태 확인 ===")
    status = get_cache_status()
    
    print(f"PDF 파일 경로: {PDF_PATH}")
    print(f"벡터DB 경로: {CHROMA_PATH}")
    print(f"상태: {status['status']}")
    print(f"메시지: {status['message']}")
    
    if 'current_hash' in status:
        print(f"현재 파일 해시: {status['current_hash']}")
        print(f"캐시된 파일 해시: {status['cached_hash']}")
        print(f"청크 수: {status['chunk_count']}")
        print(f"생성 시간: {status['created_at']}")
        print(f"유효성: {'✅ 유효' if status['is_valid'] else '❌ 무효'}")

def main():
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python cache_manager.py status     - 캐시 상태 확인")
        print("  python cache_manager.py rebuild    - 캐시 강제 재생성")
        print("  python cache_manager.py clear      - 캐시 삭제")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        print_cache_status()
    
    elif command == "rebuild":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ 환경변수 OPENAI_API_KEY가 설정되어 있지 않습니다.")
            return
        
        print("캐시를 강제로 재생성합니다...")
        try:
            vector_db = force_rebuild_cache(api_key)
            print("✅ 캐시 재생성 완료!")
            print_cache_status()
        except Exception as e:
            print(f"❌ 캐시 재생성 실패: {e}")
    
    elif command == "clear":
        print("캐시를 삭제합니다...")
        clear_cache()
        print("✅ 캐시 삭제 완료!")
        print_cache_status()
    
    else:
        print(f"❌ 알 수 없는 명령어: {command}")
        print("사용 가능한 명령어: status, rebuild, clear")

if __name__ == "__main__":
    main() 