import flet as ft
import openai
from config import OPENAI_API_KEY, MODEL_NAME
import os
from flet import Column, Switch
import time
from firebase_admin import db
import uuid

IS_SERVER = os.environ.get("CLOUDTYPE") == "1"  # Cloudtype 환경변수 등으로 구분

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# 언어 코드에 따른 전체 언어 이름 매핑
LANG_NAME_MAP = {
    "ko": "한국어", "en": "영어", "ja": "일본어", "zh": "중국어",
    "fr": "프랑스어", "de": "독일어", "th": "태국어", "vi": "베트남어",
    "zh-TW": "대만어", "zh-HK": "홍콩어", "id": "인도네시아어",
    "zh-SG": "싱가포르 중국어", "en-SG": "싱가포르 영어", "ms-SG": "싱가포르 말레이어", "ta-SG": "싱가포르 타밀어"
}

# RAG 가이드 텍스트 다국어 사전 (상세 구조)
RAG_GUIDE_TEXTS = {
    "ko": {
        "title": "다문화가족 한국생활안내",
        "info": "다음과 같은 정보를 질문할 수 있습니다:",
        "items": [
            "🏥 병원, 약국 이용 방법",
            "🏦 은행, 우체국, 관공서 이용",
            "🚌 교통수단 이용 (버스, 지하철, 기차)",
            "🚗 운전면허, 자가용, 택시 이용",
            "🏠 집 구하기",
            "📱 핸드폰 사용하기",
            "🗑️ 쓰레기 버리기 (종량제, 분리배출)",
            "🆔 외국인등록증 신청, 체류기간 연장"
        ],
        "example_title": "질문 예시:",
        "examples": [
            "• 외국인등록을 하려면 어디로 가요?",
            "• 대한민국에서 더 살게 됐는데 어떡하죠?",
            "• 외국인은 핸드폰을 어떻게 사용하나요?",
            "• 전셋집이 뭐예요?",
            "• 공인중개사무소가 뭐죠?",
            "• 집 계약서는 어떻게 쓰면 되나요?",
            "• 대한민국 운전면허증을 받는 과정은?",
            "• 쓰레기 봉투는 어디서 사나요?",
            "• 쓰레기 버리는 방법은요?",
            "• 몸이 아픈데 어떡하죠?",
            "• 병원에 갈 때 필요한 건강보험증이 뭐죠?",
            "• 한의원은 일반병원과 다른가요?",
            "• 처방전이 없는데 어떻게 하나요?",
            "• 은행계좌는 어떻게 만들어요?",
            "• 외국에 물건을 보내고 싶은데 어떻게 하죠?",
            "• 24시간 콜센터 번호는 어떻게 되죠?",
            "• 긴급전화 번호는 뭐에요?",
            "• 한국어를 배울 수 있는 방법은요?"
        ],
        "input_hint": "아래에 질문을 입력해보세요! 💬"
    },
    "en": {
        "title": "Korean Life Guide for Multicultural Families",
        "info": "You can ask about the following topics:",
        "items": [
            "🏥 How to use hospitals and pharmacies",
            "🏦 How to use banks, post offices, government offices",
            "🚌 How to use public transport (bus, subway, train)",
            "🚗 Driver's license, private car, taxi",
            "🏠 Finding a house",
            "📱 Using a mobile phone",
            "🗑️ How to dispose of trash (volume-based, recycling)",
            "🆔 Alien registration, extension of stay"
        ],
        "example_title": "Example questions:",
        "examples": [
            "• Where do I go to register as a foreigner?",
            "• I need to stay longer in Korea, what should I do?",
            "• How do foreigners use mobile phones?",
            "• What is jeonse (deposit-based housing)?",
            "• What is a real estate agency?",
            "• How do I write a housing contract?",
            "• What is the process for getting a Korean driver's license?",
            "• Where do I buy trash bags?",
            "• How do I dispose of trash?",
            "• I'm sick, what should I do?",
            "• What is health insurance card needed for hospitals?",
            "• Is oriental medicine different from regular hospitals?",
            "• What if I don't have a prescription?",
            "• How do I open a bank account?",
            "• How do I send things abroad?",
            "• What are the 24-hour call center numbers?",
            "• What are the emergency numbers?",
            "• How can I learn Korean?"
        ],
        "input_hint": "Type your question below! 💬"
    },
    "ja": {
        "title": "多文化家族のための韓国生活ガイド",
        "info": "以下のトピックについて質問できます:",
        "items": [
            "🏥 病院、薬局の利用方法",
            "🏦 銀行、郵便局、政府機関の利用",
            "🚌 公共交通機関の利用（バス、地下鉄、電車）",
            "🚗 運転免許、自家用車、タクシー",
            "🏠 家探し",
            "📱 携帯電話の使用",
            "🗑️ ゴミの捨て方（従量制、リサイクル）",
            "🆔 外国人登録、滞在期間延長"
        ],
        "example_title": "質問例:",
        "examples": [
            "• 外国人登録はどこで行いますか？",
            "• 韓国でより長く滞在する必要がありますが、どうすればいいですか？",
            "• 外国人は携帯電話をどのように使用しますか？",
            "• 全税（保証金ベースの住宅）とは何ですか？",
            "• 不動産会社とは何ですか？",
            "• 住宅契約書はどのように書けばいいですか？",
            "• 韓国の運転免許を取得する手続きは？",
            "• ゴミ袋はどこで買えますか？",
            "• ゴミの捨て方は？",
            "• 体調が悪いのですが、どうすればいいですか？",
            "• 病院に行く際に必要な健康保険証とは？",
            "• 韓医院は一般병원と違いますか？",
            "• 処方箋がない場合はどうすればいいですか？",
            "• 銀行口座はどのように開設しますか？",
            "• 海外に物を送りたいのですが、どうすればいいですか？",
            "• 24時間コールセンターの番号は？",
            "• 緊急전화番号は何ですか？",
            "• 韓国語を学ぶ方法は？"
        ],
        "input_hint": "下に質問を入力してください！💬"
    },
    "zh": {
        "title": "多元文化家庭韩国生活指南",
        "info": "您可以询问以下主题:",
        "items": [
            "🏥 如何使用医院和药房",
            "🏦 如何使用银行、邮局、政府机关",
            "🚌 如何使用公共交通（公交车、地铁、火车）",
            "🚗 驾照、私家车、出租车",
            "🏠 找房子",
            "📱 使用手机",
            "🗑️ 如何丢弃垃圾（按量收费、回收）",
            "🆔 外国人登记、延长停留时间"
        ],
        "example_title": "问题示例:",
        "examples": [
            "• 我要去哪里办理外国人登记？",
            "• 我需要在韩国停留更久，该怎么办？",
            "• 外国人如何使用手机？",
            "• 什么是全租房？",
            "• 什么是房地产中介？",
            "• 我该如何写房屋合约？",
            "• 取得韩国驾照的流程是什么？",
            "• 我在哪里买垃圾袋？",
            "• 我该如何丢垃圾？",
            "• 我生病了该怎么办？",
            "• 去医院需要的健康保险卡是什么？",
            "• 韩医院和一般医院有什麽不同？",
            "• 如果没有处方怎么办？",
            "• 我该如何开银行账户？",
            "• 我该如何寄东西到国外？",
            "• 24小时客服电话是多少？",
            "• 紧急电话号码是什么？",
            "• 我该如何学韩文？"
        ],
        "input_hint": "请在下方输入您的问题！💬"
    },
    "zh-TW": {
        "title": "多元文化家庭韓國生活指南",
        "info": "您可以詢問以下主題:",
        "items": [
            "🏥 如何使用醫院和藥局",
            "🏦 如何使用銀行、郵局、政府機關",
            "🚌 如何搭乘大眾運輸（公車、地鐵、火車）",
            "🚗 駕照、私家車、計程車",
            "🏠 找房子",
            "📱 使用手機",
            "🗑️ 如何丟垃圾（按量收費、回收）",
            "🆔 外國人登記、延長停留時間"
        ],
        "example_title": "問題範例:",
        "examples": [
            "• 我要去哪裡辦理外國人登記？",
            "• 我需要在韓國停留更久，該怎麼辦？",
            "• 外國人如何使用手機？",
            "• 什麼是全租房？",
            "• 什麼是房地產仲介？",
            "• 我該如何寫房屋合約？",
            "• 取得韓國駕照的流程是什麼？",
            "• 我在哪裡買垃圾袋？",
            "• 我該如何丟垃圾？",
            "• 我生病了該怎麼辦？",
            "• 去醫院需要的健康保險卡是什麼？",
            "• 韓醫院和一般醫院有什麼不同？",
            "• 如果沒有處方怎麼辦？",
            "• 我該如何開銀行帳戶？",
            "• 我該如何寄東西到國外？",
            "• 24小時客服電話是多少？",
            "• 緊急電話號碼是什麼？",
            "• 我該如何學韓文？"
        ],
        "input_hint": "請在下方輸入您的問題！💬"
    },
    "id": {
        "title": "Panduan Hidup di Korea untuk Keluarga Multikultural",
        "info": "Anda dapat bertanya tentang topik berikut:",
        "items": [
            "🏥 Cara menggunakan rumah sakit dan apotek",
            "🏦 Cara menggunakan bank, kantor pos, kantor pemerintah",
            "🚌 Cara menggunakan transportasi umum (bus, subway, kereta)",
            "🚗 SIM, mobil pribadi, taksi",
            "🏠 Mencari rumah",
            "📱 Menggunakan ponsel",
            "🗑️ Cara membuang sampah (berdasarkan volume, daur ulang)",
            "🆔 Pendaftaran orang asing, perpanjangan masa tinggal"
        ],
        "example_title": "Contoh pertanyaan:",
        "examples": [
            "• Ke mana saya harus pergi untuk mendaftar sebagai orang asing?",
            "• Saya perlu tinggal lebih lama di Korea, apa yang harus saya lakukan?",
            "• Bagaimana orang asing menggunakan ponsel?",
            "• Apa itu jeonse (rumah sewa deposit)?",
            "• Apa itu agen real estat?",
            "• Bagaimana cara menulis kontrak rumah?",
            "• Apa proses mendapatkan SIM Korea?",
            "• Di mana saya membeli kantong sampah?",
            "• Bagaimana cara membuang sampah?",
            "• Saya sakit, apa yang harus saya lakukan?",
            "• Apa itu kartu asuransi kesehatan untuk rumah sakit?",
            "• Apakah pengobatan oriental berbeda dengan rumah sakit biasa?",
            "• Bagaimana jika saya tidak punya resep?",
            "• Bagaimana cara membuka rekening bank?",
            "• Bagaimana cara mengirim barang ke luar negeri?",
            "• Berapa nomor call center 24 jam?",
            "• Berapa nomor darurat?",
            "• Bagaimana cara belajar bahasa Korea?"
        ],
        "input_hint": "Tulis pertanyaan Anda di bawah ini! 💬"
    },
    "vi": {
        "title": "Hướng dẫn cuộc sống Hàn Quốc cho gia đình đa văn hóa",
        "info": "Bạn có thể hỏi về các chủ đề sau:",
        "items": [
            "🏥 Cách sử dụng bệnh viện và nhà thuốc",
            "🏦 Cách sử dụng ngân hàng, bưu điện, cơ quan chính phủ",
            "🚌 Cách sử dụng phương tiện công cộng (xe buýt, tàu điện ngầm, tàu)",
            "🚗 Bằng lái xe, xe riêng, taxi",
            "🏠 Tìm nhà",
            "📱 Sử dụng điện thoại di động",
            "🗑️ Cách vứt rác (theo thể tích, tái chế)",
            "🆔 Đăng ký người nước ngoài, gia hạn thời gian lưu trú"
        ],
        "example_title": "Ví dụ câu hỏi:",
        "examples": [
            "• Tôi đi đâu để đăng ký người nước ngoài?",
            "• Tôi cần ở lại Hàn Quốc lâu hơn, tôi nên làm gì?",
            "• Người nước ngoài sử dụng điện thoại di động như thế nào?",
            "• Jeonse (nhà ở theo tiền đặt cọc) là gì?",
            "• Công ty bất động sản là gì?",
            "• Tôi viết hợp đồng nhà như thế nào?",
            "• Quy trình lấy bằng lái xe Hàn Quốc là gì?",
            "• Tôi mua túi rác ở đâu?",
            "• Tôi vứt rác như thế nào?",
            "• Tôi bị bệnh, tôi nên làm gì?",
            "• Thẻ bảo hiểm y tế cần thiết cho bệnh viện là gì?",
            "• Y học cổ truyền có khác với bệnh viện thường không?",
            "• Nếu tôi không có đơn thuốc thì sao?",
            "• Tôi mở tài khoản ngân hàng như thế nào?",
            "• Tôi gửi đồ ra nước ngoài như thế nào?",
            "• Số điện thoại trung tâm cuộc gọi 24 giờ là gì?",
            "• Số điện thoại khẩn cấp là gì?",
            "• Tôi có thể học tiếng Hàn như thế nào?"
        ],
        "input_hint": "Nhập câu hỏi của bạn bên dưới! 💬"
    },
    "fr": {
        "title": "Guide de vie en Corée pour familles multiculturelles",
        "info": "Vous pouvez poser des questions sur les sujets suivants :",
        "items": [
            "🏥 Comment utiliser les hôpitaux et pharmacies",
            "🏦 Comment utiliser les banques, bureaux de poste, bureaux gouvernementaux",
            "🚌 Comment utiliser les transports publics (bus, métro, train)",
            "🚗 Permis de conduire, voiture privée, taxi",
            "🏠 Trouver une maison",
            "📱 Utiliser un téléphone portable",
            "🗑️ Comment jeter les déchets (basé sur le volume, recyclage)",
            "🆔 Enregistrement des étrangers, prolongation du séjour"
        ],
        "example_title": "Exemples de questions :",
        "examples": [
            "• Comment inscrire mon enfant à l'école coréenne ?",
            "• Comment demander l'assurance maladie coréenne ?",
            "• Parlez-moi de la culture culinaire coréenne",
            "• Comment utiliser les transports publics coréens ?"
        ],
        "input_hint": "Tapez votre question ci-dessous ! 💬"
    },
    "de": {
        "title": "Leitfaden für das Leben in Korea für multikulturelle Familien",
        "info": "Sie können Fragen zu folgenden Themen stellen:",
        "items": [
            "🏥 Wie man Krankenhäuser und Apotheken nutzt",
            "🏦 Wie man Banken, Postämter, Regierungsbüros nutzt",
            "🚌 Wie man öffentliche Verkehrsmittel nutzt (Bus, U-Bahn, Zug)",
            "🚗 Führerschein, Privatauto, Taxi",
            "🏠 Haus finden",
            "📱 Mobiltelefon nutzen",
            "🗑️ Wie man Müll entsorgt (volumenbasiert, Recycling)",
            "🆔 Ausländerregistrierung, Aufenthaltsverlängerung"
        ],
        "example_title": "Beispielfragen:",
        "examples": [
            "• Wie melde ich mein Kind in einer koreanischen Schule an?",
            "• Wie beantrage ich koreanische Krankenversicherung?",
            "• Erzählen Sie mir von der koreanischen Esskultur",
            "• Wie benutze ich koreanische öffentliche Verkehrsmittel?"
        ],
        "input_hint": "Geben Sie Ihre Frage unten ein! 💬"
    },
    "th": {
        "title": "คู่มือการใช้ชีวิตในเกาหลีสำหรับครอบครัวพหุวัฒนธรรม",
        "info": "คุณสามารถถามเกี่ยวกับหัวข้อต่อไปนี้:",
        "items": [
            "🏥 วิธีใช้โรงพยาบาลและร้านขายยา",
            "🏦 วิธีใช้ธนาคาร ที่ทำการไปรษณีย์ สำนักงานรัฐบาล",
            "🚌 วิธีใช้ระบบขนส่งสาธารณะ (รถบัส รถไฟใต้ดิน รถไฟ)",
            "🚗 ใบขับขี่ รถส่วนตัว แท็กซี่",
            "🏠 หาบ้าน",
            "📱 ใช้โทรศัพท์มือถือ",
            "🗑️ วิธีทิ้งขยะ (ตามปริมาณ การรีไซเคิล)",
            "🆔 การลงทะเบียนชาวต่างชาติ การขยายเวลาพำนัก"
        ],
        "example_title": "ตัวอย่างคำถาม:",
        "examples": [
            "• ฉันจะลงทะเบียนลูกในโรงเรียนเกาหลีได้อย่างไร?",
            "• ฉันจะสมัครประกันสุขภาพเกาหลีได้อย่างไร?",
            "• บอกฉันเกี่ยวกับวัฒนธรรมอาหารเกาหลี",
            "• ฉันจะใช้ระบบขนส่งสาธารณะของเกาหลีได้อย่างไร?"
        ],
        "input_hint": "พิมพ์คำถามของคุณด้านล่าง! 💬"
    }
}

