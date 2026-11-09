# Restoran buyurtmalarini hisobga olish tizimi

Python 3.10+ bilan ishlaydigan konsol ilovasi. Ma'lumotlar odatda joriy katalogdagi `restaurant_data.json` faylida saqlanadi.

## Ishga tushirish

```bash
python restaurant.py
```

Buyruqlar argumentlari bo'shliq bilan ajratiladi; nomida bo'shliq bor taomni qo'shishda qo'shtirnoq ishlating.

```text
add-table <stol_raqami> <o'rinlar>
add-dish "<nomi>" <narxi> <ovqat|ichimlik>
open <stol_raqami> [ha]
add <stol_raqami> "<taom_nomi>" [miqdor]
remove <stol_raqami> "<taom_nomi>" [miqdor]
bill <stol_raqami> [mehmonlar_soni]
close <stol_raqami> [mehmonlar_soni]
exit
```

`open` buyrug'idagi `ha` sodiqlik kartasi mavjudligini bildiradi. Hisobda avval 10% xizmat haqi qo'shiladi, keyin yakuniy summadan 15% chegirma olinadi. `bill` va `close` mehmonlar soni berilsa, bir kishiga to'g'ri keladigan summani ham chiqaradi.

## Testlar

```bash
python3 -m pip install -r requirements.txt
python -m pytest -q
```

## Chegaralar va keyingi bosqichlar

2-bosqichdagi stol ko'chirish/birlashtirish va 3-bosqichdagi aksiyalar hamda baxtli soatlar ataylab hozirgi minimal versiyaga kiritilmadi. Ular ADR.md da alohida kengaytirish nuqtalari sifatida qayd etilgan.