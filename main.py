import os
import pickle
import shutil

# 환경변수에서 firebase_key.json 내용을 읽어서 파일로 저장
firebase_key_json = os.getenv("FIREBASE_KEY_JSON")
if firebase_key_json:
    with open("firebase_key.json", "w", encoding="utf-8") as f:
        f.write(firebase_key_json)

# config.py가 없으면 환경변수로 자동 생성
if not os.path.exists("config.py"):
    with open("config.py", "w", encoding="utf-8") as f:
        f.write(f'''
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL", "https://pychat-25c45-default-rtdb.asia-southeast1.firebasedatabase.app/")
FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH", "firebase_key.json")
''')

import flet as ft
from flet_webview import WebView
from pages.nationality_select import NationalitySelectPage
from pages.home import HomePage
from pages.create_room import CreateRoomPage
from pages.room_list import RoomListPage
from pages.chat_room import ChatRoomPage
from pages.foreign_country_select import ForeignCountrySelectPage
import openai
from config import OPENAI_API_KEY, MODEL_NAME, FIREBASE_DB_URL, FIREBASE_KEY_PATH
import uuid
import qrcode
import io
import base64
import geocoder
import time
import firebase_admin
from firebase_admin import credentials, db
from rag_utils import get_or_create_vector_db, answer_with_rag
from rag_utils import SimpleVectorDB, OpenAIEmbeddings


IS_SERVER = os.environ.get("CLOUDTYPE") == "1"  # Cloudtype 환경변수 등으로 구분

# Cloudtype 배포 주소를 반드시 실제 주소로 바꿔주세요!
BASE_URL = "https://port-0-buchat-m0t1itev3f2879ad.sel4.cloudtype.app"

# RAG 채팅방 상수
RAG_ROOM_ID = "rag_korean_guide"
RAG_ROOM_TITLE = "다문화가족 한국생활안내"

# --- Firebase 초기화 ---
FIREBASE_AVAILABLE = False
try:
    print(f"Firebase 초기화 시도...")
    print(f"FIREBASE_DB_URL: {FIREBASE_DB_URL}")
    print(f"FIREBASE_KEY_PATH: {FIREBASE_KEY_PATH}")
    
    if not FIREBASE_DB_URL or FIREBASE_DB_URL == "None":
        print("❌ FIREBASE_DB_URL이 설정되지 않았습니다.")
        raise Exception("FIREBASE_DB_URL is not set")
    
    if not os.path.exists(FIREBASE_KEY_PATH):
        print(f"❌ Firebase 키 파일이 존재하지 않습니다: {FIREBASE_KEY_PATH}")
        raise Exception(f"Firebase key file not found: {FIREBASE_KEY_PATH}")
    
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DB_URL
    })
    FIREBASE_AVAILABLE = True
    print("✅ Firebase 초기화 성공")
except Exception as e:
    print(f"❌ Firebase 초기화 실패: {e}")
    print("⚠️ Firebase 기능이 비활성화됩니다. 채팅방 생성 및 메시지 저장이 불가능합니다.")
    FIREBASE_AVAILABLE = False

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# RAG용 벡터DB 준비 (무조건 병합본만 사용)
print("RAG 벡터DB 준비 중...")
VECTOR_DB_MERGED_PATH = "vector_db_merged.pkl"
vector_db = None

try:
    if os.path.exists(VECTOR_DB_MERGED_PATH):
        print("기존 벡터DB 파일을 로드합니다...")
        with open(VECTOR_DB_MERGED_PATH, "rb") as f:
            vector_db = pickle.load(f)
        # 임베딩 객체 다시 생성
        vector_db.embeddings = OpenAIEmbeddings(
            openai_api_key=OPENAI_API_KEY,
            model="text-embedding-3-small"
        )
        print("기존 병합 벡터DB 로드 완료!")
    else:
        print("벡터DB 파일이 없습니다.")
        print("RAG 기능이 비활성화됩니다.")
except Exception as e:
    print(f"벡터DB 로드 중 오류 발생: {e}")
    if "langchain" in str(e).lower():
        print("langchain 의존성 오류로 인해 기존 벡터DB를 변환합니다...")
        try:
            # 기존 벡터DB 파일을 백업
            backup_path = VECTOR_DB_MERGED_PATH + ".backup"
            if os.path.exists(VECTOR_DB_MERGED_PATH):
                shutil.copy2(VECTOR_DB_MERGED_PATH, backup_path)
                print(f"기존 벡터DB 백업 완료: {backup_path}")
            
            # 기존 벡터DB에서 데이터 추출
            with open(VECTOR_DB_MERGED_PATH, 'rb') as f:
                old_db = pickle.load(f)
            
            print("기존 벡터DB에서 데이터 추출 중...")
            
            # 기존 벡터DB에서 문서 추출
            documents = []
            if hasattr(old_db, 'documents'):
                documents = old_db.documents
                print(f"기존 문서 수: {len(documents)}")
            elif hasattr(old_db, 'docstore') and hasattr(old_db.docstore, '_dict'):
                # ChromaDB 형식에서 문서 추출
                for doc_id, doc in old_db.docstore._dict.items():
                    if hasattr(doc, 'page_content') and hasattr(doc, 'metadata'):
                        documents.append({
                            'page_content': doc.page_content,
                            'metadata': doc.metadata
                        })
                print(f"추출된 문서 수: {len(documents)}")
            
            if documents:
                # 새로운 임베딩 생성
                from rag_utils import SimpleVectorDB
                embeddings = OpenAIEmbeddings(
                    openai_api_key=OPENAI_API_KEY,
                    model="text-embedding-3-small"
                )
                
                # 문서 임베딩 생성
                print("새로운 임베딩 생성 중...")
                doc_embeddings = embeddings.embed_documents([doc['page_content'] for doc in documents])
                
                # SimpleVectorDB 생성
                vector_db = SimpleVectorDB(documents, embeddings, doc_embeddings)
                
                # 새로운 벡터DB 저장
                with open(VECTOR_DB_MERGED_PATH, "wb") as f:
                    pickle.dump(vector_db, f)
                
                # 변환 완료 표시
                with open(VECTOR_DB_MERGED_PATH + ".converted", "w") as f:
                    f.write("converted")
                print("벡터DB 변환 완료!")
            else:
                print("추출할 문서가 없습니다.")
                vector_db = None
                
        except Exception as e2:
            print(f"벡터DB 변환 실패: {e2}")
            vector_db = None
    else:
        print("RAG 기능이 비활성화됩니다.")
        vector_db = None

# RAG 기능 사용 가능 여부 설정 (vector_db 정의 후)
RAG_AVAILABLE = vector_db is not None

print("RAG 벡터DB 준비 완료!")

FIND_ROOM_TEXTS = {
    "ko": {
        "title": "채팅방 찾기 방법을 선택하세요",
        "id": "ID로 찾기",
        "id_desc": "채팅방 ID를 입력하여 참여",
        "qr": "QR코드로 찾기",
        "qr_desc": "QR 코드를 스캔하여 빠른 참여",
        "rag": "다문화가족 한국생활안내",
        "rag_desc": "공식 안내 채팅방"
    },
    "en": {
        "title": "Select a way to find a chat room",
        "id": "Find by ID",
        "id_desc": "Join by entering chat room ID",
        "qr": "Find by QR code",
        "qr_desc": "Quick join by scanning QR code",
        "rag": "Korean Life Guide for Multicultural Families",
        "rag_desc": "Official guide chat room"
    },
    "vi": {
        "title": "Chọn cách tìm phòng chat",
        "id": "Tìm bằng ID",
        "id_desc": "Tham gia bằng cách nhập ID phòng chat",
        "qr": "Tìm bằng mã QR",
        "qr_desc": "Tham gia nhanh bằng quét mã QR",
        "rag": "Hướng dẫn cuộc sống Hàn Quốc cho gia đình đa văn hóa",
        "rag_desc": "Phòng chat hướng dẫn chính thức"
    },
    "ja": {
        "title": "チャットルームの探し方を選択してください",
        "id": "IDで探す",
        "id_desc": "IDでチャットルームに参加",
        "qr": "QRコードで探す",
        "qr_desc": "QRコードをスキャンして参加",
        "rag": "多文化家族のための韓国生活ガイド",
        "rag_desc": "公式ガイドチャットルーム"
    },
    "zh": {
        "title": "请选择查找聊天室的方法",
        "id": "通过ID查找",
        "id_desc": "通过输入聊天室ID加入",
        "qr": "通过二维码查找",
        "qr_desc": "扫描二维码快速加入",
        "rag": "多文化家庭韩国生活指南",
        "rag_desc": "官方指南聊天室"
    },
    "fr": {
        "title": "Sélectionnez une méthode pour trouver un salon de discussion",
        "id": "Rechercher par ID",
        "id_desc": "Rejoindre en entrant l'ID de la salle de discussion",
        "qr": "Rechercher par QR code",
        "qr_desc": "Rejoindre rapidement en scanant le code QR",
        "rag": "Guide de la vie en Corée pour les familles multiculturelles",
        "rag_desc": "Salon de discussion guide officiel"
    },
    "de": {
        "title": "Wählen Sie eine Methode, um einen Chatraum zu finden",
        "id": "Nach ID suchen",
        "id_desc": "Beitreten, indem Sie die Chatraum-ID eingeben",
        "qr": "Mit QR-Code suchen",
        "qr_desc": "Schnell beitreten, indem Sie den QR-Code scannen",
        "rag": "Koreanischer Lebensratgeber für multikulturelle Familien",
        "rag_desc": "Offizieller Guide-Chatraum"
    },
    "th": {
        "title": "เลือกวิธีค้นหาห้องแชท",
        "id": "ค้นหาด้วย ID",
        "id_desc": "เข้าร่วมโดยการป้อน IDห้องแชท",
        "qr": "ค้นหาด้วย QR โค้ด",
        "qr_desc": "เข้าร่วมอย่างรวดเร็วโดยสแกน QR โค้ด",
        "rag": "คู่มือการใช้ชีวิตในเกาหลีสำหรับครอบครัวพหุวัฒนธรรม",
        "rag_desc": "ห้องแชทคู่มือการใช้ชีวิตระบบองค์กรสำหรับครอบครัวพหุวัฒนธรรม"
    },
    "zh-TW": {
        "title": "請選擇查找聊天室的方法",
        "id": "通過ID查找",
        "id_desc": "輸入聊天室ID參加",
        "qr": "通過二維碼查找",
        "qr_desc": "掃描二維碼快速參加",
        "rag": "多元文化家庭韓國生活指南",
        "rag_desc": "官方指南聊天室"
    },
    "id": {
        "title": "Pilih cara menemukan ruang obrolan",
        "id": "Cari dengan ID",
        "id_desc": "Gabung dengan memasukkan ID ruang obrolan",
        "qr": "Cari dengan kode QR",
        "qr_desc": "Gabung cepat dengan memindai kode QR",
        "rag": "Panduan Hidup di Korea untuk Keluarga Multikultural",
        "rag_desc": "Ruang obrolan panduan resmi"
    },
}

# 닉네임 입력 화면 다국어 지원
NICKNAME_TEXTS = {
    "ko": {"title": "닉네임 설정", "desc": "다른 사용자들에게 보여질 이름을 설정해주세요", "label": "닉네임", "hint": "닉네임을 입력하세요", "enter": "채팅방 입장", "back": "뒤로가기"},
    "en": {"title": "Set Nickname", "desc": "Set a name to show to other users", "label": "Nickname", "hint": "Enter your nickname", "enter": "Enter Chat Room", "back": "Back"},
    "ja": {"title": "ニックネーム設定", "desc": "他のユーザーに表示される名前を設定してください", "label": "ニックネーム", "hint": "ニックネームを入力してください", "enter": "チャットルーム入室", "back": "戻る"},
    "zh": {"title": "设置昵称", "desc": "请设置将显示给其他用户的名称", "label": "昵称", "hint": "请输入昵称", "enter": "进入聊天室", "back": "返回"},
    "vi": {"title": "Đặt biệt danh", "desc": "Hãy đặt tên sẽ hiển thị cho người khác", "label": "Biệt danh", "hint": "Nhập biệt danh", "enter": "Vào phòng chat", "back": "Quay lại"},
    "fr": {"title": "Définir un pseudo", "desc": "Définissez un nom à afficher aux autres utilisateurs", "label": "Pseudo", "hint": "Entrez votre pseudo", "enter": "Entrer dans le salon", "back": "Retour"},
    "de": {"title": "Spitznamen festlegen", "desc": "Legen Sie einen Namen fest, der anderen angezeigt wird", "label": "Spitzname", "hint": "Spitznamen eingeben", "enter": "Chatraum betreten", "back": "Zurück"},
    "th": {"title": "ตั้งชื่อเล่น", "desc": "ตั้งชื่อที่จะแสดงให้ผู้อื่นเห็น", "label": "ชื่อเล่น", "hint": "กรอกชื่อเล่น", "enter": "เข้าสู่ห้องแชท", "back": "ย้อนกลับ"},
    "zh-TW": {
        "title": "設定暱稱",
        "desc": "請設定將顯示給其他用戶的名稱",
        "label": "暱稱",
        "hint": "請輸入暱稱",
        "enter": "進入聊天室",
        "back": "返回"
    },
    "id": {
        "title": "Atur Nama Panggilan",
        "desc": "Atur nama yang akan ditampilkan ke pengguna lain",
        "label": "Nama Panggilan",
        "hint": "Masukkan nama panggilan",
        "enter": "Masuk ke Ruang Obrolan",
        "back": "Kembali"
    },
}

