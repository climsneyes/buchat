import flet as ft

def HomePage(page, lang="ko", on_create=None, on_find=None, on_quick=None, on_change_lang=None, on_back=None):
    texts = {
        "ko": {
            "title": "🗺️ 부산 다국어 채팅앱",
            "desc": "언어가 달라도 문제 없어요!",
            "create": "➕ 채팅방 만들기",
            "find": "🔍 채팅방 찾기",
            "quick": "⚡ 빠른 채팅 시작",
            "current_lang": "🌐 현재 언어: {}",
            "change": "변경"
        },
        "en": {
            "title": "🗺️ Busan Multilingual Chat",
            "desc": "Talk freely, auto-translated!",
            "create": "➕ Create Chat Room",
            "find": "🔍 Find Chat Room",
            "quick": "⚡ Quick Match Chat",
            "current_lang": "🌐 Current Language: {}",
            "change": "Change"
        },
        "ja": {
            "title": "🗺️ 釜山多言語チャットアプリ",
            "desc": "言語が違っても大丈夫！",
            "create": "➕ チャットルーム作成",
            "find": "🔍 チャットルーム検索",
            "quick": "⚡ クイックチャット開始",
            "current_lang": "🌐 現在の言語: {}",
            "change": "変更"
        },
        "zh": {
            "title": "🗺️ 釜山多语言聊天应用",
            "desc": "语言不同也没关系！",
            "create": "➕ 创建聊天室",
            "find": "🔍 查找聊天室",
            "quick": "⚡ 快速聊天",
            "current_lang": "🌐 当前语言: {}",
            "change": "更改"
        },
        "fr": {
            "title": "🗺️ Chat multilingue de Busan",
            "desc": "Discutez librement, traduction automatique !",
            "create": "➕ Créer une salle",
            "find": "🔍 Trouver une salle",
            "quick": "⚡ Démarrer un chat rapide",
            "current_lang": "🌐 Langue actuelle : {}",
            "change": "Changer"
        },
        "de": {
            "title": "🗺️ Busan Mehrsprachiger Chat",
            "desc": "Sprechen Sie frei, automatisch übersetzt!",
            "create": "➕ Chatraum erstellen",
            "find": "🔍 Chatraum finden",
            "quick": "⚡ Schnellchat starten",
            "current_lang": "🌐 Aktuelle Sprache: {}",
            "change": "Ändern"
        },
        "th": {
            "title": "🗺️ แชทหลายภาษาปูซาน",
            "desc": "คุยได้ทุกภาษา แปลอัตโนมัติ!",
            "create": "➕ สร้างห้องแชท",
            "find": "🔍 ค้นหาห้องแชท",
            "quick": "⚡ เริ่มแชทด่วน",
            "current_lang": "🌐 ภาษา: {}",
            "change": "เปลี่ยน"
        },
        "vi": {
            "title": "🗺️ Chat đa ngôn ngữ Busan",
            "desc": "Nói chuyện thoải mái, tự động dịch!",
            "create": "➕ Tạo phòng chat",
            "find": "🔍 Tìm phòng chat",
            "quick": "⚡ Bắt đầu chat nhanh",
            "current_lang": "🌐 Ngôn ngữ hiện tại: {}",
            "change": "Thay đổi"
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
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=on_back) if on_back else ft.Container(),
                ft.Text(t["title"], size=22, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.START),
            ft.Container(
                content=ft.Column([
                    ft.Text(t["desc"], size=14, color=ft.Colors.GREY_600),
                    ft.Divider(),
                    ft.ElevatedButton(t["create"], on_click=on_create, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=16))),
                    ft.ElevatedButton(t["find"], on_click=on_find, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=16))),
                    ft.ElevatedButton(t["quick"], on_click=on_quick, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=16))),
                    ft.Divider(),
                    ft.Row([
                        ft.Text(t["current_lang"].format(lang_display.get(lang, lang)), size=12),
                        ft.TextButton(t["change"], on_click=on_change_lang)
                    ], alignment=ft.MainAxisAlignment.END)
                ], spacing=16),
                padding=30,
                bgcolor=ft.Colors.WHITE,
                border_radius=30,
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.GREY_200)
            )
        ],
        bgcolor=ft.Colors.GREY_100
    )
