import flet as ft
import openai
from config import OPENAI_API_KEY, MODEL_NAME
import os
from flet import Column, Switch
import time
from firebase_admin import db

IS_SERVER = os.environ.get("CLOUDTYPE") == "1"  # Cloudtype 환경변수 등으로 구분

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 언어 코드에 따른 전체 언어 이름 매핑
LANG_NAME_MAP = {
    "ko": "한국어", "en": "영어", "ja": "일본어", "zh": "중국어",
    "fr": "프랑스어", "de": "독일어", "th": "태국어", "vi": "베트남어"
}

def translate_message(text, target_lang):
    try:
        target_lang_name = LANG_NAME_MAP.get(target_lang, "영어")
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful translator."},
                {"role": "user", "content": f"다음 문장을 {target_lang_name}로 번역해줘:\n{text}"}
            ],
            max_tokens=1000,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[번역 오류] {e}"

def transcribe_from_mic(input_box: ft.TextField, page: ft.Page, mic_button: ft.IconButton):
    if IS_SERVER:
        input_box.hint_text = "서버에서는 음성 입력이 지원되지 않습니다."
        page.update()
        return
    import sounddevice as sd
    from scipy.io.wavfile import write
    samplerate = 44100  # Sample rate
    duration = 5  # seconds
    filename = "temp_recording.wav"

    original_hint_text = input_box.hint_text
    try:
        # 1. 녹음 시작 알림
        mic_button.disabled = True
        input_box.hint_text = "녹음 중... (5초)"
        page.update()

        # 2. 녹음
        recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
        sd.wait()  # Wait until recording is finished

        # 3. 파일로 저장
        write(filename, samplerate, recording)

        # 4. Whisper API로 전송
        input_box.hint_text = "음성 분석 중..."
        page.update()
        with open(filename, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
              model="whisper-1",
              file=audio_file
            )
        
        # 5. 결과 입력
        input_box.value = transcript.text
        
    except Exception as e:
        input_box.hint_text = f"오류: {e}"
        print(f"Whisper STT 오류: {e}")
    finally:
        # 6. 정리
        input_box.hint_text = original_hint_text
        mic_button.disabled = False
        if os.path.exists(filename):
            os.remove(filename)
        page.update()

def ChatRoomPage(page, room_id, room_title, user_lang, target_lang, on_back=None, on_share=None):
    # --- 상태 및 컨트롤 초기화 ---
    chat_messages = Column(auto_scroll=True, spacing=15, expand=True)
    current_target_lang = [target_lang]
    is_korean = user_lang == "ko"
    input_box = ft.TextField(hint_text="메시지 입력" if is_korean else "Type a message", expand=True)
    translate_switch = ft.Switch(label="번역 ON/OFF" if is_korean else "Translate ON/OFF", value=True)

    def create_message_bubble(msg_data, is_me):
        """메시지 말풍선을 생성하는 함수"""
        message_column = ft.Column(
            [
                ft.Text(msg_data['text'], color=ft.Colors.WHITE if is_me else ft.Colors.BLACK),
                ft.Text(
                    f"({msg_data['translated']})" if msg_data.get('translated') else "",
                    color=ft.Colors.WHITE70 if is_me else ft.Colors.GREY_700,
                    size=12,
                    italic=True,
                )
            ],
            spacing=4,
        )

        bubble = ft.Container(
            content=message_column,
            padding=12,
            border_radius=18,
            bgcolor=ft.Colors.BLUE_500 if is_me else ft.Colors.GREY_300,  # 본인: 파란색, 상대: 회색
            margin=ft.margin.only(top=5, bottom=5, left=5, right=5),
            alignment=ft.alignment.center_right if is_me else ft.alignment.center_left,  # 본인: 오른쪽, 상대: 왼쪽
        )

        # 내가 보낸 메시지는 오른쪽, 상대 메시지는 왼쪽에 정렬
        return ft.Row(
            controls=[bubble],
            alignment=ft.MainAxisAlignment.END if is_me else ft.MainAxisAlignment.START,  # 본인: 오른쪽, 상대: 왼쪽
        )

    # --- Firebase 리스너 콜백 ---
    def on_message(event):
        # 처음 로드 시 또는 데이터가 없을 때
        if event.path == "/" and event.data is None:
            chat_messages.controls.clear()
            chat_messages.controls.append(ft.Text("아직 메시지가 없습니다. 첫 메시지를 보내보세요!", text_align=ft.TextAlign.CENTER))
            page.update()
            return
            
        # 데이터가 딕셔너리 형태일 때 (초기 로드)
        if event.path == "/" and isinstance(event.data, dict):
            chat_messages.controls.clear() # 기존 메시지 초기화
            all_messages = sorted(event.data.values(), key=lambda x: x['timestamp'])
            for msg_data in all_messages:
                is_me = msg_data.get('user_id') == page.session.get("user_id") # user_id로 비교
                chat_messages.controls.append(create_message_bubble(msg_data, is_me))
        
        # 새로운 메시지가 추가될 때
        elif event.path != "/" and isinstance(event.data, dict):
            msg_data = event.data
            is_me = msg_data.get('user_id') == page.session.get("user_id") # user_id로 비교
            
            # "메시지가 없습니다" 텍스트 제거
            if len(chat_messages.controls) == 1 and isinstance(chat_messages.controls[0], ft.Text):
                chat_messages.controls.clear()

            chat_messages.controls.append(create_message_bubble(msg_data, is_me))

        page.update()
        page.views[-1].scroll = ft.ScrollMode.ADAPTIVE # 스크롤을 맨 아래로

    # --- Firebase 리스너 설정 ---
    messages_ref = db.reference(f'/messages/{room_id}')
    
    # 페이지가 로드될 때 사용자 ID를 세션에 저장 (임시)
    if not page.session.get("user_id"):
        page.session.set("user_id", str(time.time_ns()))
        page.update()

    # --- 이벤트 핸들러 ---
    def on_target_lang_change(e):
        current_target_lang[0] = e.control.value
        print(f"채팅방 내 번역 언어 변경: {current_target_lang[0]}")

    def send_message(e=None):
        msg_text = input_box.value.strip()
        if not msg_text:
            return
        
        translated_text = ""
        if translate_switch.value:
            translated_text = translate_message(msg_text, current_target_lang[0])

        # Firebase에 메시지 저장
        new_message = {
            'user_id': page.session.get("user_id"), # 임시 사용자 ID 사용
            'user_lang': user_lang,
            'text': msg_text,
            'translated': translated_text,
            'timestamp': int(time.time() * 1000)
        }
        try:
            messages_ref.push(new_message)
            input_box.value = ""
            input_box.focus() # 메시지 전송 후 다시 포커스
            page.update()
        except Exception as ex:
            print(f"메시지 전송 실패: {ex}")

    # 뒤로가기 버튼 클릭 시 리스너 제거 (메모리 누수 방지)
    def go_back(e):
        print("채팅방을 나갑니다.")
        on_back(e)

    # 핸들러를 컨트롤에 연결합니다.
    input_box.on_submit = send_message

    # 페이지가 처음 로드될 때 기존 메시지를 가져옵니다.
    messages_ref.listen(on_message)

    # --- UI 구성 ---
    lang_options_map = {
        "en": "🇺🇸 English", "ko": "🇰🇷 한국어", "ja": "🇯🇵 日本語", "zh": "🇨🇳 中文",
        "fr": "🇫🇷 Français", "de": "🇩🇪 Deutsch", "th": "🇹🇭 ไทย", "vi": "🇻🇳 Tiếng Việt"
    }
    available_langs = [
        ft.dropdown.Option(code, name) for code, name in lang_options_map.items() if code != user_lang
    ]

    # 상대방 언어 선택 드롭다운
    target_lang_dd = ft.Dropdown(
        value=current_target_lang[0],
        options=available_langs,
        on_change=on_target_lang_change,
        width=180,
        hint_text="번역할 언어"
    )

    # 마이크 버튼 생성 및 UI에 추가 (서버 환경에서는 보이지 않게)
    mic_button = None
    if not IS_SERVER:
        mic_button = ft.IconButton(ft.Icons.MIC)
        mic_button.on_click = lambda e: transcribe_from_mic(input_box, page, mic_button)

    return ft.View(
        f"/chat/{room_id}",
        controls=[
            ft.Row(
                [
                    ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back, tooltip="뒤로가기"),
                    ft.Text(f'"{room_title}"', size=16, weight=ft.FontWeight.BOLD, expand=True, text_align=ft.TextAlign.CENTER),
                    ft.IconButton(ft.Icons.SHARE, on_click=on_share, tooltip="QR 코드로 공유") if on_share else ft.Container(width=40),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                height=50,
            ),
            ft.Divider(height=1),
            ft.Container(
                content=chat_messages,
                expand=True, # Column이 확장되도록 설정
                padding=ft.padding.symmetric(horizontal=15),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        input_box,
                        ft.IconButton(ft.Icons.SEND, on_click=send_message, bgcolor=ft.Colors.BLUE_500, icon_color=ft.Colors.WHITE),
                        *( [mic_button] if mic_button else [] ),
                    ], spacing=8),
                    ft.Row([
                        target_lang_dd,
                        translate_switch,
                    ], alignment=ft.MainAxisAlignment.END, spacing=10)
                ], spacing=10),
                padding=ft.padding.all(15),
                border=ft.border.only(top=ft.border.BorderSide(1, ft.Colors.GREY_300))
            )
        ],
        padding=0, # View 전체 패딩 제거
        bgcolor=ft.Colors.WHITE
    )

# 환경변수에서 firebase_key.json 내용을 읽어서 파일로 저장
firebase_key_json = os.getenv("FIREBASE_KEY_JSON")
if firebase_key_json:
    with open("firebase_key.json", "w", encoding="utf-8") as f:
        f.write(firebase_key_json)
