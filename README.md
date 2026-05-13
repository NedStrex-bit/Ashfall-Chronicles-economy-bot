# Discord-бот Ashfall Chronicles

Базовый Discord-бот для сервера Ashfall Chronicles: заявки на проверку, начисление Ash Marks, профили, история, лидерборды и автоматическая синхронизация ролей.

## Требования

- Python 3.11+
- Discord-приложение с ботом в Discord Developer Portal
- `discord.py` 2.x
- `python-dotenv`

## Быстрый старт

Создайте локальный `.env` из примера:

```bash
cp .env.example .env
```

Заполните переменные:

```env
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_discord_server_id_here
REWARDS_LOG_CHANNEL_ID=optional_rewards_log_channel_id_here
REVIEW_QUEUE_CHANNEL_ID=optional_review_queue_channel_id_here
PATH_MESSAGE_ID=optional_choose_your_path_message_id_here
```

`DISCORD_TOKEN` нельзя коммитить и нельзя хардкодить в коде.

`REWARDS_LOG_CHANNEL_ID` необязателен. Оставьте пустым или поставьте `0`, чтобы отключить лог начислений.

`REVIEW_QUEUE_CHANNEL_ID` нужен для `/submit`. Оставьте пустым или поставьте `0`, чтобы отключить отправку заявок.

`PATH_MESSAGE_ID` понадобится для будущей функции reaction roles в канале
`#choose-your-path`. Это ID сообщения, под которым участники будут ставить
реакции для выбора пути. Пока сама выдача ролей по реакциям не реализована.

## Установка зависимостей

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Запуск

```bash
python bot.py
```

При запуске бот:

- инициализирует SQLite-базу `ashfall.db`;
- загружает slash-команды;
- синхронизирует команды для сервера из `GUILD_ID`.

Проверочная команда:

```text
/ping
```

Ответ:

```text
Pong! Bot is working.
```

## База данных

Бот использует стандартный модуль Python `sqlite3`, без ORM.

Файл базы создаётся автоматически:

```text
ashfall.db
```

Таблицы:

- `users` — общий баланс Ash Marks участника.
- `branch_progress` — прогресс участника по веткам.
- `transactions` — история начислений и корректировок.
- `submissions` — заявки из `/submit` и их статус проверки.

Схема создаётся через `CREATE TABLE IF NOT EXISTS`, поэтому существующая база не удаляется.

## Команды

### `/ping`

Назначение: проверить, что бот отвечает.

Кто может использовать: все участники.

Пример:

```text
/ping
```

### `/submit`

Назначение: отправить отчёт на проверку администрации.

Кто может использовать: все участники.

Пример:

```text
/submit branch:voice action_type:feed_post proof_url:https://example.com description:Shared a post metrics:120 views
```

Команда не начисляет Ash Marks. Она создаёт запись в `submissions` и отправляет embed в review-queue канал. В сообщении есть кнопки `Approve` и `Reject`.

`Approve` только помечает заявку как approved и просит администратора начислить очки через `/approve`. Автоматического начисления с кнопки нет.

### `/approve`

Назначение: начислить Ash Marks после проверки заявки.

Кто может использовать: участники с правом `Manage Server`.

Пример:

```text
/approve user:@Member branch:voice action_key:feed_post bonus_key:views_1000_or_100_reactions proof_url:https://example.com comment:Verified
```

Команда:

- рассчитывает `base_marks` по `action_key`;
- рассчитывает `bonus_marks` по `bonus_key`, если он указан;
- записывает транзакцию;
- обновляет общий и веточный баланс;
- синхронизирует Discord-роли прогрессии;
- отправляет лог в `REWARDS_LOG_CHANNEL_ID`, если канал настроен.

### `/adjust`

Назначение: вручную добавить или снять Ash Marks в одной ветке.

Кто может использовать: участники с правом `Manage Server`.

Пример:

```text
/adjust user:@Member branch:wardens amount:-2 reason:Duplicate report
```

Команда не даёт балансу уйти ниже нуля, пишет транзакцию `manual_adjustment` и синхронизирует роли.

### `/remove_marks`

Назначение: снять Ash Marks у участника в выбранной ветке.

Кто может использовать: участники с правом `Manage Server`.

