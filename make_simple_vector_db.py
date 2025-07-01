import os
import pickle
from rag_utils import SimpleVectorDB, OpenAIEmbeddings, chunk_pdf_to_text_chunks

PDF_DIR = r"C:\Users\yonom\Downloads\다누리"
OUTPUT_PATH = "vector_db_merged.pkl"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# PDF 파일 목록 수집
pdf_files = [os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR) if f.lower().endswith('.pdf')]
pdf_files.sort()

print(f"PDF 파일 {len(pdf_files)}개 발견:")
for f in pdf_files:
    print(f"- {f}")

all_chunks = []
for pdf_path in pdf_files:
    print(f"청크 분할: {pdf_path}")
    chunks = chunk_pdf_to_text_chunks(pdf_path)
    all_chunks.extend(chunks)
    print(f"  → {len(chunks)}개 청크 생성")

print(f"총 청크 개수: {len(all_chunks)}")

# 임베딩 생성
embeddings = OpenAIEmbeddings(
    openai_api_key=OPENAI_API_KEY,
    model="text-embedding-3-small"
)
print("문서 임베딩 생성 중...")
doc_embeddings = embeddings.embed_documents([doc['page_content'] for doc in all_chunks])

# SimpleVectorDB 생성 및 저장
vector_db = SimpleVectorDB(all_chunks, embeddings, doc_embeddings)
with open(OUTPUT_PATH, "wb") as f:
    pickle.dump(vector_db, f)
print(f"SimpleVectorDB 저장 완료: {OUTPUT_PATH}") 