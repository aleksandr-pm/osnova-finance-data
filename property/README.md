# @osnova.property · автопубликация Reels (EN)

Аккаунт: статистика коммерческой недвижимости Дубая (DLD, Ejari, листинги порталов). Цель: трафик на osnova.property.
Без предложений купить или продать, без WhatsApp и BRN. В каждом ролике и подписи: источник и «Statistics only · Not an offer or advice».

## Как работает

1. Ролики собираются заранее в чате Claude (движок `pe.py`, данные DLD/Ejari) и кладутся в `property/reels/`.
2. `queue.json`: очередь (id, файл, подпись, кадр обложки). Публикуется первый ролик, которого нет в `state.json`.
3. Workflow `property-reels.yml`: 2 Reels + 1 пост в день. Тест времени через день: набор A (Reels 11:41 и 19:41, пост 15:11), набор B (Reels 08:41 и 21:41, пост 13:11), по Дубаю.
   Workflow `property-stats.yml`: статистика раз в день в `stats.json` и `stats_report.md` (сравнение A/B, слотов, рубрик).
   Картинки постов берутся по ссылке raw.githubusercontent.com с SHA коммита.
   `dm_keywords.json`: слово для DM и ссылка с UTM, которую автоответ отправляет в директ.
4. Публикация идёт только если есть файл `property/LIVE`. Удалить файл = остановить всё.
5. Пауза до даты: ISO-дата в `property/pause_until.txt` (например `2026-11-20T00:00:00+00:00`).

## Токен и аккаунт

- Токен: секрет `IG_TOKEN_PROP`, если его нет, берётся `IG_TOKEN` (тот же системный пользователь OSNOVA Finance Media).
- ID аккаунта: `property/ig_user_id.txt` (пишет `property-check.yml`) или секрет `IG_USER_ID_PROP`.
- Проверка без публикации: изменить `property/check_request.txt` (любой текст) или запустить `property-check` вручную. Результат в `property/logs/check.txt`.
- Разовая публикация вне расписания: изменить `property/publish_request.txt`.

## Правила (из опыта OSNOVA Finance)

- Ошибка на шаге `media_publish` = ролик считается использованным, повторно не отправляется (пост мог выйти).
- Instagram отклонил обработку = ролик `failed`, в этом же запуске одна замена следующим.
- Reels не чаще раза в 5 часов, пост раз в 20 часов.
- Удаление постов через API не делаем.
