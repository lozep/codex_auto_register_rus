
# codex_auto_register

Набор инструментов для автоматической регистрации ChatGPT / Codex и генерации OAuth токенов на базе DuckMail.

## Благодарности

Этот проект основан на базе оригинального репозитория https://github.com/adminlove520/chatgpt_register.

Основные отличия текущего репозитория:

- Сервис почты для регистрации codex заменен с оригинального решения на DuckMail API.
- Сохранен и расширен процесс OAuth по протоколу Codex.
- Вывод файлов авторизации Codex, распознаваемых CLIProxyAPI v6.

## Состав проекта

- `chatgpt_register.py`: Скрипт регистрации через DuckMail в корневом каталоге.
- `codex/protocol_keygen.py`: Скрипт регистрации OAuth и генерации токенов Codex через чистый HTTP.
- `duckmaildoc.md`: Справочная документация DuckMail API.
- [management.html](https://github.com/router-for-me/Cli-Proxy-API-Management-Center/releases) (автоматическое обновление).

## Зависимости

Скрипт в корневом каталоге:

```bash
pip install curl_cffi
```

Скрипт Codex:

```bash
pip install requests urllib3
```

## Настройка

В репозитории представлены только примеры конфигурации, реальные данные не публикуются.

Перед использованием скопируйте файлы:

```bash
copy config.example.json config.json
copy codex\config.example.json codex\config.json
```

Затем впишите свои параметры DuckMail, прокси и CPA.

## Скрипт в корневом каталоге

Запуск:

```bash
python chatgpt_register.py
```

Пример конфигурации находится в `config.example.json`.

Основные параметры:

| Параметр          | Описание                         |
| ----------------- | -------------------------------- |
| total_accounts    | Количество аккаунтов для регистрации |
| duckmail_api_base | Адрес DuckMail API               |
| duckmail_bearer   | Токен Bearer для DuckMail        |
| proxy             | HTTP/HTTPS прокси                |
| output_file       | Файл с результатами регистрации  |
| enable_oauth      | Выполнять ли OAuth               |
| oauth_required    | Обязателен ли успешный OAuth     |
| upload_api_url    | Опционально: URL для загрузки в CPA |
| upload_api_token  | Опционально: Токен API управления CPA |

## Скрипт протокола Codex

Запуск:

```bash
python codex\protocol_keygen.py
```

Пример конфигурации находится в `codex/config.example.json`.

Этот скрипт:

- Создает временную почту через DuckMail.
- Завершает процесс регистрации ChatGPT.
- Выполняет вход через Codex OAuth для получения токенов.
- Генерирует JSON-файлы токенов с именами, совместимыми с CLIProxyAPI v6.
- По желанию загружает данные в интерфейс управления CPA.

## Описание вывода

В процессе работы обычно создаются следующие локальные файлы (они добавлены в `.gitignore` и не попадут в репозиторий):

- `config.json`
- `codex/config.json`
- `registered_accounts.txt`
- `codex/accounts.txt`
- `codex/ak.txt`
- `codex/rk.txt`
- `codex/registered_accounts.csv`
- `codex/codex_tokens/`
- `codex/codex_accounts_tokens/`

## Структура репозитория

```text
chatgpt_register/
├── chatgpt_register.py
├── config.example.json
├── duckmaildoc.md
├── README.md
└── codex/
    ├── config.example.json
    ├── protocol_keygen.py
    └── README.md
```

## Примечания

- Необходимы рабочие прокси, иначе регистрация, OAuth и автообновление CPA завершатся ошибкой.
- `config.json` и `codex/config.json` предназначены только для локального использования и не должны отправляться в репозиторий.
- Если вы используете CLIProxyAPI, рекомендуется сохранять `refresh_token` и JSON-файлы токенов полностью.
```
