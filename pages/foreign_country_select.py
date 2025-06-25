import flet as ft

def ForeignCountrySelectPage(page, on_select, on_back=None):
    country_options = [
        ("us", "🇺🇸 United States"),
        ("jp", "🇯🇵 Japan"),
        ("cn", "🇨🇳 China"),
        ("fr", "🇫🇷 France"),
        ("de", "🇩🇪 Germany"),
        ("th", "🇹🇭 Thailand"),
        ("vn", "🇻🇳 Vietnam"),
        ("etc", "🌏 Other"),
    ]
    return ft.View(
        "/foreign_country_select",
        controls=[
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=on_back) if on_back else ft.Container(),
                ft.Text("국적을 선택하세요", size=22, weight=ft.FontWeight.BOLD),
            ], alignment=ft.MainAxisAlignment.START),
            ft.Container(
                content=ft.Column([
                    ft.Text("Which country are you from?", size=16, color=ft.Colors.GREY_600),
                    ft.Column([
                        ft.ElevatedButton(label, on_click=lambda e, code=code: on_select(code))
                        for code, label in country_options
                    ], spacing=10)
                ], spacing=20),
                padding=30,
                bgcolor=ft.Colors.WHITE,
                border_radius=30,
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.GREY_200)
            )
        ],
        bgcolor=ft.Colors.GREY_100
    ) 