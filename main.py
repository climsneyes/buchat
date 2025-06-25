import os

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

        qr_data = f"/join_room/{room_id}"
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
        # 1. geocoder로 현재 위치 가져오기
        g = geocoder.ip('me')
        location = g.city if g.city else "알 수 없는 위치"

        # Firebase에서 방 목록 가져오기
        try:
            rooms_ref = db.reference('/rooms')
            rooms_data = rooms_ref.get()
            # Firebase에서 받은 dict를 list로 변환, 데이터가 없으면 빈 리스트
            rooms = [value for key, value in rooms_data.items()] if rooms_data else []
            print("Firebase에서 방 목록 가져오기 성공")
        except Exception as e:
            print(f"Firebase 방 목록 가져오기 실패: {e}")
            rooms = [] # 오류 발생 시 빈 목록으로 처리

        page.views.clear()
        page.views.append(RoomListPage(page, lang, location=location, rooms=rooms,
            on_create=lambda e: go_create(lang),
            on_select=lambda room_id: go_chat_from_list(room_id), # 방 목록에서 선택 시 호출할 함수 변경
            on_back=lambda e: go_home(lang)))
        page.go("/room_list")

    def go_chat_from_list(room_id):
        # Firebase에서 해당 방의 정보를 가져와서 채팅방을 엽니다.
        try:
            room_ref = db.reference(f'/rooms/{room_id}')
            room_data = room_ref.get()
            if room_data:
                go_chat(
                    user_lang=room_data.get('user_lang', 'ko'),
                    target_lang=room_data.get('target_lang', 'en'),
                    room_id=room_id,
                    room_title=room_data.get('title', '채팅방')
                )
            else:
                print(f"오류: ID가 {room_id}인 방을 찾을 수 없습니다.")
        except Exception as e:
            print(f"Firebase에서 방 정보 가져오기 실패: {e}")

    def go_chat(user_lang, target_lang, room_id, room_title="채팅방"):
        def on_share_clicked(e):
            print(f"--- DEBUG: 공유 버튼 클릭됨 ---")
            show_qr_dialog(room_id, room_title)

        page.views.clear()
        page.views.append(ChatRoomPage(
            page, 
            room_id=room_id, 
            room_title=room_title, 
            user_lang=user_lang, 
            target_lang=target_lang,
            on_back=lambda e: go_home(user_lang),
            on_share=on_share_clicked
        ))
        page.go(f"/chat/{room_id}")

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
