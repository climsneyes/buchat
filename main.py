import os
import pickle

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
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")
FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH", "firebase_key.json")
''')

import flet as ft
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
RAG_AVAILABLE = vector_db is not None  # RAG 기능 사용 가능 여부

# --- Firebase 초기화 ---
try:
    cred = credentials.Certificate(FIREBASE_KEY_PATH)
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DB_URL
    })
    print("Firebase 초기화 성공")
except Exception as e:
    print(f"Firebase 초기화 실패: {e}")
    # Firebase 초기화 실패 시, 앱을 계속 진행할지 여부를 결정할 수 있습니다.
    # 여기서는 오류를 출력하고 계속 진행하도록 합니다.

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
    print("RAG 기능이 비활성화됩니다.")

print("RAG 벡터DB 준비 완료!")

FIND_ROOM_TEXTS = {
    "ko": {
        "title": "채팅방 찾기 방법을 선택하세요",
        "id": "ID로 찾기",
        "qr": "QR코드로 찾기",
        "rag": "다문화가족 한국생활안내",
        "back": "뒤로가기"
    },
    "en": {
        "title": "Select a way to find a chat room",
        "id": "Find by ID",
        "qr": "Find by QR code",
        "rag": "Korean Life Guide for Multicultural Families",
        "back": "Back"
    },
    "vi": {
        "title": "Chọn cách tìm phòng chat",
        "id": "Tìm bằng ID",
        "qr": "Tìm bằng mã QR",
        "rag": "Hướng dẫn cuộc sống Hàn Quốc cho gia đình đa văn hóa",
        "back": "Quay lại"
    },
    "ja": {
        "title": "チャットルームの探し方を選択してください",
        "id": "IDで探す",
        "qr": "QRコードで探す",
        "rag": "多文化家族のための韓国生活ガイド",
        "back": "戻る"
    },
    "zh": {
        "title": "请选择查找聊天室的方法",
        "id": "通过ID查找",
        "qr": "通过二维码查找",
        "rag": "多文化家庭韩国生活指南",
        "back": "返回"
    },
    "fr": {
        "title": "Sélectionnez une méthode pour trouver un salon de discussion",
        "id": "Rechercher par ID",
        "qr": "Rechercher par QR code",
        "rag": "Guide de la vie en Corée pour les familles multiculturelles",
        "back": "Retour"
    },
    "de": {
        "title": "Wählen Sie eine Methode, um einen Chatraum zu finden",
        "id": "Nach ID suchen",
        "qr": "Mit QR-Code suchen",
        "rag": "Koreanischer Lebensratgeber für multikulturelle Familien",
        "back": "Zurück"
    },
    "th": {
        "title": "เลือกวิธีค้นหาห้องแชท",
        "id": "ค้นหาด้วย ID",
        "qr": "ค้นหาด้วย QR โค้ด",
        "rag": "คู่มือการใช้ชีวิตในเกาหลีสำหรับครอบครัวพหุวัฒนธรรม",
        "back": "ย้อนกลับ"
    }
}

def main(page: ft.Page):
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
            print(f"Firebase에 방 '{room_title}' 정보 저장 성공")
        except Exception as e:
            print(f"Firebase 방 정보 저장 실패: {e}")
            # 오류 처리 (예: 사용자에게 알림)
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

    def on_country_selected(country_code):
        nonlocal lang
        lang = {"us": "en", "jp": "ja", "cn": "zh", "fr": "fr", "de": "de", "th": "th", "vn": "vi"}.get(country_code, "en")
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
        # 사용자별 고유 RAG 방 ID 생성
        user_id = page.session.get("user_id")
        if not user_id:
            import time
            user_id = str(time.time_ns())
            page.session.set("user_id", user_id)
        user_rag_room_id = f"rag_korean_guide_{user_id}"
        page.views.append(
            ft.View(
                "/find_room_method",
                controls=[
                    ft.Text(texts["title"], size=22, weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton(texts["id"], on_click=on_find_by_id, width=300),
                    ft.ElevatedButton(texts["qr"], on_click=on_find_by_qr, width=300),
                    *( [ft.ElevatedButton(texts["rag"], on_click=lambda e: go_chat(lang, lang, user_rag_room_id, RAG_ROOM_TITLE, is_rag=True), width=300)] if RAG_AVAILABLE else [] ),
                    ft.ElevatedButton(texts["back"], on_click=lambda e: go_home(lang), width=300)
                ],
                bgcolor=ft.Colors.WHITE,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                vertical_alignment=ft.MainAxisAlignment.CENTER
            )
        )
        page.go("/find_room_method")

    def go_find_by_id(lang):
        def on_submit(e=None):
            room_id = id_field.value.strip()
            if room_id:
                go_chat_from_list(room_id)
        id_field = ft.TextField(label="방 ID를 입력하세요", width=300, on_submit=on_submit)
        page.views.clear()
        page.views.append(
            ft.View(
                "/find_by_id",
                controls=[
                    ft.Text("방 ID로 채팅방 찾기", size=20, weight=ft.FontWeight.BOLD),
                    id_field,
                    ft.ElevatedButton("입장", on_click=on_submit, width=300),
                    ft.ElevatedButton("뒤로가기", on_click=lambda e: go_room_list(lang), width=300)
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

        webview_html = '''
        <div id="reader" style="width:300px"></div>
        <script src="https://unpkg.com/html5-qrcode"></script>
        <script>
        function onScanSuccess(decodedText, decodedResult) {
            window.parent.postMessage(decodedText, "*");
        }
        let html5QrcodeScanner = new Html5QrcodeScanner(
            "reader", { fps: 10, qrbox: 250 });
        html5QrcodeScanner.render(onScanSuccess);
        </script>
        '''
        page.views.clear()
        page.views.append(
            ft.View(
                "/find_by_qr",
                controls=[
                    ft.Text("QR코드를 카메라로 스캔하세요", size=20, weight=ft.FontWeight.BOLD),
                    ft.WebView(
                        content=webview_html,
                        on_message=on_message,
                        width=350,
                        height=400
                    ),
                    ft.ElevatedButton("뒤로가기", on_click=lambda e: go_room_list(lang), width=300)
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
                import time
                user_id = str(time.time_ns())
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
                    custom_translate_message=rag_translate_message
                ))
            else:
                page.views.append(ChatRoomPage(
                    page, 
                    room_id=room_id, 
                    room_title=room_title, 
                    user_lang=user_lang, 
                    target_lang=target_lang,
                    on_back=lambda e: go_home(lang),
                    on_share=on_share_clicked
                ))
            page.go(f"/chat/{room_id}")
        def on_share_clicked(e):
            print(f"--- DEBUG: 공유 버튼 클릭됨 ---")
            show_qr_dialog(room_id, room_title)
        if not page.session.get("nickname"):
            # 닉네임 입력 화면 다국어 지원
            NICKNAME_TEXTS = {
                "ko": {"title": "채팅방 입장 전 닉네임을 입력하세요.", "label": "닉네임을 입력하세요", "enter": "입장", "back": "뒤로가기"},
                "en": {"title": "Enter your nickname before joining the chat room.", "label": "Enter your nickname", "enter": "Enter", "back": "Back"},
                "ja": {"title": "チャットルームに入る前にニックネームを入力してください。", "label": "ニックネームを入力してください", "enter": "入室", "back": "戻る"},
                "zh": {"title": "进入聊天室前请输入昵称。", "label": "请输入昵称", "enter": "进入", "back": "返回"},
                "vi": {"title": "Vui lòng nhập biệt danh trước khi vào phòng chat.", "label": "Nhập biệt danh", "enter": "Vào phòng", "back": "Quay lại"},
                "fr": {"title": "Veuillez entrer un pseudo avant d'entrer dans le salon.", "label": "Entrez votre pseudo", "enter": "Entrer", "back": "Retour"},
                "de": {"title": "Bitte geben Sie vor dem Betreten des Chatraums einen Spitznamen ein.", "label": "Spitznamen eingeben", "enter": "Eintreten", "back": "Zurück"},
                "th": {"title": "กรุณากรอกชื่อเล่นก่อนเข้าห้องแชท", "label": "กรอกชื่อเล่น", "enter": "เข้าสู่ห้องแชท", "back": "ย้อนกลับ"},
            }
            texts = NICKNAME_TEXTS.get(lang, NICKNAME_TEXTS["ko"])
            def on_nickname_submit(e):
                nickname = nickname_field.value.strip()
                if nickname:
                    after_nickname(nickname)
            nickname_field = ft.TextField(label=texts["label"], on_submit=on_nickname_submit)
            page.views.clear()
            page.views.append(
                ft.View(
                    "/nickname",
                    controls=[
                        ft.Text(texts["title"], size=18),
                        nickname_field,
                        ft.ElevatedButton(texts["enter"], on_click=lambda e: on_nickname_submit(None)),
                        ft.ElevatedButton(texts["back"], on_click=lambda e: go_home(lang), width=300)
                    ],
                    bgcolor=ft.Colors.WHITE
                )
            )
            page.update()
            return
        else:
            after_nickname(page.session.get("nickname"))

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
