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

def ChatRoomPage(page, room_id, room_title, user_lang, target_lang, on_back=None, on_share=None, custom_translate_message=None):
    # --- 상태 및 컨트롤 초기화 ---
    chat_messages = Column(auto_scroll=True, spacing=15, expand=True)
    current_target_lang = [target_lang]
    is_korean = user_lang == "ko"
    # RAG 채팅방인지 확인
    is_rag_room = custom_translate_message is not None
    # 언어별 입력창 안내문구
    RAG_INPUT_HINTS = {
        "ko": "한국생활에 대해 질문하세요",
        "en": "Ask about life in Korea",
        "vi": "Hãy hỏi về cuộc sống ở Hàn Quốc",
        "ja": "韓国での生活について質問してください",
        "zh": "请咨询有关在韩国生活的问题",
        "fr": "Posez des questions sur la vie en Corée",
        "de": "Stellen Sie Fragen zum Leben in Korea",
        "th": "สอบถามเกี่ยวกับการใช้ชีวิตในเกาหลีได้เลย",
    }
    input_hint = RAG_INPUT_HINTS.get(user_lang, RAG_INPUT_HINTS["ko"]) if is_rag_room else ("메시지 입력" if is_korean else "Type a message")
    input_box = ft.TextField(hint_text=input_hint, expand=True)
    if is_rag_room:
        translate_switch = None  # RAG 답변 ON/OFF 스위치 제거
    else:
        switch_label = "번역 ON/OFF" if is_korean else "Translate ON/OFF"
        translate_switch = ft.Switch(label=switch_label, value=True)

    def create_message_bubble(msg_data, is_me):
        """메시지 말풍선을 생성하는 함수"""
        message_column = ft.Column(
            [
                ft.Text(msg_data.get('nickname', '익명'), size=12, color=ft.Colors.GREY_700),  # 닉네임 표시
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
        # 다국어 안내 메시지 딕셔너리
        RAG_GUIDE_TEXTS = {
            "ko": {
                "title": "다문화가족 한국생활안내",
                "info": "다음과 같은 정보를 질문할 수 있습니다:",
                "items": [
                    "🏥 병원, 약국 이용 방법",
                    "🏦 은행, 우체국, 관공서 이용",
                    "🚌 교통수단 이용 (버스, 지하철, 기차)",
                    "🚗 운전면허, 자가용, 택시 이용",
                    "🏠 집 구하기",
                    "📱 핸드폰 사용하기",
                    "🗑️ 쓰레기 버리기 (종량제, 분리배출)",
                    "🆔 외국인등록증 신청, 체류기간 연장"
                ],
                "example_title": "질문 예시:",
                "examples": [
                    "• 병원에 가려면 어떻게 해야 하나요?",
                    "• 쓰레기는 어떻게 버려야 하나요?",
                    "• 외국인등록증은 어디서 신청하나요?"
                ],
                "input_hint": "아래에 질문을 입력해보세요! 💬"
            },
            "en": {
                "title": "Korean Life Guide for Multicultural Families",
                "info": "You can ask about the following topics:",
                "items": [
                    "🏥 How to use hospitals and pharmacies",
                    "🏦 How to use banks, post offices, government offices",
                    "🚌 How to use public transport (bus, subway, train)",
                    "🚗 Driver's license, private car, taxi",
                    "🏠 Finding a house",
                    "📱 Using a mobile phone",
                    "🗑️ How to dispose of trash (volume-based, recycling)",
                    "🆔 Alien registration, extension of stay"
                ],
                "example_title": "Example questions:",
                "examples": [
                    "• How do I go to the hospital?",
                    "• How do I throw away trash?",
                    "• Where can I apply for an alien registration card?"
                ],
                "input_hint": "Type your question below! 💬"
            },
            "vi": {
                "title": "Hướng dẫn cuộc sống Hàn Quốc cho gia đình đa văn hóa",
                "info": "Bạn có thể hỏi về các thông tin sau:",
                "items": [
                    "🏥 Cách sử dụng bệnh viện, nhà thuốc",
                    "🏦 Cách sử dụng ngân hàng, bưu điện, cơ quan công quyền",
                    "🚌 Cách sử dụng phương tiện giao thông (xe buýt, tàu điện ngầm, tàu hỏa)",
                    "🚗 Bằng lái xe, xe riêng, taxi",
                    "🏠 Tìm nhà ở",
                    "📱 Sử dụng điện thoại di động",
                    "🗑️ Cách vứt rác (theo khối lượng, phân loại)",
                    "🆔 Đăng ký người nước ngoài, gia hạn lưu trú"
                ],
                "example_title": "Ví dụ câu hỏi:",
                "examples": [
                    "• Làm thế nào để đi bệnh viện?",
                    "• Vứt rác như thế nào?",
                    "• Đăng ký người nước ngoài ở đâu?"
                ],
                "input_hint": "Hãy nhập câu hỏi bên dưới! 💬"
            },
            "ja": {
                "title": "多文化家族のための韓国生活ガイド",
                "info": "次のような情報について質問できます:",
                "items": [
                    "🏥 病院・薬局の利用方法",
                    "🏦 銀行・郵便局・官公庁の利用",
                    "🚌 交通機関の利用（バス・地下鉄・電車）",
                    "🚗 運転免許・自家用車・タクシー利用",
                    "🏠 住まい探し",
                    "📱 携帯電話の使い方",
                    "🗑️ ゴミの捨て方（有料・分別）",
                    "🆔 外国人登録証の申請、滞在期間の延長"
                ],
                "example_title": "質問例:",
                "examples": [
                    "• 病院へ行くにはどうすればいいですか？",
                    "• ゴミはどうやって捨てますか？",
                    "• 外国人登録証はどこで申請できますか？"
                ],
                "input_hint": "下に質問を入力してください！ 💬"
            },
            # 필요시 추가 언어...
        }
        # 현재 언어 가져오기 (없으면 ko)
        current_lang = user_lang if user_lang in RAG_GUIDE_TEXTS else "ko"
        guide = RAG_GUIDE_TEXTS[current_lang]
        def get_rag_guide_message():
            return ft.Container(
                content=ft.Column([
                    ft.Text(f"{current_lang.upper()} {guide['title']}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                    ft.Text(guide["info"], size=14, weight=ft.FontWeight.W_500),
                    ft.Container(
                        content=ft.Column([
                            *(ft.Text(item, size=12) for item in guide["items"])
                        ], spacing=5),
                        padding=ft.padding.all(10),
                        bgcolor=ft.Colors.BLUE_50,
                        border_radius=10,
                        margin=ft.margin.only(top=10, bottom=10)
                    ),
                    ft.Container(
                        content=ft.Text(guide["example_title"], size=14, weight=ft.FontWeight.W_500),
                        margin=ft.margin.only(top=10)
                    ),
                    ft.Container(
                        content=ft.Column([
                            *(ft.Text(ex, size=12, color=ft.Colors.GREY_700) for ex in guide["examples"])
                        ], spacing=3),
                        padding=ft.padding.all(10),
                        bgcolor=ft.Colors.GREY_50,
                        border_radius=10
                    ),
                    ft.Container(
                        content=ft.Text(guide["input_hint"], size=12, color=ft.Colors.GREY_600),
                        margin=ft.margin.only(top=10)
                    )
                ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.all(20),
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
                border=ft.border.all(1, ft.Colors.BLUE_200),
                margin=ft.margin.symmetric(horizontal=20, vertical=10)
            )

        # 처음 로드 시 또는 데이터가 없을 때
        if event.path == "/" and event.data is None:
            chat_messages.controls.clear()
            if is_rag_room:
                chat_messages.controls.append(get_rag_guide_message())
            else:
                chat_messages.controls.append(ft.Text("아직 메시지가 없습니다. 첫 메시지를 보내보세요!", text_align=ft.TextAlign.CENTER))
            page.update()
            # UI 스레드에서 안전하게 스크롤 조정
            def set_scroll():
                try:
                    if hasattr(page, 'views') and len(page.views) > 0:
                        page.views[-1].scroll = ft.ScrollMode.ADAPTIVE
                        page.update()
                except Exception as e:
                    print(f"스크롤 설정 중 오류: {e}")
            if hasattr(page, 'run_on_main'):
                page.run_on_main(set_scroll)
            else:
                set_scroll()
            return
        # 데이터가 딕셔너리 형태일 때 (초기 로드)
        if event.path == "/" and isinstance(event.data, dict):
            chat_messages.controls.clear() # 기존 메시지 초기화
            # RAG 안내 메시지 항상 맨 위에 추가
            if is_rag_room:
                chat_messages.controls.append(get_rag_guide_message())
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
            # RAG 안내 메시지만 있을 때는 그대로 두고 메시지 추가
            chat_messages.controls.append(create_message_bubble(msg_data, is_me))
        page.update()
        # UI 스레드에서 안전하게 스크롤 조정
        def set_scroll():
            try:
                if hasattr(page, 'views') and len(page.views) > 0:
                    page.views[-1].scroll = ft.ScrollMode.ADAPTIVE
                    page.update()
            except Exception as e:
                print(f"스크롤 설정 중 오류: {e}")
        if hasattr(page, 'run_on_main'):
            page.run_on_main(set_scroll)
        else:
            set_scroll()

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
        
        if is_rag_room:
            # 1. 내 질문 메시지(파란색, 오른쪽)
            user_message = {
                'user_id': page.session.get("user_id"),
                'nickname': page.session.get("nickname"),
                'user_lang': user_lang,
                'text': msg_text,
                'translated': "",
                'timestamp': int(time.time() * 1000)
            }
            try:
                messages_ref.push(user_message)
                input_box.value = ""
                input_box.focus()
                page.update()
            except Exception as ex:
                print(f"메시지 전송 실패: {ex}")
            # 2. RAG 답변 메시지(회색, 왼쪽)
            try:
                rag_answer = custom_translate_message(msg_text, current_target_lang[0]) if custom_translate_message else ""
                rag_message = {
                    'user_id': "rag_bot",
                    'nickname': "한국생활안내",
                    'user_lang': user_lang,
                    'text': rag_answer,
                    'translated': "",
                    'timestamp': int(time.time() * 1000) + 1  # 사용자 메시지보다 뒤에 오도록
                }
                messages_ref.push(rag_message)
            except Exception as ex:
                print(f"RAG 답변 생성 실패: {ex}")
        else:
            translated_text = ""
            if translate_switch and translate_switch.value:
                if custom_translate_message:
                    translated_text = custom_translate_message(msg_text, current_target_lang[0])
                else:
                    translated_text = translate_message(msg_text, current_target_lang[0])
            new_message = {
                'user_id': page.session.get("user_id"),
                'nickname': page.session.get("nickname"),
                'user_lang': user_lang,
                'text': msg_text,
                'translated': translated_text,
                'timestamp': int(time.time() * 1000)
            }
            try:
                messages_ref.push(new_message)
                input_box.value = ""
                input_box.focus()
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
    # 모든 경우에 본인 언어도 선택할 수 있도록 전체 언어 리스트를 사용
    available_langs = [ft.dropdown.Option(code, name) for code, name in lang_options_map.items()]

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

    # 번역 스위치가 있을 때만 Row에 추가
    row_controls = [target_lang_dd]
    if translate_switch:
        row_controls.append(translate_switch)

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
                    ft.Row(row_controls, alignment=ft.MainAxisAlignment.END, spacing=10)
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
