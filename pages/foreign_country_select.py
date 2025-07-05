import flet as ft

def ForeignCountrySelectPage(page, on_select, on_back=None):
    # 화면 크기에 따른 반응형 설정
    is_mobile = page.width < 600
    is_tablet = 600 <= page.width < 1024
    
    # 반응형 크기 계산
    container_width = min(page.width * 0.95, 400) if not is_mobile else page.width * 0.98
    title_size = 20 if is_mobile else 22
    desc_size = 12 if is_mobile else 14
    icon_size = 32 if is_mobile else 36
    
    # 국가 데이터 (국기, 영어국가명, 코드, 언어코드)
    popular_countries = [
        ("🇺🇸", "United States", "US", "en"),
        ("🇯🇵", "Japan", "JP", "ja"),
        ("🇨🇳", "China", "CN", "zh"),
        ("🇻🇳", "Vietnam", "VN", "vi"),
        ("🇹🇭", "Thailand", "TH", "th"),
        ("🇵🇭", "Philippines", "PH", "en"),
        ("🇫🇷", "France", "FR", "fr"),
        ("🇩🇪", "Germany", "DE", "de"),
        ("🇹🇼", "Taiwan", "TW", "zh-TW"),
        ("🇮🇩", "Indonesia", "ID", "id"),
    ]
    
    # 2열 그리드로 국가 버튼 생성
    country_rows = []
    for i in range(0, len(popular_countries), 2):
        row_countries = popular_countries[i:i+2]
        row_buttons = []
        
        for flag, name, code, lang in row_countries:
            button = ft.Container(
                content=ft.Row([
                    ft.Text(flag, size=24 if is_mobile else 28),
                    ft.Text(name, size=14 if is_mobile else 16, weight=ft.FontWeight.W_500, color=ft.Colors.BLACK87),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                bgcolor=ft.LinearGradient(["#7B61FF", "#6C47FF"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
                border_radius=12,
                padding=12 if is_mobile else 16,
                margin=ft.margin.only(bottom=8, right=8),
                on_click=lambda e, c=code, l=lang: on_select(c, l),
                width=page.width * 0.4 if is_mobile else 160,
                height=50 if is_mobile else 60,
                shadow=ft.BoxShadow(blur_radius=8, color="#B0BEC544")
            )
            row_buttons.append(button)
        
        # 2개 미만인 경우 빈 컨테이너로 채움
        while len(row_buttons) < 2:
            row_buttons.append(ft.Container(width=page.width * 0.4 if is_mobile else 160, height=50 if is_mobile else 60))
        
        country_rows.append(ft.Row(row_buttons, alignment=ft.MainAxisAlignment.CENTER, spacing=8))

    return ft.View(
        "/foreign_country_select",
        controls=[
            # 헤더
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=on_back) if on_back else ft.Container(),
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Icon(ft.Icons.LANGUAGE, size=icon_size, color="#6D8BFF"),
                            bgcolor="#EEF2FF",
                            border_radius=12,
                            padding=8 if is_mobile else 10,
                            margin=ft.margin.only(right=12 if is_mobile else 16)
                        ),
                        ft.Column([
                            ft.Text("국적을 선택하세요", size=title_size, weight=ft.FontWeight.BOLD),
                            ft.Text("당신의 출신 국가를 알려주세요", size=desc_size, color=ft.Colors.GREY_600),
                        ], spacing=4)
                    ], alignment=ft.MainAxisAlignment.START),
                ),
            ], alignment=ft.MainAxisAlignment.START, spacing=8),
            
            # 국가 선택 카드 (완전 흰색 배경, 연보라 그림자)
            ft.Container(
                content=ft.Column([
                    ft.Text("인기 국가", size=16 if is_mobile else 18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87),
                    ft.Container(height=16 if is_mobile else 20),
                    *country_rows
                ], spacing=8),
                padding=20 if is_mobile else 24,
                bgcolor=ft.Colors.WHITE,
                border_radius=16 if is_mobile else 18,
                margin=ft.margin.only(top=20 if is_mobile else 30, left=10 if is_mobile else 20, right=10 if is_mobile else 20),
                width=container_width,
                shadow=ft.BoxShadow(blur_radius=24, color="#B0BEC544")
            )
        ],
        bgcolor="#F4F7FE",
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    ) 