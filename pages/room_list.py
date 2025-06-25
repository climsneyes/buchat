import flet as ft

def RoomListPage(page, lang="ko", location="알 수 없는 위치", rooms=None, on_create=None, on_select=None, on_back=None):
    if rooms is None:
        rooms = []
        
    texts = {
        "ko": {
            "title_format": "📍 현재위치: {}",
            "no_rooms_text": "현재 생성된 방이 없습니다. 첫 번째 방을 만들어보세요!",
            "subtitle_format": "👥 {count}명 참여중",
            "create_btn": "➕ 방 만들기"
        },
        "en": {
            "title_format": "📍 Current Location: {}",
            "no_rooms_text": "No rooms available. Be the first to create one!",
            "subtitle_format": "👥 {count} people participating",
            "create_btn": "➕ Create Room"
        },
        "ja": {
            "title_format": "📍 現在地: {}",
            "no_rooms_text": "現在、作成されたルームはありません。最初のルームを作成してください！",
            "subtitle_format": "👥 {count}人参加中",
            "create_btn": "➕ ルーム作成"
        },
        "zh": {
            "title_format": "📍 当前位置: {}",
            "no_rooms_text": "当前没有可用的房间。快来创建第一个房间吧！",
            "subtitle_format": "👥 {count}人参与中",
            "create_btn": "➕ 创建房间"
        },
        "fr": {
            "title_format": "📍 Emplacement actuel: {}",
            "no_rooms_text": "Aucune salle disponible. Soyez le premier à en créer une !",
            "subtitle_format": "👥 {count} personnes participent",
            "create_btn": "➕ Créer une salle"
        },
        "de": {
            "title_format": "📍 Aktueller Standort: {}",
            "no_rooms_text": "Keine Räume verfügbar. Erstellen Sie den ersten!",
            "subtitle_format": "👥 {count} Personen nehmen teil",
            "create_btn": "➕ Raum erstellen"
        },
        "th": {
            "title_format": "📍 ตำแหน่งปัจจุบัน: {}",
            "no_rooms_text": "ไม่มีห้องว่าง เป็นคนแรกที่สร้างห้อง!",
            "subtitle_format": "👥 มีผู้เข้าร่วม {count} คน",
            "create_btn": "➕ สร้างห้อง"
        },
        "vi": {
            "title_format": "📍 Vị trí hiện tại: {}",
            "no_rooms_text": "Không có phòng nào. Hãy là người đầu tiên tạo phòng!",
            "subtitle_format": "👥 {count} người tham gia",
            "create_btn": "➕ Tạo phòng"
        }
    }
    t = texts.get(lang, texts["en"])
    
    room_list_view = ft.Column(spacing=10)
    
    if not rooms:
        room_list_view.controls.append(ft.Text(t["no_rooms_text"], text_align=ft.TextAlign.CENTER))
    else:
        for room in rooms:
            room_list_view.controls.append(
                ft.ListTile(
                    title=ft.Text(room.get("title", "알 수 없는 방")),
                    subtitle=ft.Text(t["subtitle_format"].format(count=room.get("count", 0))),
                    on_click=lambda e, room_id=room.get("id"): on_select(room_id) if on_select else None,
                )
            )
            
    room_list_view.controls.append(ft.ElevatedButton(t["create_btn"], on_click=on_create))

    return ft.View(
        "/room_list",
        controls=[
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=on_back) if on_back else ft.Container(),
                ft.Text(t["title_format"].format(location), size=16),
            ], alignment=ft.MainAxisAlignment.START),
            ft.Container(
                content=room_list_view,
                padding=30,
                bgcolor=ft.Colors.WHITE,
                border_radius=30,
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.GREY_200)
            )
        ],
        bgcolor=ft.Colors.GREY_100
    )
