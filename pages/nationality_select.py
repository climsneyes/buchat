import flet as ft

def NationalitySelectPage(page, on_select, on_foreign_select, on_back=None):
    return ft.View(
        "/",
        controls=[
            ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=on_back) if on_back else ft.Container(),
                ft.Text("📱 Welcome to Busan Chat!", size=24, weight=ft.FontWeight.BOLD, text_align="center"),
            ], alignment=ft.MainAxisAlignment.START),
            ft.Container(
                content=ft.Column([
                    ft.Text("Where are you from?", size=16, text_align="center", color=ft.Colors.GREY_600),
                    ft.Row([
                        ft.ElevatedButton("🇰🇷 한국인", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)), on_click=lambda e: on_select("ko")),
                        ft.ElevatedButton("🌍 Foreigner", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20)), on_click=lambda e: on_foreign_select()),
                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=30),
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=30),
                padding=40,
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.WHITE,
                border_radius=30,
                shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.GREY_200)
            ),
        ],
        bgcolor=ft.Colors.GREY_100
    )
