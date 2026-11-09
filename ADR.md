# Architecture Decision Record

## ADR-001: Bitta moduldagi domen va CLI

Kichik konsol ilovasi uchun domen modeli va buyruq adapteri `restaurant.py` faylida saqlandi. Bu qo'shimcha framework va konfiguratsiyasiz ishga tushirishni osonlashtiradi; keyinchalik CLI alohida modulga ajratilishi mumkin.

## ADR-002: JSON faylga saqlash

Tashqi ma'lumotlar bazasi talab qilinmagani uchun JSON tanlandi. Har bir o'zgarish vaqtinchalik faylga yozilib, `os.replace` orqali almashtiriladi. Decimal qiymatlar aniqlikni saqlash uchun satr ko'rinishida yoziladi.

## ADR-003: Hisoblash tartibi

Formula: `subtotal = pozitsiyalar yig'indisi`, `service = subtotal * 10%`, `discount = (subtotal + service) * 15%` (faqat sodiqlik kartasi bo'lsa), `total = subtotal + service - discount`. Bu chegirmani xizmat haqi qo'shilgan yakuniy oraliq summaga qo'llash haqidagi farazdir.

## ADR-004: Buyurtma va to'lov farazlari

- Bir stolga faqat bitta ochiq buyurtma ruxsat etiladi.
- Taom nomi menyuda yagona identifikator hisoblanadi.
- `close` to'lovni tasdiqlaydi, buyurtmani ochiq buyurtmalar ro'yxatidan olib tashlaydi.
- 2- va 3-bosqich funksiyalari ushbu versiyaga kiritilmagan.