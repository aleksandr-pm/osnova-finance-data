# Сторис @aleksandr_markets

Каждый будний день в 08:15 по Дубаю (workflow `am-stories.yml`) две сторис:
1. Итоги торгов ОАЭ: FTSE ADX General, DFM General, DFM Real Estate; 5 лидеров роста и падения среди компаний дороже 5 млрд AED; Brent, золото, USD/AED.
2. Итоги торгов США: S&P 500, Nasdaq 100, Dow Jones; 5 лидеров роста и падения среди S&P 500; Brent, UST 10 лет, золото, EUR/USD.

Скрипт: `scripts/am_stories.py` (probe / render / publish).

Включение публикации:
- секреты репозитория: `IG_USER_ID_AM` (числовой ID аккаунта aleksandr_markets) и `IG_TOKEN_AM` (токен системного пользователя с доступом к этому аккаунту; если не задан, берётся `IG_TOKEN`);
- файл `am/LIVE` в репозитории. Без него сторис только рисуются.

Пауза: дата и время в `am/pause_until.txt` (например `2026-11-20T08:00:00+04:00`).
Фоны: `am/bg/uae_*.jpg`, `am/bg/us_*.jpg`, меняются по дням.
Правило: после любой ошибки публикации сторис помечается в `am/state_stories.json` и не повторяется.
