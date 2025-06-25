import flet as ft

def CreateRoomPage(page, lang="ko", on_create=None, on_back=None):
    # 언어별 텍스트 사전
    texts = {
        "ko": {
            "title": "📌 채팅방 만들기",
            "room_title_label": "방 제목 입력",
            "room_title_hint": "예: 외국인에게 길을 알려주는 방",
            "your_lang": "🇰🇷 한국어 (자동 선택)",
            "target_lang_label": "상대방 언어 선택",
            "target_lang_hint": "예: 영어, 일본어, 중국어 등",
            "purpose_label": "채팅 목적 선택 (선택사항)",
            "purpose_options": ["길안내", "음식 추천", "관광지 설명", "자유 대화", "긴급 도움 요청"],
            "create_btn": "✅ 채팅방 만들기"
        },
        "en": {
            "title": "📌 Create Chat Room",
            "room_title_label": "Enter Room Title",
            "room_title_hint": "e.g. Need help finding subway station",
            "your_lang": "🇺🇸 English (auto-detected)",
            "target_lang_label": "Target Language",
            "target_lang_hint": "e.g. Korean, Japanese, Chinese",
            "purpose_label": "Purpose of Chat (optional)",
            "purpose_options": ["Directions", "Food Recommendations", "Tourist Info", "Casual Talk", "Emergency Help"],
            "create_btn": "✅ Create Chat Room"
        },
        "ja": {
            "title": "📌 チャットルーム作成",
            "room_title_label": "ルームタイトルを入力",
            "room_title_hint": "例: 外国人に道案内する部屋",
            "your_lang": "🇯🇵 日本語 (自動検出)",
            "target_lang_label": "相手の言語を選択",
            "target_lang_hint": "例: 英語、韓国語、中国語など",
            "purpose_label": "チャットの目的（任意）",
            "purpose_options": ["道案内", "食事のおすすめ", "観光案内", "フリートーク", "緊急支援"],
            "create_btn": "✅ チャットルーム作成"
        },
        "zh": {
            "title": "📌 创建聊天室",
            "room_title_label": "输入房间标题",
            "room_title_hint": "例如：帮助外国人找路的房间",
            "your_lang": "🇨🇳 中文（自动检测）",
            "target_lang_label": "选择对方语言",
            "target_lang_hint": "例如：英语、日语、韩语等",
            "purpose_label": "聊天目的（可选）",
            "purpose_options": ["导航", "美食推荐", "旅游信息", "自由聊天", "紧急求助"],
            "create_btn": "✅ 创建聊天室"
        },
        "fr": {
            "title": "📌 Créer une salle de chat",
            "room_title_label": "Entrez le titre de la salle",
            "room_title_hint": "ex : Salle pour aider les étrangers",
            "your_lang": "🇫🇷 Français (auto-détecté)",
            "target_lang_label": "Langue de l'autre",
            "target_lang_hint": "ex : Anglais, Japonais, Chinois",
            "purpose_label": "But du chat (optionnel)",
            "purpose_options": ["Itinéraire", "Recommandation de nourriture", "Info touristique", "Discussion libre", "Aide d'urgence"],
            "create_btn": "✅ Créer la salle"
        },
        "de": {
            "title": "📌 Chatraum erstellen",
            "room_title_label": "Raumtitel eingeben",
            "room_title_hint": "z.B. Raum zur Wegbeschreibung für Ausländer",
            "your_lang": "🇩🇪 Deutsch (automatisch erkannt)",
            "target_lang_label": "Zielsprache wählen",
            "target_lang_hint": "z.B. Englisch, Japanisch, Chinesisch",
            "purpose_label": "Chat-Zweck (optional)",
            "purpose_options": ["Wegbeschreibung", "Essensempfehlung", "Touristeninfo", "Freies Gespräch", "Notfallhilfe"],
            "create_btn": "✅ Chatraum erstellen"
        },
        "th": {
            "title": "📌 สร้างห้องแชท",
            "room_title_label": "กรอกชื่อห้อง",
            "room_title_hint": "เช่น ห้องช่วยเหลือชาวต่างชาติ",
            "your_lang": "🇹🇭 ไทย (ตรวจจับอัตโนมัติ)",
            "target_lang_label": "เลือกภาษาของคู่สนทนา",
            "target_lang_hint": "เช่น อังกฤษ ญี่ปุ่น จีน",
            "purpose_label": "วัตถุประสงค์ของแชท (ไม่บังคับ)",
            "purpose_options": ["นำทาง", "แนะนำอาหาร", "ข้อมูลท่องเที่ยว", "พูดคุยทั่วไป", "ขอความช่วยเหลือฉุกเฉิน"],
            "create_btn": "✅ สร้างห้องแชท"
        },
        "vi": {
            "title": "📌 Tạo phòng trò chuyện",
            "room_title_label": "Nhập tên phòng",
            "room_title_hint": "VD: Phòng hướng dẫn cho người nước ngoài",
            "your_lang": "🇻🇳 Tiếng Việt (tự động phát hiện)",
            "target_lang_label": "Chọn ngôn ngữ đối phương",
            "target_lang_hint": "VD: Tiếng Anh, Tiếng Nhật, Tiếng Trung",
            "purpose_label": "Mục đích trò chuyện (tùy chọn)",
            "purpose_options": ["Chỉ đường", "Gợi ý món ăn", "Thông tin du lịch", "Trò chuyện tự do", "Yêu cầu khẩn cấp"],
            "create_btn": "✅ Tạo phòng"
        }
    }
    t = texts.get(lang, texts["en"])

    # 언어 선택 드롭다운 예시
    lang_options = [
        ft.dropdown.Option("en", "🇺🇸 English"),
        ft.dropdown.Option("ko", "🇰🇷 한국어"),
        ft.dropdown.Option("ja", "🇯🇵 日本語"),
        ft.dropdown.Option("zh", "🇨🇳 中文"),
        ft.dropdown.Option("fr", "🇫🇷 Français"),
        ft.dropdown.Option("de", "🇩🇪 Deutsch"),
        ft.dropdown.Option("th", "🇹🇭 ไทย"),
        ft.dropdown.Option("vi", "🇻🇳 Tiếng Việt"),
    ]

    # 컨트롤 참조 생성
    room_title_field = ft.TextField(hint_text=t["room_title_hint"], width=400)
    target_lang_dd = ft.Dropdown(
        options=[
            ft.dropdown.Option("en", "🇺🇸 English"),
            ft.dropdown.Option("ja", "🇯🇵 日本語"),
            ft.dropdown.Option("zh", "🇨🇳 中文"),
            ft.dropdown.Option("fr", "🇫🇷 Français"),
            ft.dropdown.Option("de", "🇩🇪 Deutsch"),
            ft.dropdown.Option("th", "🇹🇭 ไทย"),
            ft.dropdown.Option("vi", "🇻🇳 Tiếng Việt"),
        ],
        hint_text=t["target_lang_hint"],
        width=300
    )
    purpose_dd = ft.Dropdown(
        label=t["purpose_label"],
        options=[ft.dropdown.Option(opt) for opt in t["purpose_options"]],
        hint_text=t["purpose_label"],
        width=300
    )
    
    # on_create 콜백 수정: 방 제목과 함께 선택된 상대방 언어(target_lang_dd.value)를 전달
    create_button = ft.ElevatedButton(
        t["create_btn"],
        on_click=lambda e: on_create(room_title_field.value, target_lang_dd.value) if on_create else None,
        width=300
    )

    return ft.View(
        "/create_room",
        controls=[
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=on_back) if on_back else ft.Container(),
                ft.Text(t["title"], size=22, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.START),
            ft.Container(
                content=ft.Column([
                    ft.Text(t["room_title_label"], size=14, weight=ft.FontWeight.W_500),
                    room_title_field,
                    ft.Text(t["your_lang"], size=14, weight=ft.FontWeight.W_500, color=ft.Colors.BLUE_700),
                    ft.Text(t["target_lang_label"], size=14, weight=ft.FontWeight.W_500),
                    target_lang_dd,
                    purpose_dd,
                    create_button
                ], spacing=16),
                padding=30,
                bgcolor=ft.Colors.WHITE,
                border_radius=30,
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.GREY_200)
            )
        ],
        bgcolor=ft.Colors.GREY_100
    )
