# Инструмент генерации ключей по протоколу Codex

В данном каталоге представлены скрипты для регистрации Codex OAuth и генерации токенов через чистый HTTP на базе DuckMail.

## Основные возможности

- Регистрация аккаунтов ChatGPT через чистый HTTP
- Создание почты и чтение кодов подтверждения через DuckMail API
- Получение `access_token`, `refresh_token`, `id_token`
- Генерация имен JSON-файлов токенов, совместимых с CLIProxyAPI v6
- Опциональная загрузка в интерфейс управления CPA

## Конфигурационный файл

В репозитории доступен только пример файла:

```bash
copy config.example.json config.json
```

Поля примера конфигурации:

```json
{
  "total_accounts": 10,
  "concurrent_workers": 2,
  "headless": false,
  "proxy": "[http://127.0.0.1:7897](http://127.0.0.1:7897)",
  "duckmail_api_base": "[https://api.duckmail.sbs](https://api.duckmail.sbs)",
  "duckmail_api_key": "",
  "oauth_issuer": "[https://auth.openai.com](https://auth.openai.com)",
  "oauth_client_id": "app_EMoamEEZ73f0CkXaXp7hrann",
  "oauth_redirect_uri": "http://localhost:1455/auth/callback",
  "upload_api_url": "http://localhost:8317/v0/management/auth-files",
  "upload_api_token": "",
  "accounts_file": "accounts.txt",
  "csv_file": "registered_accounts.csv",
  "ak_file": "ak.txt",
  "rk_file": "rk.txt",
  "token_json_dir": "codex_accounts_tokens"
}
```

## Использование

```bash
python protocol_keygen.py
```

## Выходные файлы

После запуска локально будут созданы:

- `accounts.txt`
- `registered_accounts.csv`
- `ak.txt`
- `rk.txt`
- `codex_accounts_tokens/` (или настроенный вами каталог для токенов)

Все эти файлы предназначены для локального использования и не должны попадать в репозиторий.

## Отличия от оригинального проекта

По сравнению с вышестоящим проектом, ключевым изменением в данном каталоге является переход на использование DuckMail для работы с почтой:

- Использование `POST /accounts` для создания временной почты
- Использование `POST /token` для получения Bearer токена DuckMail
- Использование `GET /messages` и `GET /messages/{id}` для циклического опроса писем с кодами подтверждения

## Инструкции по использованию с CPA

- Сгенерированные JSON-файлы адаптированы под формат именования CLIProxyAPI v6
- `refresh_token` сохраняется вместе с остальными данными для автоматического обновления access токена в CPA
- Если настроен `upload_api_url`, скрипт автоматически загрузит созданные файлы авторизации
```