Пример:

```text
/remove_marks user:@Member branch:voice amount:3 reason:Duplicate submission
```

`amount` вводится положительным числом. Если в ветке меньше очков, чем нужно
снять, бот снимет только доступное количество. Общий и веточный баланс не уходят
ниже нуля. Команда пишет транзакцию `manual_adjustment`, синхронизирует роли и
логирует действие в rewards-log, если канал настроен.

### `/sync_roles`

Назначение: синхронизировать Discord-роли участника по текущим данным в базе.

Кто может использовать: участники с правом `Manage Server`.

Пример:

```text
/sync_roles user:@Member
```

Команда не меняет баланс.

### `/profile`

Назначение: показать профиль участника, общий статус и прогресс по веткам.

Кто может использовать: все участники.

Пример:

```text
/profile
/profile user:@Member
```

Если пользователь не указан, показывается профиль автора команды.

### `/history`

Назначение: показать последние транзакции Ash Marks.

Кто может использовать: все участники.

Пример:

```text
/history user:@Member limit:10
```

`limit` ограничивается диапазоном от `1` до `20`.

### `/leaderboard`

Назначение: показать топ участников по общему балансу или конкретной ветке.

Кто может использовать: все участники.

Пример:

```text
/leaderboard branch:total limit:10
/leaderboard branch:voice limit:20
```

Если `branch` не указан или выбран `total`, используется `users.total_marks`. Для веток используется `branch_progress.marks`.

Пользователи с `0` очков не показываются. Если участника уже нет на сервере, вместо mention будет показан его Discord user ID.

## Ветки

- `voice` — The Voice of Ashfall
- `atelier` — The Atelier of Ash
- `merchant` — The Merchant Covenant
- `wardens` — The Chronicle Wardens

## Награды за действия

`/approve` использует `action_key` и необязательный `bonus_key`. Администратор больше не вводит `base_marks` вручную.

### Voice action_key

- `story_repost` = 2
- `feed_post` = 6
- `reddit_post` = 6
- `facebook_group_post` = 6
- `reel_short` = 8
- `detailed_review_thread` = 10
- `long_form_video` = 14

### Voice bonus_key

- `views_1000_or_100_reactions` = 2
- `views_5000_or_300_reactions` = 4
- `views_10000_or_1000_reactions` = 6

### Atelier action_key

- `painted_model_photo` = 8
- `printed_scene_photo` = 8
- `fan_art` = 10
- `diorama_full_scene` = 12
- `painting_process_reel` = 10
- `high_quality_photoset` = 12
- `major_showcase_project` = 16

### Atelier bonus_key

- `strong_feature_worthy_work` = 2
- `studio_feature_tier_work` = 4

### Merchant action_key

- `standard_core_backing` = 10
- `complete_full_set_backing` = 16
- `merchant_tier_backing` = 30
- `one_paid_addon_pack` = 4
- `late_pledge_completion` = 8

### Merchant bonus_key

- `three_plus_addons_bonus` = 6
- `second_campaign_in_row` = 8
- `third_campaign_in_row` = 12
- `fourth_plus_campaign_in_row` = 15

### Wardens action_key

- `printed_model_photo` = 6
- `print_report_with_settings` = 8
- `detailed_feedback_message` = 6
- `structured_review_issues_fixes` = 10
- `beta_test_summary` = 12
- `completed_feedback_mission` = 8
- `poll_participation` = 1
- `useful_issue_report_confirmed` = 8

У Wardens пока нет стандартных `bonus_key`.

## Антиспам-лимиты

Перед начислением `/approve` проверяет лимиты:

- The Voice of Ashfall — максимум 2 approve-транзакции в день на участника.
- The Atelier of Ash — максимум 1 approve-транзакция в день на участника.
- The Chronicle Wardens — `poll_participation` ограничен 2 Ash Marks в календарную неделю на участника.
- The Merchant Covenant — дневного лимита пока нет.

Лимиты используют `created_at` из `transactions`. Ручные корректировки через `/adjust` под эти лимиты не попадают.

## Роли прогрессии

Создайте на сервере Discord роли с точными названиями.

Общие роли:

- `Ashbound`
- `Hearthmarked`
- `Waysworn`
- `Trusted of Ashfall`
- `Keeper of the Chronicle`
- `Inner Circle`

The Voice of Ashfall:

- `Street Crier`
- `Ash Caller`
- `Chapel Voice`
- `Church Herald`
- `High Proclaimer`

The Atelier of Ash:

- `Soot Sketcher`
- `Candle Painter`
- `Reliquary Artisan`
- `Cathedral Illuminator`
- `Master of the Atelier`

The Merchant Covenant:

- `Pack Trader`
- `Caravan Factor`
- `Guild Broker`
- `Benefactor of Ash`
- `High Quartermaster`

The Chronicle Wardens:

- `Ash Witness`
- `Road Scout`
- `Chronicle Scribe`
- `Cartographer of Ruin`
- `Archive Keeper`

Бот поддерживает только одну активную общую роль и одну активную роль в каждой ветке. Если роль не найдена или Discord не даёт её выдать, команда не падает и показывает ошибку в embed.

## Канал логов начислений

Чтобы логировать `/approve` и `/adjust`, укажите `REWARDS_LOG_CHANNEL_ID`:

```env
REWARDS_LOG_CHANNEL_ID=123456789012345678
```

Канал должен быть на сервере из `GUILD_ID` и быть доступен боту. Боту нужны права отправлять сообщения и embeds. Если переменная пустая, равна `0` или канал не найден, команды продолжают работать без логирования.

## Канал review-queue

Чтобы участники могли отправлять заявки через `/submit`, укажите `REVIEW_QUEUE_CHANNEL_ID`:

```env
REVIEW_QUEUE_CHANNEL_ID=123456789012345678
```

Канал должен быть на сервере из `GUILD_ID` и быть доступен боту. Боту нужны права отправлять сообщения и embeds.

Если переменная пустая, равна `0` или канал не найден, `/submit` отвечает приватным сообщением, что канал проверки не настроен.

## Настройки Discord-бота

В Discord Developer Portal:

- включите `Server Members Intent`;
- пригласите бота со scope `applications.commands`;
- добавьте scope `bot`, если бот должен быть участником сервера.

Для синхронизации ролей боту нужны:

- permission `Manage Roles`;
- самая высокая роль бота должна быть выше всех ролей прогрессии;
- доступ к каналам, где используются команды;
- доступ к reward-log и review-queue каналам, если они используются.

Для будущей функции reaction roles в `#choose-your-path` боту также понадобятся:

- `Manage Roles`;
- `Add Reactions`;
- `Read Message History`;
- `View Channels`.

Роль бота должна быть выше ролей, которые он будет выдавать.

## PATH_MESSAGE_ID для choose-your-path

`PATH_MESSAGE_ID` — это ID сообщения в канале `#choose-your-path`, под которым
участники будут ставить реакции.

Как скопировать Message ID:

1. Откройте Discord.
2. Перейдите в `User Settings`.
3. Откройте `Advanced`.
4. Включите `Developer Mode`.
5. Перейдите в канал `#choose-your-path`.
6. Нажмите правой кнопкой по нужному сообщению.
7. Выберите `Copy Message ID`.
8. Вставьте значение в `.env`:

```env
PATH_MESSAGE_ID=123456789012345678
```

Не хардкодьте этот ID в коде.

## Reaction roles

Reaction roles используются для канала `#choose-your-path`: участник ставит
реакцию под специальным сообщением, а бот выдаёт роль ветки. Если реакция
убрана, бот снимает роль.

Настройка:

1. Создайте канал `#choose-your-path`.
2. Отправьте в него сообщение для выбора пути.
3. Добавьте к сообщению реакции:
   - `📣`
   - `🎨`
   - `🪙`
   - `🛡️`
4. Включите Developer Mode в Discord:
   - `User Settings`
   - `Advanced`
   - `Developer Mode`
5. Нажмите правой кнопкой по сообщению выбора пути.
6. Нажмите `Copy Message ID`.
7. Вставьте ID в `.env`:

```env
PATH_MESSAGE_ID=123456789012345678
```

Создайте роли с точными названиями:

- `Voice of Ashfall`
- `Atelier of Ash`
- `Merchant Covenant`
- `Chronicle Wardens`

Роль бота должна быть выше этих ролей в списке ролей сервера.

Боту нужны permissions:

- `Manage Roles`
- `Add Reactions`
- `Read Message History`
- `View Channels`

Пример текста сообщения для `#choose-your-path`:

```text
Choose your path 🜂

React below to unlock a branch:

📣 — The Voice of Ashfall
🎨 — The Atelier of Ash
🪙 — The Merchant Covenant
🛡️ — The Chronicle Wardens

You can choose one path or several.
Remove your reaction to leave a branch.
```

### Troubleshooting reaction roles

Если роль не выдаётся:

- проверьте, что роль бота стоит выше ролей `Voice of Ashfall`, `Atelier of Ash`, `Merchant Covenant`, `Chronicle Wardens`;
- проверьте, что у бота есть permission `Manage Roles`.

Если реакция не срабатывает:

- проверьте, что `PATH_MESSAGE_ID` в `.env` совпадает именно с ID сообщения в `#choose-your-path`;
- после изменения `.env` перезапустите бота;
- убедитесь, что реакции ставятся под тем самым сообщением.

Если бот не видит участников:

- включите `Server Members Intent` в Discord Developer Portal;
- убедитесь, что в `bot.py` включён `intents.members = True`.

Если бот не может добавить реакцию:

- проверьте permission `Add Reactions`;
- проверьте `Read Message History`;
- проверьте `View Channels`;
- убедитесь, что бот видит канал `#choose-your-path`.

Если роли названы иначе:

- либо переименуйте роли на сервере;
- либо поменяйте `REACTION_ROLE_MAP` в `services/reaction_roles_service.py`.

## Обработка ошибок

Slash-команды обрабатывают типовые ошибки:

- нет прав;
- некорректные данные;
- ошибки SQLite;
- `discord.Forbidden`;
- `discord.HTTPException`.

Пользователь получает понятное ephemeral-сообщение. Ошибки выдачи ролей не валят команду, а отображаются в embed.

## Deployment

### Локальный запуск

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

### Переменные `.env`

```env
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_discord_server_id_here
REWARDS_LOG_CHANNEL_ID=0
REVIEW_QUEUE_CHANNEL_ID=0
PATH_MESSAGE_ID=0
```

Для production укажите реальные channel ID для `REWARDS_LOG_CHANNEL_ID` и
`REVIEW_QUEUE_CHANNEL_ID`, если используете эти функции. Для reaction roles
укажите реальный `PATH_MESSAGE_ID`, когда эта функция будет реализована.

### Запуск на VPS

```bash
git clone your-repository-url ashfall-bot
cd ashfall-bot
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

### Запуск в Docker

Подготовьте `.env`:

```bash
cp .env.example .env
```

Заполните как минимум:

```env
DISCORD_TOKEN=your_bot_token_here
GUILD_ID=your_discord_server_id_here
REWARDS_LOG_CHANNEL_ID=0
REVIEW_QUEUE_CHANNEL_ID=0
PATH_MESSAGE_ID=0
```

Соберите и запустите контейнер:

```bash
docker compose up -d --build
```

Посмотреть логи:

```bash
docker compose logs -f ashfall-bot
```

Остановить:

```bash
docker compose down
```

SQLite-база в Docker хранится в:

```text
./data/ashfall.db
```

`docker-compose.yml` передаёт в контейнер:

```env
ASHFALL_DB_PATH=/app/data/ashfall.db
```

Это нужно, чтобы база сохранялась между пересборками образа и перезапусками контейнера.

### Пример systemd service

```ini
[Unit]
Description=Ashfall Chronicles Discord Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/ashfall-bot
ExecStart=/opt/ashfall-bot/.venv/bin/python /opt/ashfall-bot/bot.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Установка и запуск:

```bash
sudo cp ashfall-bot.service /etc/systemd/system/ashfall-bot.service
sudo systemctl daemon-reload
sudo systemctl enable --now ashfall-bot
sudo systemctl status ashfall-bot
```

## Git и секреты

Не коммитьте:

- `.env`
- `ashfall.db`
- `data/`
- `.venv/`
- `__pycache__/`
- `*.pyc`

Эти пути добавлены в `.gitignore`.