def main(page: ft.Page):
    # 구글 폰트 링크 및 CSS 추가 (웹 환경에서 특수문자 깨짐 방지)
    page.html = """
    <link href='https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap' rel='stylesheet'>
    <style>
      body, * {
        font-family: 'Noto Sans KR', 'Malgun Gothic', 'Apple SD Gothic Neo', Arial, sans-serif !important;
      }
    </style>
    """
    page.font_family = "Noto Sans KR, Malgun Gothic, Apple SD Gothic Neo, Arial, sans-serif"
    print("앱 시작(main 함수 진입)")
    lang = "ko"
    country = None
    
    # --- QR 코드 관련 함수 (Container를 직접 오버레이) ---
    def show_qr_dialog(room_id, room_title):
        print(f"--- DEBUG: QR 코드 다이얼로그 생성 (Container 방식) ---")
        
        def close_dialog(e):
            if page.overlay:
                page.overlay.pop()
                page.update()

        # QR코드에 전체 URL이 들어가도록 수정
        qr_data = f"{BASE_URL}/join_room/{room_id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        qr_code_image = ft.Image(src_base64=img_str, width=250, height=250)

        # AlertDialog 대신, 성공했던 Container를 직접 꾸며서 사용합니다.
        popup_content = ft.Container(
            content=ft.Column([
                ft.Text(f"방 '{room_title}' 공유", size=20, weight=ft.FontWeight.BOLD),
                ft.Text("다른 사용자가 QR코드를 스캔하면 이 방으로 바로 참여할 수 있습니다."),
                qr_code_image,
                ft.Text(f"방 ID: {room_id}"),
                ft.ElevatedButton("닫기", on_click=close_dialog, width=300)
            ], tight=True, spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=350,
            padding=30,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK26)
        )

        # 화면 중앙에 팝업을 띄웁니다.
        page.overlay.append(
            ft.Container(
                content=popup_content,
                alignment=ft.alignment.center,
                expand=True
            )
        )
        page.update()

    def handle_create_room(room_title, target_lang):
        if not room_title:
            room_title = "새로운 채팅방"
        if not target_lang:
            target_lang = "en"
            print("상대방 언어가 선택되지 않아 기본값(en)으로 설정합니다.")

        new_room_id = uuid.uuid4().hex[:8]
        
        # Firebase 사용 가능 여부 확인
        if not FIREBASE_AVAILABLE:
            print("❌ Firebase가 초기화되지 않아 방을 생성할 수 없습니다.")
            # 사용자에게 오류 메시지 표시 (간단한 팝업)
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Firebase 연결 오류로 방을 생성할 수 없습니다. 설정을 확인해주세요."),
                    action="확인"
                )
            )
            return
        
        # Firebase에 방 정보 저장
        try:
            rooms_ref = db.reference('/rooms')
            rooms_ref.child(new_room_id).set({
                'id': new_room_id,
                'title': room_title,
                'user_lang': lang,
                'target_lang': target_lang,
                'created_at': int(time.time() * 1000)
            })
            print(f"✅ Firebase에 방 '{room_title}' 정보 저장 성공")
        except Exception as e:
            print(f"❌ Firebase 방 정보 저장 실패: {e}")
            # 사용자에게 오류 메시지 표시
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("방 생성 중 오류가 발생했습니다. 다시 시도해주세요."),
                    action="확인"
                )
            )
            return

        print(f"방 '{room_title}' 생성됨 (ID: {new_room_id}, 내 언어: {lang}, 상대 언어: {target_lang})")
        go_chat(lang, target_lang, new_room_id, room_title)

    # --- 화면 이동 함수 ---
    def go_home(selected_lang=None):
        nonlocal lang
        if selected_lang:
            lang = selected_lang
        page.views.clear()
        page.views.append(HomePage(page, lang,
            on_create=lambda e: go_create(lang),
            on_find=lambda e: go_room_list(lang, e),
            on_quick=lambda e: handle_create_room("빠른 채팅방", lang),
            on_change_lang=go_nationality, on_back=go_nationality))
        page.go("/home")

    def go_nationality(e=None):
        page.views.clear()
        page.views.append(NationalitySelectPage(page, on_select=go_home, on_foreign_select=go_foreign_country_select))
        page.go("/")

    def go_foreign_country_select(e=None):
        page.views.clear()
        page.views.append(ForeignCountrySelectPage(page, on_select=on_country_selected, on_back=go_nationality))
        page.go("/foreign_country_select")

    def on_country_selected(country_code, lang_code):
        nonlocal lang
        lang = lang_code
        go_home(lang)

    def go_create(lang):
        page.views.clear()
        page.views.append(CreateRoomPage(page, lang, on_create=handle_create_room, on_back=lambda e: go_home(lang)))
        page.go("/create_room")

    def go_room_list(lang, e=None):
        def on_find_by_id(e):
            go_find_by_id(lang)
        def on_find_by_qr(e):
            go_find_by_qr(lang)
        texts = FIND_ROOM_TEXTS.get(lang, FIND_ROOM_TEXTS["ko"])
        page.views.clear()
        # 사용자별 고유 RAG 방 ID 생성 (UUID 사용)
        user_id = page.session.get("user_id")
        if not user_id:
            user_id = str(uuid.uuid4())
            page.session.set("user_id", user_id)
        user_rag_room_id = f"{RAG_ROOM_ID}_{user_id}"
        page.views.append(
            ft.View(
                "/find_room_method",
                controls=[
                    # 헤더 (뒤로가기 + 타이틀)
                    ft.Row([
                        ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: go_home(lang)),
                        ft.Text(texts["title"], size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                    ], alignment=ft.MainAxisAlignment.START, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),

                    # 카드형 버튼들
                    ft.Container(
                        content=ft.Column([
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Icon(name=ft.Icons.TAG, color="#2563EB", size=28),
                                        bgcolor="#E0E7FF", border_radius=12, padding=10, margin=ft.margin.only(right=12)
                                    ),
                                    ft.Column([
                                        ft.Text(texts["id"], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                                        ft.Text(texts["id_desc"], size=12, color=ft.Colors.GREY_600)
                                    ], spacing=2)
                                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                bgcolor=ft.Colors.WHITE,
                                border_radius=12,
                                shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                                padding=16,
                                on_click=on_find_by_id
                            ),
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Icon(name=ft.Icons.QR_CODE, color="#A259FF", size=28),
                                        bgcolor="#F3E8FF", border_radius=12, padding=10, margin=ft.margin.only(right=12)
                                    ),
                                    ft.Column([
                                        ft.Text(texts["qr"], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                                        ft.Text(texts["qr_desc"], size=12, color=ft.Colors.GREY_600)
                                    ], spacing=2)
                                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                bgcolor=ft.Colors.WHITE,
                                border_radius=12,
                                shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                                padding=16,
                                on_click=on_find_by_qr
                            ),
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Icon(name=ft.Icons.TABLE_CHART, color="#22C55E", size=28),
                                        bgcolor="#DCFCE7", border_radius=12, padding=10, margin=ft.margin.only(right=12)
                                    ),
                                    ft.Column([
                                        ft.Text(texts["rag"], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                                        ft.Text(texts["rag_desc"], size=12, color=ft.Colors.GREY_600)
                                    ], spacing=2)
                                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                                bgcolor=ft.Colors.WHITE,
                                border_radius=12,
                                shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                                padding=16,
                                margin=ft.margin.only(bottom=16),
                                on_click=lambda e: go_chat(lang, lang, user_rag_room_id, RAG_ROOM_TITLE, is_rag=True)
                            ),
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.only(top=32),
                        alignment=ft.alignment.center,
                    ),
                ],
                bgcolor=ft.LinearGradient(["#F1F5FF", "#E0E7FF"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right)
            )
        )
        page.go("/find_room_method")

    def go_find_by_id(lang):
        def on_submit(e=None):
            room_id = id_field.value.strip()
            if room_id:
                go_chat_from_list(room_id)
        # 다국어 텍스트 사전
        FIND_BY_ID_TEXTS = {
            "ko": {"title": "방 ID로 채팅방 찾기", "label": "방 ID를 입력하세요", "enter": "입장", "back": "뒤로가기"},
            "en": {"title": "Find Chat Room by ID", "label": "Enter chat room ID", "enter": "Enter", "back": "Back"},
            "ja": {"title": "IDでチャットルームを探す", "label": "ルームIDを入力してください", "enter": "入室", "back": "戻る"},
            "zh": {"title": "通过ID查找聊天室", "label": "请输入房间ID", "enter": "进入", "back": "返回"},
            "zh-TW": {"title": "通過ID查找聊天室", "label": "請輸入房間ID", "enter": "進入", "back": "返回"},
            "id": {"title": "Cari Ruang Obrolan dengan ID", "label": "Masukkan ID ruang obrolan", "enter": "Masuk", "back": "Kembali"},
            "vi": {"title": "Tìm phòng chat bằng ID", "label": "Nhập ID phòng chat", "enter": "Vào phòng", "back": "Quay lại"},
            "fr": {"title": "Trouver une salle par ID", "label": "Entrez l'ID de la salle", "enter": "Entrer", "back": "Retour"},
            "de": {"title": "Chatraum per ID finden", "label": "Geben Sie die Raum-ID ein", "enter": "Betreten", "back": "Zurück"},
            "th": {"title": "ค้นหาห้องแชทด้วย ID", "label": "กรอก ID ห้องแชท", "enter": "เข้าร่วม", "back": "ย้อนกลับ"},
        }
        t = FIND_BY_ID_TEXTS.get(lang, FIND_BY_ID_TEXTS["en"])
        id_field = ft.TextField(label=t["label"], width=300, on_submit=on_submit)
        page.views.clear()
        page.views.append(
            ft.View(
                "/find_by_id",
                controls=[
                    ft.Text(t["title"], size=20, weight=ft.FontWeight.BOLD),
                    id_field,
                    ft.ElevatedButton(t["enter"], on_click=on_submit, width=300),
                    ft.ElevatedButton(t["back"], on_click=lambda e: go_room_list(lang), width=300)
                ],
                bgcolor=ft.Colors.WHITE,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                vertical_alignment=ft.MainAxisAlignment.CENTER
            )
        )
        page.go("/find_by_id")

    def go_find_by_qr(lang):
        def on_message(e):
            qr_text = e.data  # JS에서 전달된 QR코드 텍스트
            # QR코드에서 방 ID 추출
            if "/join_room/" in qr_text:
                room_id = qr_text.split("/join_room/")[-1].split("/")[0]
            else:
                room_id = qr_text
            if room_id:
                go_chat_from_list(room_id)

        def on_manual_input(e):
            manual_room_id = manual_input_field.value.strip()
            if manual_room_id:
                # URL에서 방 ID 추출
                if "/join_room/" in manual_room_id:
                    room_id = manual_room_id.split("/join_room/")[-1].split("/")[0]
                else:
                    room_id = manual_room_id
                go_chat_from_list(room_id)

        # 다국어 텍스트 사전
        FIND_BY_QR_TEXTS = {
            "ko": {"title": "QR 코드 스캔", "desc": "QR 코드를 스캔하거나 내용을 직접 입력하세요", "label": "QR 코드 내용을 직접 입력하세요", "enter": "입력한 내용으로 입장", "tip": "💡 팁: QR 코드를 스캔할 수 없는 경우,\n위 입력창에 QR 코드 내용을 복사해서 붙여넣으세요.", "back": "뒤로가기"},
            "en": {"title": "Scan QR Code", "desc": "Scan the QR code or enter the content manually", "label": "Enter QR code content", "enter": "Enter with input", "tip": "💡 Tip: If you can't scan the QR code,\npaste the QR code content into the input box above.", "back": "Back"},
            "ja": {"title": "QRコードスキャン", "desc": "QRコードをスキャンするか内容を直接入力してください", "label": "QRコード内容を直接入力してください", "enter": "入力内容で入室", "tip": "💡 ヒント: QRコードをスキャンできない場合、\n上の入力欄にQRコード内容を貼り付けてください。", "back": "戻る"},
            "zh": {"title": "扫描二维码", "desc": "扫描二维码或手动输入内容", "label": "请直接输入二维码内容", "enter": "用输入内容进入", "tip": "💡 提示：如果无法扫描二维码，\n请将二维码内容粘贴到上方输入框。", "back": "返回"},
            "zh-TW": {"title": "掃描二維碼", "desc": "掃描二維碼或手動輸入內容", "label": "請直接輸入二維碼內容", "enter": "用輸入內容進入", "tip": "💡 提示：若無法掃描二維碼，\n請將二維碼內容貼到上方輸入框。", "back": "返回"},
            "id": {"title": "Pindai Kode QR", "desc": "Pindai kode QR atau masukkan isinya secara manual", "label": "Masukkan isi kode QR", "enter": "Masuk dengan input", "tip": "💡 Tips: Jika tidak dapat memindai kode QR,\ntempelkan isi kode QR ke kotak input di atas.", "back": "Kembali"},
            "vi": {"title": "Quét mã QR", "desc": "Quét mã QR hoặc nhập nội dung thủ công", "label": "Nhập nội dung mã QR", "enter": "Vào bằng nội dung nhập", "tip": "💡 Mẹo: Nếu không quét được mã QR,\ndán nội dung mã QR vào ô nhập phía trên.", "back": "Quay lại"},
            "fr": {"title": "Scanner le code QR", "desc": "Scannez le code QR ou saisissez le contenu manuellement", "label": "Saisissez le contenu du code QR", "enter": "Entrer avec le contenu saisi", "tip": "💡 Astuce : Si vous ne pouvez pas scanner le code QR,\ncollez le contenu du code QR dans la zone de saisie ci-dessus.", "back": "Retour"},
            "de": {"title": "QR-Code scannen", "desc": "Scannen Sie den QR-Code oder geben Sie den Inhalt manuell ein", "label": "Geben Sie den QR-Code-Inhalt ein", "enter": "Mit Eingabe beitreten", "tip": "💡 Tipp: Wenn Sie den QR-Code nicht scannen können,\nfügen Sie den QR-Code-Inhalt in das obige Eingabefeld ein.", "back": "Zurück"},
            "th": {"title": "สแกนคิวอาร์โค้ด", "desc": "สแกนคิวอาร์โค้ดหรือกรอกเนื้อหาด้วยตนเอง", "label": "กรอกเนื้อหาคิวอาร์โค้ด", "enter": "เข้าร่วมด้วยเนื้อหาที่กรอก", "tip": "💡 เคล็ดลับ: หากสแกนคิวอาร์โค้ดไม่ได้\nให้นำเนื้อหาคิวอาร์โค้ดไปวางในช่องกรอกด้านบน", "back": "ย้อนกลับ"},
        }
        t = FIND_BY_QR_TEXTS.get(lang, FIND_BY_QR_TEXTS["en"])
        manual_input_field = ft.TextField(
            label=t["label"],
            hint_text=t["label"],
            width=350,
            on_submit=on_manual_input
        )

        # 안내 메시지와 수동 입력 옵션 제공
        page.views.clear()
        page.views.append(
            ft.View(
                "/find_by_qr",
                controls=[
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(
                                name=ft.Icons.QR_CODE,
                                size=64,
                                color=ft.Colors.BLUE_500
                            ),
                            ft.Text(
                                t["title"],
                                size=24,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Text(
                                t["desc"],
                                size=14,
                                color=ft.Colors.GREY_600,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Container(height=20),
                            manual_input_field,
                            ft.ElevatedButton(
                                t["enter"],
                                on_click=on_manual_input,
                                width=350
                            ),
                            ft.Container(height=20),
                            ft.Text(
                                t["tip"],
                                size=12,
                                color=ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER
                            ),
                        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=32,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=20,
                        shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK12),
                    ),
                    ft.ElevatedButton(t["back"], on_click=lambda e: go_room_list(lang), width=350)
                ],
                bgcolor=ft.Colors.WHITE,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                vertical_alignment=ft.MainAxisAlignment.CENTER
            )
        )
        page.go("/find_by_qr")

    def go_chat_from_list(room_id):
        # RAG 채팅방인지 확인 (공용 RAG_ROOM_ID로 들어오면, 사용자별로 리다이렉트)
        if room_id == RAG_ROOM_ID or room_id.startswith(RAG_ROOM_ID):
            user_id = page.session.get("user_id")
            if not user_id:
                user_id = str(uuid.uuid4())
                page.session.set("user_id", user_id)
            user_rag_room_id = f"{RAG_ROOM_ID}_{user_id}"
            go_chat(lang, lang, user_rag_room_id, RAG_ROOM_TITLE, is_rag=True)
            return
        
        try:
            room_ref = db.reference(f'/rooms/{room_id}')
            room_data = room_ref.get()
            if room_data:
                go_chat(
                    user_lang=room_data.get('user_lang', 'ko'),
                    target_lang=room_data.get('target_lang', 'en'),
                    room_id=room_id,
                    room_title=room_data.get('title', '채팅방'),
                    is_rag=room_data.get('is_rag', False)
                )
            else:
                print(f"오류: ID가 {room_id}인 방을 찾을 수 없습니다.")
        except Exception as e:
            print(f"Firebase에서 방 정보 가져오기 실패: {e}")

    def go_chat(user_lang, target_lang, room_id, room_title="채팅방", is_rag=False):
        def after_nickname(nickname):
            page.session.set("nickname", nickname)
            page.views.clear()
            
            # RAG 채팅방인지 확인
            if is_rag:
                def rag_translate_message(text, target_lang):
                    # RAG 답변만 반환 (번역 X)
                    if vector_db is None:
                        return "죄송합니다. RAG 기능이 현재 사용할 수 없습니다. (벡터DB가 로드되지 않았습니다.)"
                    return answer_with_rag(text, vector_db, OPENAI_API_KEY)
                
                page.views.append(ChatRoomPage(
                    page,
                    room_id=room_id,
                    room_title=room_title,
                    user_lang=user_lang,
                    target_lang=target_lang,
                    on_back=lambda e: go_home(lang),
                    on_share=on_share_clicked,
                    custom_translate_message=rag_translate_message,
                    firebase_available=FIREBASE_AVAILABLE
                ))
            else:
                page.views.append(ChatRoomPage(
                    page, 
                    room_id=room_id, 
                    room_title=room_title, 
                    user_lang=user_lang, 
                    target_lang=target_lang,
                    on_back=lambda e: go_home(lang),
                    on_share=on_share_clicked,
                    firebase_available=FIREBASE_AVAILABLE
                ))
            page.go(f"/chat/{room_id}")
        def on_share_clicked(e):
            print(f"--- DEBUG: 공유 버튼 클릭됨 ---")
            show_qr_dialog(room_id, room_title)
        if not page.session.get("nickname"):
            # 닉네임 입력 화면 다국어 지원
            texts = NICKNAME_TEXTS.get(lang, NICKNAME_TEXTS["ko"])
            nickname_value = ""
            char_count = ft.Text(f"0/12", size=12, color=ft.Colors.GREY_600)
            nickname_field = ft.TextField(label=texts["label"], hint_text=texts["hint"], on_change=None, max_length=12, width=320)
            enter_button = ft.ElevatedButton(texts["enter"], disabled=True, width=320)
            def on_nickname_change(e):
                value = nickname_field.value.strip()
                char_count.value = f"{len(value)}/12"
                enter_button.disabled = not (2 <= len(value) <= 12)
                page.update()
            nickname_field.on_change = on_nickname_change
            def on_nickname_submit(e=None):
                nickname = nickname_field.value.strip()
                if 2 <= len(nickname) <= 12:
                    after_nickname(nickname)
            enter_button.on_click = on_nickname_submit
            page.views.clear()
            page.views.append(
                ft.View(
                    "/nickname",
                    controls=[
                        ft.Row([
                            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: go_home(lang)),
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(
                                        content=ft.Icon(name=ft.Icons.PERSON, color="#22C55E", size=28),
                                        bgcolor="#22C55E22", border_radius=12, padding=8, margin=ft.margin.only(right=8)
                                    ),
                                    ft.Text(texts["title"], size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            ),
                        ], alignment=ft.MainAxisAlignment.START, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(texts["desc"], size=14, color=ft.Colors.GREY_600, text_align="center"),
                                ft.Container(height=8),
                                ft.Text(texts["label"], size=14, weight=ft.FontWeight.W_500),
                                nickname_field,
                                ft.Row([
                                    char_count
                                ], alignment=ft.MainAxisAlignment.END),
                                ft.Container(height=8),
                                enter_button,
                                ft.Container(height=8),
                                ft.ElevatedButton(texts["back"], on_click=lambda e: go_home(lang), width=320, style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_200, color=ft.Colors.BLACK)),
                            ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=40,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=20,
                            shadow=ft.BoxShadow(blur_radius=24, color="#B0BEC544"),
                            alignment=ft.alignment.center,
                            margin=ft.margin.only(top=32),
                            width=400,
                        ),
                    ],
                    bgcolor=ft.LinearGradient(["#F1F5FF", "#E0E7FF"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    vertical_alignment=ft.MainAxisAlignment.CENTER
                )
            )
            page.update()
            return
        else:
            after_nickname(page.session.get("nickname") or "")

    # --- 라우팅 처리 ---
    def route_change(route):
        print(f"Route: {page.route}")
        parts = page.route.split('/')
        
        if page.route == "/":
            go_nationality()
        elif page.route == "/home":
            go_home(lang)
        elif page.route == "/create_room":
            go_create(lang)
        elif page.route.startswith("/join_room/"):
            room_id = parts[2]
            # QR코드로 참여 시, Firebase에서 방 정보를 가져옵니다.
            go_chat_from_list(room_id)
        # 다른 라우트 핸들링...
        page.update()

    page.on_route_change = route_change
    page.go(page.route)

ft.app(target=main)
