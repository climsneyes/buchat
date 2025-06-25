import flet as ft

def RoomListModernPage(page, lang="ko", on_create=None, on_select=None, on_back=None):
    texts = {
        "ko": {
            "title": "채팅방 목록",
            "rooms": [
                {"title": "🚑 긴급 도움 요청방", "desc": "긴급 상황을 도와주세요!", "count": 2},
                {"title": "🍱 한식 맛집 추천", "desc": "부산의 맛집을 공유해요.", "count": 5},
                {"title": "🗺️ 관광지 가이드", "desc": "관광 명소를 안내합니다.", "count": 3},
            ],
            "people": "명 참여중",
            "create_btn": "➕ 새 방 만들기"
        },
        "en": {
            "title": "Chat Room List",
            "rooms": [
                {"title": "🚑 Emergency Help", "desc": "Get help in urgent situations!", "count": 2},
                {"title": "🍱 Korean Food Recommendation", "desc": "Share the best food spots in Busan.", "count": 5},
                {"title": "🗺️ Tourist Guide", "desc": "Guide to tourist attractions.", "count": 3},
            ],
            "people": "people joined",
            "create_btn": "➕ Create New Room"
        },
        "ja": {
            "title": "チャットルーム一覧",
            "rooms": [
                {"title": "🚑 緊急支援ルーム", "desc": "緊急時に助けてください！", "count": 2},
                {"title": "🍱 韓国料理おすすめ", "desc": "釜山のグルメを共有しましょう。", "count": 5},
                {"title": "🗺️ 観光ガイド", "desc": "観光名所をご案内します。", "count": 3},
            ],
            "people": "人参加中",
            "create_btn": "➕ 新しいルーム作成"
        },
        "zh": {
            "title": "聊天室列表",
            "rooms": [
                {"title": "🚑 紧急求助房", "desc": "紧急情况下请帮忙！", "count": 2},
                {"title": "🍱 推荐韩餐美食", "desc": "分享釜山美食。", "count": 5},
                {"title": "🗺️ 旅游向导", "desc": "带你游览名胜。", "count": 3},
            ],
            "people": "人加入",
            "create_btn": "➕ 新建房间"
        },
        "fr": {
            "title": "Liste des salons de discussion",
            "rooms": [
                {"title": "🚑 Salle d'urgence", "desc": "Demandez de l'aide en cas d'urgence !", "count": 2},
                {"title": "🍱 Recommandation de cuisine coréenne", "desc": "Partagez les meilleurs restaurants de Busan.", "count": 5},
                {"title": "🗺️ Guide touristique", "desc": "Guide des attractions touristiques.", "count": 3},
            ],
            "people": "personnes",
            "create_btn": "➕ Créer un nouveau salon"
        },
        "de": {
            "title": "Chatraum-Liste",
            "rooms": [
                {"title": "🚑 Notfallhilfe-Raum", "desc": "Hilfe in Notfällen!", "count": 2},
                {"title": "🍱 Koreanisches Essen Empfehlung", "desc": "Teile die besten Restaurants in Busan.", "count": 5},
                {"title": "🗺️ Touristenführer", "desc": "Führung zu Sehenswürdigkeiten.", "count": 3},
            ],
            "people": "Personen beigetreten",
            "create_btn": "➕ Neuen Raum erstellen"
        },
        "th": {
            "title": "รายการห้องแชท",
            "rooms": [
                {"title": "🚑 ห้องขอความช่วยเหลือฉุกเฉิน", "desc": "ขอความช่วยเหลือในกรณีฉุกเฉิน!", "count": 2},
                {"title": "🍱 แนะนำอาหารเกาหลี", "desc": "แชร์ร้านเด็ดในปูซาน.", "count": 5},
                {"title": "🗺️ ไกด์ท่องเที่ยว", "desc": "แนะนำสถานที่ท่องเที่ยว.", "count": 3},
            ],
            "people": "คนเข้าร่วม",
            "create_btn": "➕ สร้างห้องใหม่"
        },
        "vi": {
            "title": "Danh sách phòng chat",
            "rooms": [
                {"title": "🚑 Phòng trợ giúp khẩn cấp", "desc": "Nhận trợ giúp khi khẩn cấp!", "count": 2},
                {"title": "🍱 Gợi ý món ăn Hàn Quốc", "desc": "Chia sẻ quán ăn ngon ở Busan.", "count": 5},
                {"title": "🗺️ Hướng dẫn viên du lịch", "desc": "Hướng dẫn các điểm du lịch.", "count": 3},
            ],
            "people": "người tham gia",
            "create_btn": "➕ Tạo phòng mới"
        }
    }
    t = texts.get(lang, texts["en"])
    return ft.View(
        "/room_list_modern",
        controls=[
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=on_back) if on_back else ft.Container(),
                ft.Text(t["title"], size=22, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.START),
            ft.Container(
                content=ft.Column([
                    *[
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.icons.GROUP, size=32, color=ft.Colors.BLUE_400),
                                ft.Column([
                                    ft.Text(room["title"], size=18, weight=ft.FontWeight.BOLD),
                                    ft.Text(room["desc"], size=13, color=ft.Colors.GREY_600),
                                    ft.Text(f"👥 {room['count']} {t['people']}", size=12, color=ft.Colors.GREY_700),
                                ], spacing=2),
                            ], spacing=16),
                            padding=16,
                            margin=8,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=20,
                            shadow=ft.BoxShadow(blur_radius=16, color=ft.Colors.GREY_200),
                            on_click=(lambda e, idx=i: on_select(idx))
                        ) for i, room in enumerate(t["rooms"])
                    ],
                    ft.ElevatedButton(t["create_btn"], on_click=on_create, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=16))),
                ], spacing=12),
                padding=24,
                bgcolor=ft.Colors.GREY_100,
                border_radius=30,
            )
        ],
        bgcolor=ft.Colors.GREY_100
    ) 