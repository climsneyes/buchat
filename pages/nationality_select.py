import flet as ft

def NationalitySelectPage(page, on_select, on_foreign_select, on_back=None):
    # 화면 크기에 따른 반응형 설정
    is_mobile = page.width < 600
    is_tablet = 600 <= page.width < 1024
    
    # 반응형 크기 계산
    container_width = min(page.width * 0.9, 500) if not is_mobile else page.width * 0.95
    button_width = min(250, page.width * 0.8)
    title_size = 28 if is_mobile else 32
    desc_size = 14 if is_mobile else 16
    button_height = 45 if is_mobile else 50
    
    return ft.View(
        "/",
        controls=[
            # 상단 타이틀
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(name=ft.Icons.CHAT_BUBBLE_OUTLINE, color="#7B61FF", size=36 if is_mobile else 40),
                        ft.Text("Welcome to Busan Chat!", size=title_size, weight=ft.FontWeight.BOLD, color="#7B61FF"),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=8 if is_mobile else 10),
                    ft.Text(
                        "부산에서 새로운 친구들과 만나고 소통하세요. 다양한 언어로 대화하며 문화를 교류해보세요.",
                        size=desc_size, text_align="center", color=ft.Colors.GREY_700
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8 if is_mobile else 10),
                padding=ft.padding.only(top=30 if is_mobile else 40, bottom=20 if is_mobile else 30)
            ),

            # 국적 선택 카드
            ft.Container(
                content=ft.Column([
                    ft.Text("Where are you from?", size=16 if is_mobile else 18, weight=ft.FontWeight.BOLD, text_align="center"),
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(name=ft.Icons.FLAG, color="#7B61FF", size=20 if is_mobile else 24),
                            ft.Text("KR  한국인", size=14 if is_mobile else 16)
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=8 if is_mobile else 10),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
                        on_click=lambda e: on_select("ko"),
                        width=button_width,
                        height=button_height
                    ),
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(name=ft.Icons.PUBLIC, color="#7B61FF", size=20 if is_mobile else 24),
                            ft.Text("Foreigner", size=14 if is_mobile else 16)
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=8 if is_mobile else 10),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)),
                        on_click=lambda e: on_foreign_select(),
                        width=button_width,
                        height=button_height
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16 if is_mobile else 20),
                padding=30 if is_mobile else 40,
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.WHITE,
                border_radius=25 if is_mobile else 30,
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.GREY_200),
                margin=ft.margin.symmetric(horizontal=10 if is_mobile else 0, vertical=0),
                width=container_width
            ),

            # 하단 안내 카드 2개 (실시간 채팅, 다국어 지원만 한 줄에)
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(name=ft.Icons.PEOPLE, color="#7B61FF", size=24 if is_mobile else 28),
                            ft.Text("실시간 채팅", weight=ft.FontWeight.BOLD, size=12 if is_mobile else 14),
                            ft.Text("부산 지역 사람들과 실시간으로 대화하세요", size=10 if is_mobile else 12, color=ft.Colors.GREY_600)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4 if is_mobile else 5),
                        bgcolor="#F5F7FF", border_radius=15 if is_mobile else 20, padding=15 if is_mobile else 20, expand=1
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(name=ft.Icons.LANGUAGE, color="#A259FF", size=24 if is_mobile else 28),
                            ft.Text("다국어 지원", weight=ft.FontWeight.BOLD, size=12 if is_mobile else 14),
                            ft.Text("한국어와 영어로 자유롭게 소통하세요", size=10 if is_mobile else 12, color=ft.Colors.GREY_600)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4 if is_mobile else 5),
                        bgcolor="#F5F7FF", border_radius=15 if is_mobile else 20, padding=15 if is_mobile else 20, expand=1
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10 if is_mobile else 20),
                padding=ft.padding.only(top=30 if is_mobile else 40)
            ),
        ],
        bgcolor="#F5F7FF",
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )
