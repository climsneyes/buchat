#!/usr/bin/env python3
"""
기존 langchain 벡터DB를 SimpleVectorDB로 변환하는 스크립트
"""

import os
import pickle
import shutil
from rag_utils import SimpleVectorDB, OpenAIEmbeddings

def convert_langchain_to_simple_vector_db(input_path, output_path, openai_api_key):
    """
    langchain 벡터DB를 SimpleVectorDB로 변환합니다.
    """
    print(f"벡터DB 변환 시작: {input_path} -> {output_path}")
    
    try:
        # 기존 벡터DB 로드 시도
        with open(input_path, 'rb') as f:
            old_db = pickle.load(f)
        
        print("기존 벡터DB 로드 성공")
        
        # 기존 벡터DB에서 문서와 임베딩 추출
        if hasattr(old_db, 'docstore') and hasattr(old_db.docstore, '_dict'):
            # ChromaDB 형식
            documents = []
            embeddings_list = []
            
            for doc_id, doc in old_db.docstore._dict.items():
                if hasattr(doc, 'page_content') and hasattr(doc, 'metadata'):
                    documents.append({
                        'page_content': doc.page_content,
                        'metadata': doc.metadata
                    })
            
            print(f"추출된 문서 수: {len(documents)}")
            
            # 새로운 임베딩 생성
            embeddings = OpenAIEmbeddings(
                openai_api_key=openai_api_key,
                model="text-embedding-3-small"
            )
            
            # 문서 임베딩 생성
            doc_embeddings = embeddings.embed_documents([doc['page_content'] for doc in documents])
            
            # SimpleVectorDB 생성
            new_db = SimpleVectorDB(documents, embeddings, doc_embeddings)
            
            # 새로운 벡터DB 저장
            with open(output_path, 'wb') as f:
                pickle.dump(new_db, f)
            
            print(f"벡터DB 변환 완료: {output_path}")
            return new_db
            
        elif hasattr(old_db, 'documents'):
            # 기존 SimpleVectorDB 형식
            print("이미 SimpleVectorDB 형식입니다.")
            return old_db
            
        else:
            print("알 수 없는 벡터DB 형식입니다.")
            return None
            
    except Exception as e:
        print(f"벡터DB 변환 실패: {e}")
        return None

def main():
    # 환경변수에서 API 키 가져오기
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
        return
    
    input_path = "vector_db_merged.pkl"
    output_path = "vector_db_merged_converted.pkl"
    
    if not os.path.exists(input_path):
        print(f"❌ 입력 파일이 존재하지 않습니다: {input_path}")
        return
    
    # 벡터DB 변환
    new_db = convert_langchain_to_simple_vector_db(input_path, output_path, openai_api_key)
    
    if new_db:
        # 기존 파일 백업
        backup_path = input_path + ".backup"
        shutil.copy2(input_path, backup_path)
        print(f"기존 파일 백업: {backup_path}")
        
        # 새 파일로 교체
        shutil.move(output_path, input_path)
        print(f"변환된 파일로 교체: {input_path}")
        
        # 변환 완료 표시
        with open(input_path + ".converted", "w") as f:
            f.write("converted")
        print("변환 완료!")
    else:
        print("변환 실패!")

if __name__ == "__main__":
    main() 