def translate_message(text, target_lang):
    try:
        target_lang_name = LANG_NAME_MAP.get(target_lang, "영어")
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a helpful translator."},
                {"role": "user", "content": f"다음 문장을 {target_lang_name}로 번역해줘:\n{text}"}
            ],
            max_tokens=1000,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[번역 오류] {e}"

def transcribe_from_mic(input_box: ft.TextField, page: ft.Page, mic_button: ft.IconButton):
    if IS_SERVER:
        input_box.hint_text = "서버에서는 음성 입력이 지원되지 않습니다."
        page.update()
        return
    import sounddevice as sd
    from scipy.io.wavfile import write
    samplerate = 44100  # Sample rate
    duration = 5  # seconds
    filename = "temp_recording.wav"

    original_hint_text = input_box.hint_text
    try:
        # 1. 녹음 시작 알림
        mic_button.disabled = True
        input_box.hint_text = "녹음 중... (5초)"
        page.update()

        # 2. 녹음
        recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
        sd.wait()  # Wait until recording is finished

        # 3. 파일로 저장
        write(filename, samplerate, recording)

        # 4. Whisper API로 전송
        input_box.hint_text = "음성 분석 중..."
        page.update()
        with open(filename, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
              model="whisper-1",
              file=audio_file
            )
        
        # 5. 결과 입력
        input_box.value = transcript.text
        
    except Exception as e:
        input_box.hint_text = f"오류: {e}"
        print(f"Whisper STT 오류: {e}")
    finally:
        # 6. 정리
        input_box.hint_text = original_hint_text
        mic_button.disabled = False
        if os.path.exists(filename):
            os.remove(filename)
        page.update()

def ChatRoomPage(page, room_id, room_title, user_lang, target_lang, on_back=None, on_share=None, custom_translate_message=None, firebase_available=True):
    # 화면 크기에 따른 반응형 설정
    is_mobile = page.width < 600
    is_tablet = 600 <= page.width < 1024
    
    # 반응형 크기 계산
    title_size = 18 if is_mobile else 22
    nickname_size = 10 if is_mobile else 12
    message_size = 14 if is_mobile else 16
    translated_size = 10 if is_mobile else 12
    input_height = 45 if is_mobile else 50
    bubble_padding = 8 if is_mobile else 12
    header_padding = 12 if is_mobile else 16
    
    # --- 상태 및 컨트롤 초기화 ---
    chat_messages = Column(auto_scroll=True, spacing=10 if is_mobile else 15, expand=True)
    current_target_lang = [target_lang]
    is_korean = user_lang == "ko"
    # RAG 채팅방인지 확인
    is_rag_room = custom_translate_message is not None
    # 언어별 입력창 안내문구
    RAG_INPUT_HINTS = {
        "ko": "한국생활에 대해 질문하세요",
        "en": "Ask about life in Korea",
        "vi": "Hãy hỏi về cuộc sống ở Hàn Quốc",
        "ja": "韓国での生活について質問してください",
        "zh": "请咨询有关在韩国生活的问题",
        "fr": "Posez des questions sur la vie en Corée",
        "de": "Stellen Sie Fragen zum Leben in Korea",
        "th": "สอบถามเกี่ยวกับการใช้ชีวิตในเกาหลีได้เลย",
        "zh-TW": "請詢問有關在韓國生活的問題",
        "id": "Tanyakan tentang kehidupan di Korea",
    }
    input_hint = RAG_INPUT_HINTS.get(user_lang, RAG_INPUT_HINTS["en"]) if is_rag_room else {
        "ko": "메시지 입력",
        "en": "Type a message",
        "vi": "Nhập tin nhắn",
        "ja": "メッセージを入力",
        "zh": "输入消息",
        "fr": "Entrez un message",
        "de": "Nachricht eingeben",
        "th": "พิมพ์ข้อความ",
        "zh-TW": "輸入訊息",
        "id": "Ketik pesan",
    }.get(user_lang, "Type a message")
    input_box = ft.TextField(hint_text=input_hint, expand=True, height=input_height)
    if is_rag_room:
        translate_switch = None  # RAG 답변 ON/OFF 스위치 제거
    else:
        switch_label = "번역 ON/OFF" if is_korean else "Translate ON/OFF"
        translate_switch = ft.Switch(label=switch_label, value=True)

    def on_target_lang_change(e):
        current_target_lang[0] = e.control.value

    # 번역 대상 언어 드롭다운 옵션 (국기+영어 국가명)
    target_lang_options = [
        ("ko", "🇰🇷 Korean"),
        ("en", "🇺🇸 English"),
        ("ja", "🇯🇵 Japanese"),
        ("zh", "🇨🇳 Chinese"),
        ("zh-TW", "🇹🇼 Taiwanese"),
        ("id", "🇮🇩 Indonesian"),
        ("ms", "🇲🇾 Malay"),
        ("ta", "🇮🇳 Tamil"),
        ("fr", "🇫🇷 French"),
        ("de", "🇩🇪 German"),
        ("th", "🇹🇭 Thai"),
        ("vi", "🇻🇳 Vietnamese"),
    ]
    target_lang_dropdown = ft.Dropdown(
        value=current_target_lang[0],
        options=[ft.dropdown.Option(key, text) for key, text in target_lang_options],
        width=180 if is_mobile else 220,
        on_change=on_target_lang_change
    ) if not is_rag_room else None

    def create_message_bubble(msg_data, is_me):
        """메시지 말풍선을 생성하는 함수"""
        message_column = ft.Column(
            [
                ft.Text(msg_data.get('nickname', '익명'), size=nickname_size, color=ft.Colors.GREY_700, selectable=True),  # 닉네임 표시
                ft.Text(msg_data['text'], color=ft.Colors.WHITE if is_me else ft.Colors.BLACK, size=message_size, selectable=True),
                ft.Text(
                    f"({msg_data['translated']})" if msg_data.get('translated') else "",
                    color=ft.Colors.WHITE70 if is_me else ft.Colors.GREY_700,
                    size=translated_size,
                    italic=True,
                    selectable=True,
                )
            ],
            spacing=3 if is_mobile else 4,
        )

        bubble = ft.Container(
            content=message_column,
            padding=bubble_padding,
            border_radius=15 if is_mobile else 18,
            bgcolor=ft.Colors.BLUE_500 if is_me else ft.Colors.GREY_300,  # 본인: 파란색, 상대: 회색
            margin=ft.margin.only(top=3 if is_mobile else 5, bottom=3 if is_mobile else 5, left=3 if is_mobile else 5, right=3 if is_mobile else 5),
            alignment=ft.alignment.center_right if is_me else ft.alignment.center_left,  # 본인: 오른쪽, 상대: 왼쪽
            width=page.width * 0.75 if is_mobile else None,  # 모바일에서 최대 너비 제한
        )

        # 내가 보낸 메시지는 오른쪽, 상대 메시지는 왼쪽에 정렬
        return ft.Row(
            controls=[bubble],
            alignment=ft.MainAxisAlignment.END if is_me else ft.MainAxisAlignment.START,  # 본인: 오른쪽, 상대: 왼쪽
        )

    # --- Firebase 리스너 콜백 ---
    def on_message(event):
        
        # RAG 채팅방인 경우 안내 메시지 표시
        if is_rag_room and len(chat_messages.controls) == 0:
            guide_texts = RAG_GUIDE_TEXTS.get(user_lang, RAG_GUIDE_TEXTS["ko"])
            
            # 안내 메시지 생성
            def get_rag_guide_message():
                guide_items = []
                for item in guide_texts["items"]:
                    guide_items.append(ft.Text(item, size=12 if is_mobile else 14, color=ft.Colors.GREY_700, selectable=True))
                
                example_items = []
                for example in guide_texts["examples"]:
                    example_items.append(ft.Text(example, size=11 if is_mobile else 12, color=ft.Colors.GREY_600, selectable=True))
                
                return ft.Container(
                    content=ft.Column([
                        ft.Text(guide_texts["title"], size=16 if is_mobile else 18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600, selectable=True),
                        ft.Container(height=8),
                        ft.Text(guide_texts["info"], size=13 if is_mobile else 14, color=ft.Colors.GREY_700, selectable=True),
                        ft.Container(height=8),
                        *guide_items,
                        ft.Container(height=12),
                        ft.Text(guide_texts["example_title"], size=13 if is_mobile else 14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_700, selectable=True),
                        ft.Container(height=6),
                        *example_items,
                        ft.Container(height=12),
                        ft.Text(guide_texts["input_hint"], size=13 if is_mobile else 14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_600, text_align=ft.TextAlign.CENTER, selectable=True),
                    ], spacing=4),
                    padding=16 if is_mobile else 20,
                    bgcolor=ft.LinearGradient(["#E3F2FD", "#BBDEFB"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
                    border_radius=12,
                    margin=ft.margin.only(bottom=16),
                    border=ft.border.all(1, "#2196F3")
                )
            
            chat_messages.controls.append(get_rag_guide_message())
            
            def set_scroll():
                page.update()
                time.sleep(0.1)
                chat_messages.scroll_to(offset=0)
                page.update()
            
            set_scroll()
            return
        
        # 일반 메시지 처리
        if event.data:
            try:
                data = event.data
                if isinstance(data, str):
                    import json
                    data = json.loads(data)
                
                # 메시지 데이터 추출
                msg_data = {
                    'text': data.get('text', ''),
                    'nickname': data.get('nickname', '익명'),
                    'timestamp': data.get('timestamp', ''),
                    'translated': data.get('translated', '')
                }
                
                # 메시지 말풍선 생성
                is_me = msg_data['nickname'] == (page.session.get('nickname') or '')
                message_bubble = create_message_bubble(msg_data, is_me)
                
                # 채팅창에 메시지 추가
                chat_messages.controls.append(message_bubble)
                
                # 스크롤을 맨 아래로
                def set_scroll():
                    page.update()
                    time.sleep(0.1)
                    chat_messages.scroll_to(offset=999999)
                    page.update()
                
                set_scroll()
                
            except Exception as e:
                print(f"메시지 처리 오류: {e}")

    # --- 메시지 전송 함수 ---
    def send_message(e=None):
        if not input_box.value or not input_box.value.strip():
            return
        
        message_text = input_box.value.strip()
        nickname = page.session.get('nickname') or '익명'
        
        # 번역 처리
        translated_text = ""
        if translate_switch and translate_switch.value and current_target_lang[0]:
            try:
                translated_text = translate_message(message_text, current_target_lang[0])
            except Exception as e:
                translated_text = f"[번역 오류: {e}]"
        
        # Firebase에 메시지 저장
        if firebase_available:
            try:
                message_data = {
                    'text': message_text,
                    'nickname': nickname,
                    'timestamp': time.time(),
                    'translated': translated_text
                }
                
                # Firebase에 메시지 저장
                db.reference(f'rooms/{room_id}/messages').push(message_data)
                
            except Exception as e:
                print(f"Firebase 저장 오류: {e}")
                # Firebase 실패시 로컬에만 표시
                msg_data = {
                    'text': message_text,
                    'nickname': nickname,
                    'timestamp': time.time(),
                    'translated': translated_text
                }
                message_bubble = create_message_bubble(msg_data, True)
                chat_messages.controls.append(message_bubble)
                page.update()
        else:
            # Firebase 없을 때 로컬에만 표시
            msg_data = {
                'text': message_text,
                'nickname': nickname,
                'timestamp': time.time(),
                'translated': translated_text
            }
            message_bubble = create_message_bubble(msg_data, True)
            chat_messages.controls.append(message_bubble)
            page.update()
        
        # 입력창 초기화
        input_box.value = ""
        page.update()
        
        # 스크롤을 맨 아래로
        def set_scroll():
            page.update()
            time.sleep(0.1)
            chat_messages.scroll_to(offset=999999)
            page.update()
        
        set_scroll()

    # --- 뒤로가기 함수 ---
    def go_back(e):
        if on_back:
            on_back(e)

    # --- Firebase 리스너 설정 ---
    if firebase_available:
        try:
            # Firebase 리스너 설정
            db.reference(f'rooms/{room_id}/messages').listen(on_message)
        except Exception as e:
            print(f"Firebase 리스너 설정 오류: {e}")

    # --- UI 구성 ---
    # 다국어 '빠른 채팅방' 타이틀 사전
    QUICK_ROOM_TITLES = {
        "ko": "빠른 채팅방",
        "en": "Quick Chat Room",
        "ja": "クイックチャットルーム",
        "zh": "快速聊天室",
        "zh-TW": "快速聊天室",
        "id": "Ruang Obrolan Cepat",
        "vi": "Phòng chat nhanh",
        "fr": "Salon de discussion rapide",
        "de": "Schnell-Chatraum",
        "th": "ห้องแชทด่วน"
    }
    # 공식 안내 채팅방(RAG) 헤더 타이틀 다국어 처리
    is_rag_room = custom_translate_message is not None
    rag_title = None
    if is_rag_room:
        rag_title = RAG_GUIDE_TEXTS.get(user_lang, RAG_GUIDE_TEXTS["en"])['title']
    # 헤더 (뒤로가기 + 방 제목 + 공유 버튼)
    display_room_title = rag_title if is_rag_room else (
        QUICK_ROOM_TITLES.get(user_lang, "Quick Chat Room") if room_title in ["빠른 채팅방", "Quick Chat Room"] else room_title
    )
    header = ft.Container(
        content=ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK, on_click=go_back),
            ft.Text(display_room_title, size=title_size, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK87, expand=True, selectable=True),
            ft.IconButton(ft.Icons.SHARE, on_click=on_share) if on_share else ft.Container(),
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=header_padding,
        bgcolor=ft.Colors.WHITE,
        border_radius=8 if is_mobile else 10,
        margin=ft.margin.only(bottom=8),
        shadow=ft.BoxShadow(blur_radius=4, color="#B0BEC544")
    )

    # 하단 입력 영역
    input_row = ft.Row([
        input_box,
        ft.IconButton(
            ft.Icons.MIC,
            on_click=lambda e: transcribe_from_mic(input_box, page, e.control),
            tooltip="음성 입력"
        ) if not IS_SERVER else ft.Container(),
        ft.IconButton(
            ft.Icons.SEND,
            on_click=send_message,
            tooltip="전송"
        ),
    ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    # 번역 스위치 + 드롭다운 (RAG 채팅방이 아닐 때만)
    switch_row = ft.Container(
        content=ft.Row([
            translate_switch,
            target_lang_dropdown if target_lang_dropdown else ft.Container(),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=12),
        padding=8 if is_mobile else 12,
        margin=ft.margin.only(bottom=8)
    ) if translate_switch else ft.Container()

    return ft.View(
        f"/chat/{room_id}",
        controls=[
            header,
            ft.Container(
                content=chat_messages,
                expand=True,
                padding=8 if is_mobile else 12,
            ),
            switch_row,
            ft.Container(
                content=input_row,
                padding=header_padding,
                bgcolor=ft.Colors.WHITE,
                border_radius=8,
                margin=ft.margin.only(top=8),
                shadow=ft.BoxShadow(blur_radius=4, color="#B0BEC544")
            ),
        ],
        bgcolor=ft.LinearGradient(["#F8FAFC", "#F1F5F9"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right)
    )

# 환경변수에서 firebase_key.json 내용을 읽어서 파일로 저장
firebase_key_json = os.getenv("FIREBASE_KEY_JSON")
if firebase_key_json:
    with open("firebase_key.json", "w", encoding="utf-8") as f:
        f.write(firebase_key_json)
