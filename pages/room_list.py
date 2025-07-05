import flet as ft

def RoomListPage(page, lang="ko", location="알 수 없는 위치", rooms=None, on_create=None, on_select=None, on_back=None):
    # 화면 크기에 따른 반응형 설정
    is_mobile = page.width < 600
    is_tablet = 600 <= page.width < 1024
    
    # 반응형 크기 계산
    container_width = min(page.width * 0.95, 500) if not is_mobile else page.width * 0.98
    title_size = 20 if is_mobile else 24
    card_text_size = 14 if is_mobile else 16
    card_desc_size = 11 if is_mobile else 12
    icon_size = 24 if is_mobile else 28
    card_padding = 12 if is_mobile else 16
    card_margin = 10 if is_mobile else 16
    
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
            # 헤더 (뒤로가기 + 타이틀)
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=on_back) if on_back else ft.Container(),
                ft.Text(t["title_format"].replace("📍 현재위치: ", "채팅방 찾기 방법을 선택하세요"), size=title_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
            ], alignment=ft.MainAxisAlignment.START, spacing=6 if is_mobile else 8, vertical_alignment=ft.CrossAxisAlignment.CENTER),

            # 카드형 버튼들
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Icon(name=ft.Icons.TAG, color="#2563EB", size=icon_size),
                                bgcolor="#E0E7FF", border_radius=10 if is_mobile else 12, padding=8 if is_mobile else 10, margin=ft.margin.only(right=10 if is_mobile else 12)
                            ),
                            ft.Column([
                                ft.Text("ID로 찾기", size=card_text_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                                ft.Text("채팅방 ID를 입력하여 참여", size=card_desc_size, color=ft.Colors.GREY_600)
                            ], spacing=2)
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10 if is_mobile else 12,
                        shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                        padding=card_padding,
                        margin=ft.margin.only(bottom=card_margin),
                        on_click=lambda e: on_find_by_id(e),
                        width=container_width
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Icon(name=ft.Icons.QR_CODE, color="#A259FF", size=icon_size),
                                bgcolor="#F3E8FF", border_radius=10 if is_mobile else 12, padding=8 if is_mobile else 10, margin=ft.margin.only(right=10 if is_mobile else 12)
                            ),
                            ft.Column([
                                ft.Text("QR코드로 찾기", size=card_text_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                                ft.Text("QR 코드를 스캔하여 빠른 참여", size=card_desc_size, color=ft.Colors.GREY_600)
                            ], spacing=2)
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10 if is_mobile else 12,
                        shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                        padding=card_padding,
                        margin=ft.margin.only(bottom=card_margin),
                        on_click=lambda e: on_find_by_qr(e),
                        width=container_width
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Icon(name=ft.Icons.TABLE_CHART, color="#22C55E", size=icon_size),
                                bgcolor="#DCFCE7", border_radius=10 if is_mobile else 12, padding=8 if is_mobile else 10, margin=ft.margin.only(right=10 if is_mobile else 12)
                            ),
                            ft.Column([
                                ft.Text("대문하기술 한국생활안내", size=card_text_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                                ft.Text("공식 안내 채팅방", size=card_desc_size, color=ft.Colors.GREY_600)
                            ], spacing=2)
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10 if is_mobile else 12,
                        shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                        padding=card_padding,
                        margin=ft.margin.only(bottom=card_margin),
                        on_click=lambda e: on_rag_guide(e),
                        width=container_width
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                content=ft.Icon(name=ft.Icons.PERSON, color="#64748B", size=icon_size),
                                bgcolor="#F1F5F9", border_radius=10 if is_mobile else 12, padding=8 if is_mobile else 10, margin=ft.margin.only(right=10 if is_mobile else 12)
                            ),
                            ft.Column([
                                ft.Text("뒤로가기", size=card_text_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                                ft.Text("메인 메뉴로 돌아가기", size=card_desc_size, color=ft.Colors.GREY_600)
                            ], spacing=2)
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.WHITE,
                        border_radius=10 if is_mobile else 12,
                        shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544"),
                        padding=card_padding,
                        margin=ft.margin.only(bottom=0),
                        on_click=lambda e: on_back(e) if on_back else None,
                        width=container_width
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.padding.only(top=24 if is_mobile else 32),
                alignment=ft.alignment.center,
                width=container_width
            ),
        ],
        bgcolor=ft.LinearGradient(["#F1F5FF", "#E0E7FF"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )
