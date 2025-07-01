import os
import hashlib
import json
import pickle
import numpy as np
import re
import openai
import shutil
from pypdf import PdfReader

PDF_PATH = "pdf/ban.pdf"
VECTOR_DB_PATH = "vector_db.pkl"
CACHE_INFO_PATH = "cache_info.json"

# 언어 감지 함수
def detect_language(text):
    """텍스트의 언어를 감지합니다."""
    # 한글 패턴
    korean_pattern = re.compile(r'[가-힣]')
    # 영어 패턴
    english_pattern = re.compile(r'[a-zA-Z]')
    # 일본어 패턴 (히라가나, 카타카나)
    japanese_pattern = re.compile(r'[あ-んア-ン]')
    # 중국어 패턴 (간체, 번체)
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    # 베트남어 패턴
    vietnamese_pattern = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]')
    # 프랑스어 패턴
    french_pattern = re.compile(r'[àâäéèêëïîôöùûüÿç]')
    # 독일어 패턴
    german_pattern = re.compile(r'[äöüß]')
    # 태국어 패턴
    thai_pattern = re.compile(r'[\u0e00-\u0e7f]')
    
    text_lower = text.lower()
    
    # 각 언어별 점수 계산
    scores = {
        'ko': len(korean_pattern.findall(text)),
        'en': len(english_pattern.findall(text)),
        'ja': len(japanese_pattern.findall(text)),
        'zh': len(chinese_pattern.findall(text)),
        'vi': len(vietnamese_pattern.findall(text)),
        'fr': len(french_pattern.findall(text)),
        'de': len(german_pattern.findall(text)),
        'th': len(thai_pattern.findall(text))
    }
    
    # 가장 높은 점수의 언어 반환
    detected_lang = max(scores, key=scores.get)
    
    # 점수가 0이면 기본값으로 영어 반환
    if scores[detected_lang] == 0:
        return 'en'
    
    return detected_lang

# 언어별 프롬프트 템플릿
LANGUAGE_PROMPTS = {
    'ko': """아래 참고 정보에서 답변의 근거가 되는 문장(또는 문단)을 반드시 '원문 그대로 인용'해서 답변하세요. 요약, 의역, 추가 설명 없이 참고 정보의 문장(또는 문단)을 그대로 복사해서 답변하세요. 참고 정보에 없는 내용은 '참고 정보에 없습니다'라고 답하세요.

[참고 정보]
{context}

질문: {query}
답변:""",
    
    'en': """Please answer by 'directly quoting' the relevant sentence(s) or paragraph(s) from the reference information below. Do NOT summarize, paraphrase, or add extra explanation. Just copy the original sentence(s) or paragraph(s) as is. If the information is not in the reference, answer 'Information not found in the reference.'

[Reference Information]
{context}

Question: {query}
Answer:""",
    
    'ja': """以下の参考情報から、回答の根拠となる文や段落を必ず『原文のまま引用』して答えてください。要約・意訳・追加説明はせず、参考情報の文や段落をそのままコピーして答えてください。参考情報にない内容は「参考情報にありません」と答えてください。

[参考情報]
{context}

質問: {query}
回答:""",
    
    'zh': """请务必从以下参考信息中'原文引用'相关句子或段落进行回答。不要总结、意译或添加额外说明，只需原样复制参考信息中的句子或段落。如果参考信息中没有相关内容，请回答"参考信息中没有"。

[参考信息]
{context}

问题: {query}
回答:""",
    
    'vi': """Vui lòng trả lời bằng cách 'trích dẫn nguyên văn' câu hoặc đoạn liên quan từ thông tin tham khảo dưới đây. Không tóm tắt, diễn giải hoặc thêm giải thích. Chỉ cần sao chép nguyên văn câu hoặc đoạn từ tài liệu tham khảo. Nếu không có thông tin, hãy trả lời 'Không tìm thấy thông tin trong tài liệu tham khảo.'

[Thông tin tham khảo]
{context}

Câu hỏi: {query}
Trả lời:""",
    
    'fr': """Veuillez répondre en 'citant textuellement' la ou les phrases ou paragraphes pertinents des informations de référence ci-dessous. Ne résumez pas, ne paraphrasez pas et n'ajoutez pas d'explications supplémentaires. Copiez simplement la ou les phrases ou paragraphes originaux tels quels. Si l'information ne se trouve pas dans la référence, répondez 'Information non trouvée dans la référence.'

[Informations de référence]
{context}

Question: {query}
Réponse:""",
    
    'de': """Bitte antworten Sie, indem Sie den/die relevanten Satz/Sätze oder Absatz/Absätze aus den folgenden Referenzinformationen 'wortwörtlich zitieren'. Fassen Sie nicht zusammen, paraphrasieren Sie nicht und fügen Sie keine zusätzlichen Erklärungen hinzu. Kopieren Sie einfach den Originalsatz oder Absatz. Wenn die Information nicht in der Referenz steht, antworten Sie bitte 'Information nicht in der Referenz gefunden.'

[Referenzinformationen]
{context}

Frage: {query}
Antwort:""",
    
    'th': """กรุณาตอบโดย 'คัดลอกข้อความต้นฉบับ' ประโยคหรือย่อหน้าที่เกี่ยวข้องจากข้อมูลอ้างอิงด้านล่าง ห้ามสรุปความ แปลความ หรืออธิบายเพิ่มเติม ให้คัดลอกข้อความต้นฉบับเท่านั้น หากไม่มีข้อมูลในเอกสารอ้างอิง กรุณาตอบว่า 'ไม่พบข้อมูลในเอกสารอ้างอิง'

[ข้อมูลอ้างอิง]
{context}

คำถาม: {query}
คำตอบ:"""
}

# 언어별 오류 메시지
ERROR_MESSAGES = {
    'ko': {
        'no_chunks': '참고 정보에서 관련 내용을 찾을 수 없습니다.',
        'empty_response': '답변을 생성하지 못했습니다. (OpenAI 응답이 비어 있음)',
        'auth_error': 'OpenAI API 인증에 실패했습니다. API Key를 확인해주세요.',
        'rate_limit': 'OpenAI API 요청 제한에 도달했습니다. 잠시 후 다시 시도해주세요.',
        'api_error': 'OpenAI API 오류가 발생했습니다: {error}',
        'unknown_error': '답변 생성 중 오류가 발생했습니다: {error}'
    },
    'en': {
        'no_chunks': 'No relevant information found in the reference.',
        'empty_response': 'Failed to generate response. (OpenAI response is empty)',
        'auth_error': 'OpenAI API authentication failed. Please check your API Key.',
        'rate_limit': 'OpenAI API rate limit reached. Please try again later.',
        'api_error': 'OpenAI API error occurred: {error}',
        'unknown_error': 'An error occurred while generating response: {error}'
    },
    'ja': {
        'no_chunks': '参考情報に関連する内容が見つかりません。',
        'empty_response': '回答の生成に失敗しました。（OpenAIの応答が空です）',
        'auth_error': 'OpenAI API認証に失敗しました。API Keyを確認してください。',
        'rate_limit': 'OpenAI APIリクエスト制限に達しました。しばらくしてから再試行してください。',
        'api_error': 'OpenAI APIエラーが発生しました: {error}',
        'unknown_error': '回答生成中にエラーが発生しました: {error}'
    },
    'zh': {
        'no_chunks': '在参考信息中找不到相关内容。',
        'empty_response': '无法生成回答。（OpenAI响应为空）',
        'auth_error': 'OpenAI API认证失败。请检查您的API密钥。',
        'rate_limit': '达到OpenAI API请求限制。请稍后重试。',
        'api_error': '发生OpenAI API错误: {error}',
        'unknown_error': '生成回答时发生错误: {error}'
    },
    'vi': {
        'no_chunks': 'Không tìm thấy thông tin liên quan trong tài liệu tham khảo.',
        'empty_response': 'Không thể tạo phản hồi. (Phản hồi OpenAI trống)',
        'auth_error': 'Xác thực OpenAI API thất bại. Vui lòng kiểm tra API Key của bạn.',
        'rate_limit': 'Đã đạt giới hạn yêu cầu OpenAI API. Vui lòng thử lại sau.',
        'api_error': 'Lỗi OpenAI API xảy ra: {error}',
        'unknown_error': 'Đã xảy ra lỗi khi tạo phản hồi: {error}'
    },
    'fr': {
        'no_chunks': 'Aucune information pertinente trouvée dans la référence.',
        'empty_response': 'Échec de la génération de la réponse. (Réponse OpenAI vide)',
        'auth_error': 'Échec de l\'authentification OpenAI API. Veuillez vérifier votre clé API.',
        'rate_limit': 'Limite de taux OpenAI API atteinte. Veuillez réessayer plus tard.',
        'api_error': 'Erreur OpenAI API survenue: {error}',
        'unknown_error': 'Une erreur s\'est produite lors de la génération de la réponse: {error}'
    },
    'de': {
        'no_chunks': 'Keine relevanten Informationen in der Referenz gefunden.',
        'empty_response': 'Antwortgenerierung fehlgeschlagen. (OpenAI-Antwort ist leer)',
        'auth_error': 'OpenAI API-Authentifizierung fehlgeschlagen. Bitte überprüfen Sie Ihren API-Schlüssel.',
        'rate_limit': 'OpenAI API-Ratenlimit erreicht. Bitte versuchen Sie es später erneut.',
        'api_error': 'OpenAI API-Fehler aufgetreten: {error}',
        'unknown_error': 'Fehler bei der Antwortgenerierung aufgetreten: {error}'
    },
    'th': {
        'no_chunks': 'ไม่พบข้อมูลที่เกี่ยวข้องในเอกสารอ้างอิง',
        'empty_response': 'ไม่สามารถสร้างคำตอบได้ (การตอบสนองของ OpenAI ว่างเปล่า)',
        'auth_error': 'การยืนยันตัวตน OpenAI API ล้มเหลว กรุณาตรวจสอบ API Key ของคุณ',
        'rate_limit': 'ถึงขีดจำกัดการร้องขอ OpenAI API แล้ว กรุณาลองใหม่อีกครั้ง',
        'api_error': 'เกิดข้อผิดพลาด OpenAI API: {error}',
        'unknown_error': 'เกิดข้อผิดพลาดในการสร้างคำตอบ: {error}'
    }
}

# 파일 해시 계산 함수
def calculate_file_hash(file_path):
    """파일의 MD5 해시를 계산합니다."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# 캐시 정보 저장/로드 함수
def save_cache_info(file_hash, chunk_count):
    """캐시 정보를 JSON 파일로 저장합니다."""
    cache_info = {
        "file_hash": file_hash,
        "chunk_count": chunk_count,
        "created_at": str(os.path.getctime(PDF_PATH))
    }
    with open(CACHE_INFO_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache_info, f, ensure_ascii=False, indent=2)

def load_cache_info():
    """캐시 정보를 JSON 파일에서 로드합니다."""
    if not os.path.exists(CACHE_INFO_PATH):
        return None
    try:
        with open(CACHE_INFO_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None

def is_cache_valid():
    """현재 PDF 파일의 해시와 캐시된 해시를 비교하여 캐시가 유효한지 확인합니다."""
    if not os.path.exists(PDF_PATH):
        print(f"PDF 파일이 존재하지 않습니다: {PDF_PATH}")
        return False
    
    if not os.path.exists(VECTOR_DB_PATH):
        print("벡터DB 파일이 존재하지 않습니다.")
        return False
    
    current_hash = calculate_file_hash(PDF_PATH)
    cache_info = load_cache_info()
    
    if cache_info is None:
        print("캐시 정보가 없습니다.")
        return False
    
    if cache_info.get("file_hash") != current_hash:
        print(f"PDF 파일이 변경되었습니다. (이전 해시: {cache_info.get('file_hash')[:8]}..., 현재 해시: {current_hash[:8]}...)")
        return False
    
    print(f"캐시가 유효합니다. (파일 해시: {current_hash[:8]}...)")
    return True

# 1. PDF 청크 분할 함수 (pypdf 사용)
def chunk_pdf_to_text_chunks(pdf_path, chunk_size=1000, chunk_overlap=100):
    """PDF를 텍스트 청크로 분할합니다."""
    reader = PdfReader(pdf_path)
    text_chunks = []
    
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text.strip():
            continue
            
        # 텍스트를 청크로 분할
        words = text.split()
        current_chunk = ""
        chunks = []
        
        for word in words:
            if len(current_chunk) + len(word) + 1 <= chunk_size:
                current_chunk += (word + " ")
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = word + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # 청크 오버랩 처리
        final_chunks = []
        for i, chunk in enumerate(chunks):
            if i > 0 and chunk_overlap > 0:
                # 이전 청크의 끝 부분을 현재 청크 앞에 추가
                overlap_text = chunks[i-1][-chunk_overlap:] if len(chunks[i-1]) > chunk_overlap else chunks[i-1]
                chunk = overlap_text + " " + chunk
            
            # Document 객체 대신 딕셔너리 사용
            final_chunks.append({
                'page_content': chunk,
                'metadata': {'page': page_num + 1}
            })
        
        text_chunks.extend(final_chunks)
    
    return text_chunks

# 간단한 벡터DB 클래스
class SimpleVectorDB:
    def __init__(self, documents, embeddings=None, doc_embeddings=None):
        self.documents = documents
        self.embeddings = embeddings
        self.doc_embeddings = doc_embeddings
    
    def similarity_search(self, query, k=3):
        if self.embeddings is None:
            print("임베딩 객체가 없습니다. 새로 생성합니다...")
            # 임베딩 객체를 다시 생성해야 하는 경우
            return self.documents[:k]
        
        # 쿼리 임베딩 생성
        query_embedding = self.embeddings.embed_query(query)
        
        # 문서 텍스트 추출 (다양한 형식 지원)
        doc_texts = []
        for doc in self.documents:
            if isinstance(doc, dict) and 'page_content' in doc:
                # 딕셔너리 형식
                doc_texts.append(doc['page_content'])
            elif hasattr(doc, 'page_content'):
                # Document 객체 형식
                doc_texts.append(doc.page_content)
            elif isinstance(doc, str):
                # 문자열 형식
                doc_texts.append(doc)
            else:
                # 기타 형식은 문자열로 변환
                doc_texts.append(str(doc))
        
        # 코사인 유사도 계산
        similarities = []
        for doc_embedding in self.embeddings.embed_documents(doc_texts):
            similarity = np.dot(query_embedding, doc_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding))
            similarities.append(similarity)
        
        # 상위 k개 문서 반환
        top_indices = np.argsort(similarities)[-k:][::-1]
        return [self.documents[i] for i in top_indices]
    
    def __getstate__(self):
        # pickle 저장 시 임베딩 객체 제외
        state = self.__dict__.copy()
        state['embeddings'] = None  # 임베딩 객체는 저장하지 않음
        return state
    
    def __setstate__(self, state):
        # pickle 로드 시 임베딩 객체는 None으로 유지
        self.__dict__.update(state)

# OpenAI 임베딩 클래스
class OpenAIEmbeddings:
    def __init__(self, openai_api_key, model="text-embedding-3-small"):
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.model = model
    
    def embed_query(self, text):
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
    
    def embed_documents(self, texts):
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [data.embedding for data in response.data]

# 2. 임베딩 및 벡터DB 저장/로드 함수
def get_or_create_vector_db(openai_api_key):
    # 벡터DB 파일 존재 확인
    print(f"벡터DB 파일 확인: {VECTOR_DB_PATH}")
    if not os.path.exists(VECTOR_DB_PATH):
        print(f"❌ 벡터DB 파일이 존재하지 않습니다: {VECTOR_DB_PATH}")
        print(f"현재 작업 디렉토리: {os.getcwd()}")
        print(f"벡터DB 파일 절대 경로: {os.path.abspath(VECTOR_DB_PATH)}")
        return None
    
    print(f"✅ 벡터DB 파일 확인됨: {os.path.abspath(VECTOR_DB_PATH)}")
    print(f"벡터DB 파일 크기: {os.path.getsize(VECTOR_DB_PATH)} bytes")
    
    # 캐시 유효성 검사
    if is_cache_valid():
        print("유효한 캐시가 있어 기존 벡터DB를 로드합니다...")
        try:
            with open(VECTOR_DB_PATH, 'rb') as f:
                vector_db = pickle.load(f)
            # 임베딩 객체 다시 생성 (절대 변경 불가)
            embeddings = OpenAIEmbeddings(
                openai_api_key=openai_api_key,
                model="text-embedding-3-small"
            )
            vector_db.embeddings = embeddings
            cache_info = load_cache_info()
            print(f"벡터DB 로드 완료 (청크 수: {cache_info.get('chunk_count', '알 수 없음')})")
            return vector_db
        except Exception as e:
            print(f"벡터DB 로드 실패: {e}")
            print("새로 생성합니다...")
    
    # 캐시가 유효하지 않으면 새로 생성
    print("새로운 임베딩을 생성합니다...")
    
    # 기존 파일 삭제 (있다면)
    for file_path in [VECTOR_DB_PATH, CACHE_INFO_PATH]:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"기존 파일 삭제: {file_path}")
    
    # 새로운 임베딩 생성 (절대 변경 불가)
    print("PDF 청크 분할 시작...")
    pdf_chunks = chunk_pdf_to_text_chunks(PDF_PATH)
    print(f"PDF 청크 개수: {len(pdf_chunks)}")
    
    # 청크 미리보기 (처음 3개만)
    for i, chunk in enumerate(pdf_chunks[:3]):
        print(f"--- 청크 {i+1} ---\n{chunk['page_content'][:200]}\n")
    
    print("OpenAI 임베딩 생성 시작...")
    embeddings = OpenAIEmbeddings(
        openai_api_key=openai_api_key,
        model="text-embedding-3-small"
    )
    
    # 모든 문서의 임베딩을 미리 생성
    print("문서 임베딩 생성 중...")
    doc_embeddings = embeddings.embed_documents([doc['page_content'] for doc in pdf_chunks])
    
    print("벡터DB 생성 중...")
    vector_db = SimpleVectorDB(pdf_chunks, embeddings, doc_embeddings)
    
    # 벡터DB 저장
    print("벡터DB 저장 중...")
    with open(VECTOR_DB_PATH, 'wb') as f:
        pickle.dump(vector_db, f)
    
    # 캐시 정보 저장
    file_hash = calculate_file_hash(PDF_PATH)
    save_cache_info(file_hash, len(pdf_chunks))
    
    print(f"새로운 벡터DB 생성 및 저장 완료 (청크 수: {len(pdf_chunks)})")
    print(f"파일 해시: {file_hash[:8]}...")
    
    return vector_db

# 캐시 관리 유틸리티 함수들
def get_cache_status():
    """현재 캐시 상태를 반환합니다."""
    if not os.path.exists(VECTOR_DB_PATH):
        return {"status": "not_exists", "message": "벡터DB가 존재하지 않습니다."}
    
    cache_info = load_cache_info()
    if cache_info is None:
        return {"status": "no_cache_info", "message": "캐시 정보가 없습니다."}
    
    current_hash = calculate_file_hash(PDF_PATH)
    is_valid = cache_info.get("file_hash") == current_hash
    
    return {
        "status": "valid" if is_valid else "invalid",
        "current_hash": current_hash[:8] + "...",
        "cached_hash": cache_info.get("file_hash", "")[:8] + "...",
        "chunk_count": cache_info.get("chunk_count"),
        "created_at": cache_info.get("created_at"),
        "is_valid": is_valid
    }

def force_rebuild_cache(openai_api_key):
    """캐시를 강제로 재생성합니다."""
    print("캐시를 강제로 재생성합니다...")
    if os.path.exists(VECTOR_DB_PATH):
        os.remove(VECTOR_DB_PATH)
        print("기존 벡터DB를 삭제했습니다.")
    
    return get_or_create_vector_db(openai_api_key)

def clear_cache():
    """캐시를 완전히 삭제합니다."""
    if os.path.exists(VECTOR_DB_PATH):
        os.remove(VECTOR_DB_PATH)
        print("캐시가 완전히 삭제되었습니다.")
    else:
        print("삭제할 캐시가 없습니다.")

# 3. 유사 청크 검색 함수
def retrieve_relevant_chunks(query, vector_db, k=3):
    print(f"  - 유사 청크 검색 시작 (k={k})")
    try:
        docs = vector_db.similarity_search(query, k=k)
        print(f"  - 유사 청크 검색 완료: {len(docs)}개 찾음")
        return docs
    except Exception as e:
        print(f"  - ❌ 유사 청크 검색 실패: {e}")
        return []

def insert_linebreaks(text, max_length=60):
    result = ""
    line = ""
    for sentence in re.split(r'([.!?]\s+)', text):  # 문장 단위로 분리
        if not sentence.strip():
            continue
        if len(line) + len(sentence) > max_length:
            result += line.strip() + "\n"
            line = sentence
        else:
            line += sentence
    result += line.strip()
    # 쉼표 등에서도 추가로 줄바꿈
    result = re.sub(r'([,，])\s*', '\1\n', result)
    return result

# 4. RAG 답변 생성 함수
def answer_with_rag(query, vector_db, openai_api_key, model=None):
    # OpenAI 답변 모델을 절대 변경하지 않음
    model = "gpt-4.1-nano-2025-04-14"
    print(f"  - RAG 답변 생성 시작")

    # 질문 언어 감지
    lang = detect_language(query)
    print(f"  - 감지된 언어: {lang}")
    prompt_template = LANGUAGE_PROMPTS.get(lang, LANGUAGE_PROMPTS['en'])
    error_msg = ERROR_MESSAGES.get(lang, ERROR_MESSAGES['en'])

    # 1단계: 유사 청크 검색
    print(f"  - 1단계: 유사 청크 검색")
    relevant_chunks = retrieve_relevant_chunks(query, vector_db)

    if not relevant_chunks:
        print(f"  - ❌ 유사한 청크를 찾지 못했습니다.")
        return error_msg['no_chunks']

    # 2단계: 컨텍스트 생성
    print(f"  - 2단계: 컨텍스트 생성")
    context_parts = []
    for doc in relevant_chunks:
        if isinstance(doc, dict) and 'page_content' in doc:
            # 딕셔너리 형식
            context_parts.append(doc['page_content'])
        elif hasattr(doc, 'page_content'):
            # Document 객체 형식
            context_parts.append(doc.page_content)
        elif isinstance(doc, str):
            # 문자열 형식
            context_parts.append(doc)
        else:
            # 기타 형식은 문자열로 변환
            context_parts.append(str(doc))
    
    context = "\n\n".join(context_parts)
    print(f"  - 컨텍스트 길이: {len(context)} 문자")

    # 3단계: 프롬프트 생성
    print(f"  - 3단계: 프롬프트 생성")
    prompt = prompt_template.format(context=context, query=query)
    print(f"  - 프롬프트 길이: {len(prompt)} 문자")

    # 4단계: OpenAI API 호출
    print(f"  - 4단계: OpenAI API 호출 (모델: {model})")
    try:
        client = openai.OpenAI(api_key=openai_api_key)
        print(f"  - OpenAI 클라이언트 생성 완료")

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.1
        )
        print(f"  - OpenAI API 응답 수신 완료")

        answer = response.choices[0].message.content.strip()
        print(f"  - 응답 길이: {len(answer)} 문자")
        if not answer:
            print(f"  - ❌ OpenAI 응답이 비어있습니다.")
            return error_msg['empty_response']
        # 줄바꿈 후처리
        answer = insert_linebreaks(answer, max_length=60)
        print(f"  - ✅ RAG 답변 생성 완료")
        return answer

    except openai.AuthenticationError as e:
        print(f"  - ❌ OpenAI 인증 오류: {e}")
        return error_msg['auth_error']
    except openai.RateLimitError as e:
        print(f"  - ❌ OpenAI 요청 제한 오류: {e}")
        return error_msg['rate_limit']
    except openai.APIError as e:
        print(f"  - ❌ OpenAI API 오류: {e}")
        return error_msg['api_error'].format(error=e)
    except Exception as e:
        print(f"  - ❌ 예상치 못한 오류: {e}")
        return error_msg['unknown_error'].format(error=e)

def get_or_create_vector_db_multi(pdf_paths, openai_api_key):
    """여러 PDF를 한 번에 임베딩해서 하나의 벡터DB로 저장합니다."""
    all_chunks = []
    for pdf_path in pdf_paths:
        if not os.path.exists(pdf_path):
            print(f"❌ PDF 파일이 존재하지 않습니다: {pdf_path}")
            continue
        print(f"✅ PDF 파일 확인됨: {os.path.abspath(pdf_path)}")
        chunks = chunk_pdf_to_text_chunks(pdf_path)
        all_chunks.extend(chunks)
        print(f"{pdf_path} → 청크 {len(chunks)}개")
    print(f"총 청크 개수: {len(all_chunks)}")
    if not all_chunks:
        print("❌ 임베딩할 청크가 없습니다.")
        return None
    embeddings = OpenAIEmbeddings(
        openai_api_key=openai_api_key,
        model="text-embedding-3-small"
    )
    doc_embeddings = embeddings.embed_documents([doc['page_content'] for doc in all_chunks])
    vector_db = SimpleVectorDB(all_chunks, embeddings, doc_embeddings)
    with open("vector_db_multi.pkl", "wb") as f:
        pickle.dump(vector_db, f)
    print("벡터DB 저장 완료: vector_db_multi.pkl")
    return vector_db

def merge_vector_dbs(db_paths, openai_api_key, save_path="vector_db_merged.pkl"):
    """여러 벡터DB(pkl)를 병합하여 하나의 벡터DB로 만듭니다."""
    all_chunks = []
    for db_path in db_paths:
        if not os.path.exists(db_path):
            print(f"❌ DB 파일이 존재하지 않습니다: {db_path}")
            continue
        with open(db_path, "rb") as f:
            db = pickle.load(f)
            all_chunks.extend(db.documents)
    print(f"총 합쳐진 청크 개수: {len(all_chunks)}")
    if not all_chunks:
        print("❌ 합칠 청크가 없습니다.")
        return None
    embeddings = OpenAIEmbeddings(
        openai_api_key=openai_api_key,
        model="text-embedding-3-small"
    )
    doc_embeddings = embeddings.embed_documents([doc['page_content'] for doc in all_chunks])
    vector_db = SimpleVectorDB(all_chunks, embeddings, doc_embeddings)
    with open(save_path, "wb") as f:
        pickle.dump(vector_db, f)
    print(f"병합 벡터DB 저장 완료: {save_path}")
    return vector_db

if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    
    # API Key 디버깅
    print("=== API Key 확인 ===")
    if not api_key:
        print("❌ 환경변수 OPENAI_API_KEY가 설정되어 있지 않습니다.")
        print("환경변수 설정 방법:")
        print("Windows: set OPENAI_API_KEY=your-api-key-here")
        print("Linux/Mac: export OPENAI_API_KEY=your-api-key-here")
        exit(1)
    else:
        print(f"✅ API Key 확인됨: {api_key[:10]}...{api_key[-4:]}")
    
    # 캐시 상태 확인
    print("\n=== 캐시 상태 확인 ===")
    cache_status = get_cache_status()
    print(f"상태: {cache_status['status']}")
    print(f"메시지: {cache_status.get('message', '')}")
    if 'current_hash' in cache_status:
        print(f"현재 파일 해시: {cache_status['current_hash']}")
        print(f"캐시된 파일 해시: {cache_status['cached_hash']}")
        print(f"청크 수: {cache_status['chunk_count']}")
    
    print("\n=== 벡터DB 준비 ===")
    vector_db = get_or_create_vector_db(api_key)
    print("임베딩/DB 준비 완료!")

    # 직접 질문 입력 반복
    while True:
        query = input("\n질문을 입력하세요(엔터만 입력 시 종료): ").strip()
        if not query:
            print("종료합니다.")
            break
        
        print(f"\n질문: {query}")
        print("유사 청크 검색 중...")
        docs = retrieve_relevant_chunks(query, vector_db)
        print(f"찾은 유사 청크 수: {len(docs)}")
        
        print("\n유사 청크 미리보기:")
        for i, doc in enumerate(docs):
            print(f"--- 청크 {i+1} ---\n{doc['page_content'][:300]}\n")
        
        print("OpenAI API로 답변 생성 중...")
        answer = answer_with_rag(query, vector_db, api_key)
        print(f"\nRAG 답변: {answer}\n") 

    # 1~64.pdf 임베딩 및 저장
    pdf_paths_64 = [f"pdf/{i}.pdf" for i in range(1, 65)]
    get_or_create_vector_db_multi(pdf_paths_64, api_key)
    # 64개 PDF 임베딩 결과를 별도 파일로 저장
    shutil.copy("vector_db_multi.pkl", "vector_db_64multi.pkl")
    # 기존 단일 PDF DB와 병합
    db_paths = ["vector_db.pkl", "vector_db_64multi.pkl"]
    merge_vector_dbs(db_paths, api_key, save_path="vector_db_merged.pkl") 