import flet as ft

def HomePage(page, lang="ko", on_create=None, on_find=None, on_quick=None, on_change_lang=None, on_back=None):
    # 화면 크기에 따른 반응형 설정
    is_mobile = page.width < 600
    is_tablet = 600 <= page.width < 1024
    
    # 반응형 크기 계산
    container_width = min(page.width * 0.95, 500) if not is_mobile else page.width * 0.98
    title_size = 20 if is_mobile else 24
    desc_size = 16 if is_mobile else 20
    desc2_size = 12 if is_mobile else 14
    button_text_size = 14 if is_mobile else 16
    icon_size = 24 if is_mobile else 28
    header_icon_size = 28 if is_mobile else 32
    
    texts = {
        "ko": {
            "title": "부산 다국어 채팅앱",
            "desc": "언어가 달라도 문제 없어요!",
            "desc2": "새로운 친구들과 만나보세요 ✨",
            "create": "채팅방 만들기",
            "find": "채팅방 찾기",
            "quick": "빠른 채팅방 시작"
        },
        "en": {
            "title": "Busan Multilingual Chat",
            "desc": "No problem even if the language is different!",
            "desc2": "Meet new friends ✨",
            "create": "Create Chat Room",
            "find": "Find Chat Room",
            "quick": "Quick Chat Start"
        },
        "ja": {
            "title": "釜山多言語チャットアプリ",
            "desc": "言語が違っても問題ありません！",
            "desc2": "新しい友達と出会いましょう ✨",
            "create": "チャットルーム作成",
            "find": "チャットルーム検索",
            "quick": "クイックチャット開始"
        },
        "zh": {
            "title": "釜山多语言聊天应用",
            "desc": "即使语言不同也没问题！",
            "desc2": "结识新朋友 ✨",
            "create": "创建聊天室",
            "find": "查找聊天室",
            "quick": "快速聊天开始"
        },
        "fr": {
            "title": "Chat multilingue de Busan",
            "desc": "Pas de problème même si la langue est différente !",
            "desc2": "Rencontrez de nouveaux amis ✨",
            "create": "Créer une salle de chat",
            "find": "Trouver une salle de chat",
            "quick": "Démarrer un chat rapide"
        },
        "de": {
            "title": "Busan Mehrsprachiger Chat",
            "desc": "Kein Problem, auch wenn die Sprache anders ist!",
            "desc2": "Treffen Sie neue Freunde ✨",
            "create": "Chatraum erstellen",
            "find": "Chatraum finden",
            "quick": "Schnellchat starten"
        },
        "th": {
            "title": "แชทหลายภาษาปูซาน",
            "desc": "แม้ภาษาต่างกันก็ไม่เป็นไร!",
            "desc2": "พบเพื่อนใหม่ ๆ ✨",
            "create": "สร้างห้องแชท",
            "find": "ค้นหาห้องแชท",
            "quick": "เริ่มแชทด่วน"
        },
        "vi": {
            "title": "Trò chuyện đa ngôn ngữ Busan",
            "desc": "Không vấn đề gì dù ngôn ngữ khác nhau!",
            "desc2": "Gặp gỡ bạn mới ✨",
            "create": "Tạo phòng trò chuyện",
            "find": "Tìm phòng trò chuyện",
            "quick": "Bắt đầu trò chuyện nhanh"
        },
        "zh-TW": {
            "title": "釜山多語聊天室",
            "desc": "即使語言不同也沒問題！",
            "desc2": "認識新朋友 ✨",
            "create": "建立聊天室",
            "find": "查找聊天室",
            "quick": "快速聊天開始"
        },
        "id": {
            "title": "Obrolan Multibahasa Busan",
            "desc": "Tidak masalah meskipun bahasanya berbeda!",
            "desc2": "Temui teman baru ✨",
            "create": "Buat Ruang Obrolan",
            "find": "Cari Ruang Obrolan",
            "quick": "Mulai Obrolan Cepat"
        }
    }
    t = texts.get(lang, texts["en"])
    lang_display = {
        "ko": "🇰🇷 한국어",
        "en": "🇺🇸 English",
        "ja": "🇯🇵 日本語",
        "zh": "🇨🇳 中文",
        "fr": "🇫🇷 Français",
        "de": "🇩🇪 Deutsch",
        "th": "🇹🇭 ไทย",
        "vi": "🇻🇳 Tiếng Việt"
    }
    return ft.View(
        "/home",
        controls=[
            # 헤더 (앱 아이콘 + 타이틀)
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=on_back) if on_back else ft.Container(),
                ft.Container(
                    content=ft.Icon(name=ft.Icons.APARTMENT, color="#7B61FF", size=header_icon_size),
                    bgcolor=ft.LinearGradient(["#7B61FF", "#6C47FF"], begin=ft.alignment.center_left, end=ft.alignment.center_right),
                    border_radius=10 if is_mobile else 12,
                    padding=6 if is_mobile else 8,
                    margin=ft.margin.only(right=6 if is_mobile else 8)
                ),
                ft.Text(t["title"], size=title_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
            ], alignment=ft.MainAxisAlignment.START, spacing=6 if is_mobile else 8, vertical_alignment=ft.CrossAxisAlignment.CENTER),

            # 중앙 카드 (웰컴 메시지)
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Column([
                            ft.Text(t["desc"], size=desc_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                            ft.Container(
                                content=ft.Text(t["desc2"], size=desc2_size, color=ft.Colors.BLACK87, weight=ft.FontWeight.W_500),
                                margin=ft.margin.only(top=4)
                            ),
                        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=ft.padding.symmetric(vertical=20 if is_mobile else 24, horizontal=24 if is_mobile else 32),
                        bgcolor=ft.LinearGradient(["#7B61FF", "#A259FF"], begin=ft.alignment.center_left, end=ft.alignment.center_right),
                        border_radius=14 if is_mobile else 16,
                        shadow=ft.BoxShadow(blur_radius=16, color="#B39DDB44"),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                margin=ft.margin.only(top=24 if is_mobile else 32, bottom=20 if is_mobile else 24),
                alignment=ft.alignment.center,
                expand=False,
                width=container_width
            ),

            # 주요 액션 버튼들 (카드 스타일)
            ft.Column([
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(name=ft.Icons.ADD, color="#22C55E", size=icon_size),
                            bgcolor="#DCFCE7", border_radius=10 if is_mobile else 12, padding=8 if is_mobile else 10, margin=ft.margin.only(right=10 if is_mobile else 12)
                        ),
                        ft.Text(t["create"], size=button_text_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=10 if is_mobile else 12,
                    shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                    padding=14 if is_mobile else 16,
                    margin=ft.margin.only(bottom=10 if is_mobile else 12),
                    on_click=on_create,
                    width=container_width
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(name=ft.Icons.SEARCH, color="#2563EB", size=icon_size),
                            bgcolor="#DBEAFE", border_radius=10 if is_mobile else 12, padding=8 if is_mobile else 10, margin=ft.margin.only(right=10 if is_mobile else 12)
                        ),
                        ft.Text(t["find"], size=button_text_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=10 if is_mobile else 12,
                    shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                    padding=14 if is_mobile else 16,
                    margin=ft.margin.only(bottom=10 if is_mobile else 12),
                    on_click=on_find,
                    width=container_width
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(name=ft.Icons.FLASH_ON, color="#FB923C", size=icon_size),
                            bgcolor="#FFEDD5", border_radius=10 if is_mobile else 12, padding=8 if is_mobile else 10, margin=ft.margin.only(right=10 if is_mobile else 12)
                        ),
                        ft.Text(t["quick"], size=button_text_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                    ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.WHITE,
                    border_radius=10 if is_mobile else 12,
                    shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                    padding=14 if is_mobile else 16,
                    margin=ft.margin.only(bottom=10 if is_mobile else 12),
                    on_click=on_quick,
                    width=container_width
                ),
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=False),
        ],
        bgcolor=ft.LinearGradient(["#F1F5FF", "#E0E7FF"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )
