import flet as ft

def CreateRoomPage(page, lang="ko", on_create=None, on_back=None):
    # 화면 크기에 따른 반응형 설정
    is_mobile = page.width < 600
    is_tablet = 600 <= page.width < 1024
    
    # 반응형 크기 계산
    container_width = min(page.width * 0.95, 500) if not is_mobile else page.width * 0.98
    field_width = min(360, page.width * 0.85)
    title_size = 20 if is_mobile else 24
    subtitle_size = 18 if is_mobile else 22
    label_size = 12 if is_mobile else 14
    hint_size = 11 if is_mobile else 13
    icon_size = 24 if is_mobile else 28
    header_icon_size = 24 if is_mobile else 28
    
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
        "zh-TW": {
            "title": "📌 建立聊天室",
            "room_title_label": "輸入房間標題",
            "room_title_hint": "例如：幫助外國人找路的房間",
            "your_lang": "🇹🇼 台灣中文（自動偵測）",
            "target_lang_label": "選擇對方語言",
            "target_lang_hint": "例如：英文、日文、韓文等",
            "purpose_label": "聊天目的（可選）",
            "purpose_options": ["導航", "美食推薦", "旅遊資訊", "自由聊天", "緊急求助"],
            "create_btn": "✅ 建立聊天室"
        },
        "id": {
            "title": "📌 Buat Ruang Obrolan",
            "room_title_label": "Masukkan Judul Ruangan",
            "room_title_hint": "misal: Ruang untuk membantu orang asing menemukan jalan",
            "your_lang": "🇮🇩 Bahasa Indonesia (terdeteksi otomatis)",
            "target_lang_label": "Pilih Bahasa Lawan Bicara",
            "target_lang_hint": "misal: Inggris, Jepang, Korea, dll",
            "purpose_label": "Tujuan Obrolan (opsional)",
            "purpose_options": ["Petunjuk Arah", "Rekomendasi Makanan", "Info Wisata", "Obrolan Bebas", "Bantuan Darurat"],
            "create_btn": "✅ Buat Ruang Obrolan"
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
        ft.dropdown.Option("zh-TW", "🇹🇼 台灣中文"),
        ft.dropdown.Option("id", "🇮🇩 Bahasa Indonesia"),
        ft.dropdown.Option("fr", "🇫🇷 Français"),
        ft.dropdown.Option("de", "🇩🇪 Deutsch"),
        ft.dropdown.Option("th", "🇹🇭 ไทย"),
        ft.dropdown.Option("vi", "🇻🇳 Tiếng Việt"),
    ]

    # 컨트롤 참조 생성
    room_title_field = ft.TextField(hint_text=t["room_title_hint"], width=field_width)
    target_lang_dd = ft.Dropdown(
        options=[
            ft.dropdown.Option("en", "🇺🇸 English"),
            ft.dropdown.Option("ja", "🇯🇵 日本語"),
            ft.dropdown.Option("zh", "🇨🇳 中文"),
            ft.dropdown.Option("zh-TW", "🇹🇼 台灣中文"),
            ft.dropdown.Option("id", "🇮🇩 Bahasa Indonesia"),
            ft.dropdown.Option("fr", "🇫🇷 Français"),
            ft.dropdown.Option("de", "🇩🇪 Deutsch"),
            ft.dropdown.Option("th", "🇹🇭 ไทย"),
            ft.dropdown.Option("vi", "🇻🇳 Tiếng Việt"),
        ],
        hint_text=t["target_lang_hint"],
        width=field_width
    )
    purpose_dd = ft.Dropdown(
        label=t["purpose_label"],
        options=[ft.dropdown.Option(opt) for opt in t["purpose_options"]],
        hint_text=t["purpose_label"],
        width=field_width
    )
    
    # on_create 콜백 수정: 방 제목과 함께 선택된 상대방 언어(target_lang_dd.value)를 전달
    create_button = ft.ElevatedButton(
        t["create_btn"],
        on_click=lambda e: on_create(room_title_field.value, target_lang_dd.value) if on_create else None,
        width=field_width,
        bgcolor="#4ADE80",
        color=ft.Colors.WHITE
    )

    return ft.View(
        "/create_room",
        controls=[
            # 헤더 (아이콘 + 타이틀)
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=on_back) if on_back else ft.Container(),
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(name=ft.Icons.PEOPLE, color="#22C55E", size=header_icon_size),
                            bgcolor="#22C55E22", border_radius=10 if is_mobile else 12, padding=6 if is_mobile else 8, margin=ft.margin.only(right=6 if is_mobile else 8)
                        ),
                        ft.Text(t["title"].replace("📌 ", ""), size=title_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ),
            ], alignment=ft.MainAxisAlignment.START, spacing=6 if is_mobile else 8, vertical_alignment=ft.CrossAxisAlignment.CENTER),

            # 중앙 카드 (설정 폼)
            ft.Container(
                content=ft.Column([
                    ft.Text("새로운 채팅방 설정", size=subtitle_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87, text_align="center"),
                    ft.Container(
                        content=ft.Text(t["room_title_label"], size=label_size, weight=ft.FontWeight.W_500),
                        margin=ft.margin.only(top=16 if is_mobile else 20)
                    ),
                    room_title_field,
                    ft.Row([
                        ft.Icon(name=ft.Icons.LANGUAGE, color="#2563EB", size=14 if is_mobile else 16),
                        ft.Text(t["your_lang"], size=hint_size, color="#2563EB"),
                    ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(
                        content=ft.Text(t["target_lang_label"], size=label_size, weight=ft.FontWeight.W_500),
                        margin=ft.margin.only(top=12)
                    ),
                    target_lang_dd,
                    ft.Container(
                        content=ft.Text(t["purpose_label"], size=label_size, weight=ft.FontWeight.W_500),
                        margin=ft.margin.only(top=12)
                    ),
                    purpose_dd,
                    ft.Container(
                        content=create_button,
                        margin=ft.margin.only(top=16 if is_mobile else 20)
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(name=ft.Icons.LIGHTBULB_OUTLINE, color="#F59E42", size=16 if is_mobile else 18),
                            ft.Text("구체적인 방 제목을 작성하면 더 많은 사람들이 참여할 수 있어요!", size=11 if is_mobile else 12, color="#64748B"),
                        ], spacing=4 if is_mobile else 6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor="#F1F5FF",
                        border_radius=6 if is_mobile else 8,
                        padding=10 if is_mobile else 12,
                        margin=ft.margin.only(top=16)
                    ),
                ], spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=30 if is_mobile else 40,
                bgcolor=ft.Colors.WHITE,
                border_radius=16 if is_mobile else 20,
                shadow=ft.BoxShadow(blur_radius=24, color="#B0BEC544"),
                alignment=ft.alignment.center,
                margin=ft.margin.only(top=24 if is_mobile else 32),
                width=container_width
            ),
        ],
        bgcolor=ft.LinearGradient(["#F1F5FF", "#E0E7FF"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )
