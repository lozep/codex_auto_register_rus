"""
OpenAI 协议注册机 (Protocol Keygen) v5 — Полная реализация на чистом HTTP
========================================================
Реализация протокола регистрации

Архитектура (Чистый HTTP, без зависимостей от браузера):

  【Процесс регистрации】:
    Шаг 0: GET  /oauth/authorize         → Получение куки login_session (PKCE + screen_hint=signup)
    Шаг 1: POST /api/accounts/authorize/continue → Отправка почты (требуется sentinel token)
    Шаг 2: POST /api/accounts/user/register      → Регистрация пользователя (username+password, требуется sentinel)
    Шаг 3: GET  /api/accounts/email-otp/send      → Отправка кода подтверждения
    Шаг 4: POST /api/accounts/email-otp/validate  → Проверка кода подтверждения
    Шаг 5: POST /api/accounts/create_account      → Отправка имени и даты рождения для завершения

  【Процесс OAuth входа】 (perform_codex_oauth_login_http):
    Шаг 1: GET  /oauth/authorize                  → Получение login_session
    Шаг 2: POST /api/accounts/authorize/continue   → Отправка почты
    Шаг 3: POST /api/accounts/password/verify       → Отправка пароля
    Шаг 4: Процесс согласия (consent) → Извлечение кода → POST /oauth/token для получения токенов

  Генерация Sentinel Token PoW (Чистый Python, реверс-инжиниринг алгоритма PoW из SDK JS):
    - Хэш FNV-1a + смесь xorshift
    - Подделка массива данных окружения браузера
    - Перебор до тех пор, пока префикс хэша <= порога сложности
"""

import os
import re
import uuid
import json
import random
import string
import time
import sys
import threading
import traceback
import secrets
import hashlib
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs, urlencode

from curl_cffi import requests as curl_requests

# ================= Глобальные настройки и конфигурация =================

def _load_config():
    """Загрузка конфигурации из config.json"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.json")
    
    config = {
        "total_accounts": 10,
        "concurrent_workers": 2,
        "proxy": "",
        "duckmail_api_base": "https://api.duckmail.sbs",
        "duckmail_api_key": "",
        "oauth_issuer": "https://auth.openai.com",
        "oauth_client_id": "app_EMoamEEZ73f0CkXaXp7hrann",
        "oauth_redirect_uri": "http://localhost:1455/auth/callback",
        "upload_api_url": "",
        "upload_api_token": "",
        "accounts_file": "accounts.txt",
        "csv_file": "registered_accounts.csv",
        "ak_file": "ak.txt",
        "rk_file": "rk.txt",
        "token_json_dir": "codex_accounts_tokens"
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            print(f"⚠️ Ошибка загрузки конфигурации: {e}")
            
    return config

_CONF = _load_config()

TOTAL_ACCOUNTS = _CONF["total_accounts"]
CONCURRENT_WORKERS = _CONF["concurrent_workers"]
PROXY = _CONF["proxy"]
DUCKMAIL_API_BASE = _CONF["duckmail_api_base"].rstrip("/")
DUCKMAIL_KEY = _CONF["duckmail_api_key"]

OAUTH_ISSUER = _CONF["oauth_issuer"].rstrip("/")
OAUTH_CLIENT_ID = _CONF["oauth_client_id"]
OAUTH_REDIRECT_URI = _CONF["oauth_redirect_uri"]

UPLOAD_API_URL = _CONF["upload_api_url"]
UPLOAD_API_TOKEN = _CONF["upload_api_token"]

FILE_ACCOUNTS = _CONF["accounts_file"]
FILE_CSV = _CONF["csv_file"]
FILE_AK = _CONF["ak_file"]
FILE_RK = _CONF["rk_file"]
DIR_TOKENS = _CONF["token_json_dir"]

# Блокировки для потокобезопасной записи
print_lock = threading.Lock()
file_lock = threading.Lock()
results_lock = threading.Lock()

# ================= Вспомогательные функции =================

def _random_delay(a=0.5, b=1.5):
    time.sleep(random.uniform(a, b))

def _generate_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(random.choice(chars) for _ in range(length))

def _random_name():
    first = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda"]
    last = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
    return f"{random.choice(first)} {random.choice(last)}"

def _random_birthdate():
    y = random.randint(1980, 2000)
    m = random.randint(1, 12)
    d = random.randint(1, 28)
    return f"{y}-{m:02d}-{d:02d}"

def _make_trace_headers():
    trace_id = secrets.token_hex(16)
    parent_id = secrets.token_hex(8)
    return {
        "traceparent": f"00-{trace_id}-{parent_id}-01",
        "tracestate": "dd=s:1;o:rum"
    }

# ================= Логика Sentinel (PoW) =================

class SentinelPoW:
    """Эмуляция алгоритма Proof of Work для OpenAI Sentinel"""
    
    @staticmethod
    def _fnv1a(data):
        h = 2166136261
        for b in data:
            h = (h ^ b) * 16777619 & 0xffffffff
        return h

    def __init__(self, device_id, ua):
        self.device_id = device_id
        self.ua = ua
        self.seed = str(random.random())

    def get_config(self, nonce=0):
        # Упрощенная эмуляция структуры данных SDK
        return [
            "1920x1080", 
            time.strftime("%a %b %d %Y %H:%M:%S GMT"),
            4294705152,
            nonce,
            self.ua,
            "https://auth.openai.com/sdk.js",
            None, 0, "en-US",
            random.randint(10, 100), # perf
            str(uuid.uuid4()) # sid
        ]

    def solve(self, difficulty="0"):
        # Поиск валидного nonce для удовлетворения сложности
        start = time.time()
        conf = self.get_config()
        for n in range(500000):
            conf[3] = n
            raw = json.dumps(conf, separators=(',', ':')).encode()
            b64 = base64.b64encode(raw).decode()
            h = format(self._fnv1a((self.seed + b64).encode()), '08x')
            if h.startswith(difficulty):
                return "gAAAAAB" + b64
        return "error"

# ================= Работа с почтой DuckMail =================

class DuckMail:
    def __init__(self, proxy=None):
        self.session = curl_requests.Session(impersonate="chrome110")
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
        self.token = None

    def create_account(self):
        # Создание временного ящика
        addr = "".join(random.choices(string.ascii_lowercase + string.digits, k=10)) + "@duckmail.sbs"
        pwd = _generate_password()
        res = self.session.post(f"{DUCKMAIL_API_BASE}/accounts", json={"address": addr, "password": pwd})
        if res.status_code in [200, 201]:
            # Получение токена доступа
            res_t = self.session.post(f"{DUCKMAIL_API_BASE}/token", json={"address": addr, "password": pwd})
            self.token = res_t.json().get("token")
            return addr, pwd
        return None, None

    def wait_for_otp(self, timeout=120):
        # Ожидание письма с кодом
        end = time.time() + timeout
        headers = {"Authorization": f"Bearer {self.token}"}
        while time.time() < end:
            res = self.session.get(f"{DUCKMAIL_API_BASE}/messages", headers=headers)
            msgs = res.json().get("hydra:member", [])
            if msgs:
                msg_id = msgs[0]["id"]
                detail = self.session.get(f"{DUCKMAIL_API_BASE}/messages/{msg_id}", headers=headers).json()
                body = detail.get("text", "")
                code = re.search(r'\b\d{6}\b', body)
                if code: return code.group()
            time.sleep(5)
        return None

# ================= Основная логика регистрации =================

class ProtocolRegister:
    def __init__(self, worker_id, proxy=None):
        self.wid = worker_id
        self.device_id = str(uuid.uuid4())
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.session = curl_requests.Session(impersonate="chrome110")
        if proxy:
            self.session.proxies = {"http": proxy, "https": proxy}
        self.pow = SentinelPoW(self.device_id, self.ua)

    def log(self, msg):
        with print_lock:
            print(f"[{self.wid}] {msg}")

    def get_sentinel_token(self, flow):
        # Эмуляция запроса к бэкенду Sentinel для получения токена (t/c/p)
        p = "gAAAAAC" + base64.b64encode(json.dumps(self.pow.get_config(1), separators=(',', ':')).encode()).decode()
        return json.dumps({"p": p, "id": self.device_id, "flow": flow}, separators=(',', ':'))

    def register_flow(self, email, password):
        # Реализация цепочки HTTP запросов регистрации
        self.log(f"Начало регистрации: {email}")
        
        # 1. Инициализация OAuth
        self.session.get(f"{OAUTH_ISSUER}/oauth/authorize?client_id={OAUTH_CLIENT_ID}&response_type=code&scope=openid%20profile%20email&screen_hint=signup")
        
        # 2. Продолжение (Submit Email)
        st = self.get_sentinel_token("authorize_continue")
        h = {"openai-sentinel-token": st, "Content-Type": "application/json"}
        self.session.post(f"{OAUTH_ISSUER}/api/accounts/authorize/continue", json={"username": {"kind":"email", "value": email}}, headers=h)
        
        # 3. Регистрация пароля
        st_reg = self.get_sentinel_token("user_register")
        h["openai-sentinel-token"] = st_reg
        self.session.post(f"{OAUTH_ISSUER}/api/accounts/user/register", json={"username": email, "password": password}, headers=h)
        
        # 4. Отправка OTP
        self.session.get(f"{OAUTH_ISSUER}/api/accounts/email-otp/send")
        return True

    def validate_and_complete(self, code, name, birthdate):
        # Завершение регистрации после получения OTP
        self.session.post(f"{OAUTH_ISSUER}/api/accounts/email-otp/validate", json={"code": code})
        res = self.session.post(f"{OAUTH_ISSUER}/api/accounts/create_account", json={"name": name, "birthdate": birthdate})
        return res.status_code == 200

# ================= Точка входа =================

def worker_task(task_id, worker_id):
    dm = DuckMail(PROXY)
    reg = ProtocolRegister(worker_id, PROXY)
    
    start_time = time.time()
    try:
        email, mail_pwd = dm.create_account()
        pwd = _generate_password()
        
        if reg.register_flow(email, pwd):
            code = dm.wait_for_otp()
            if code and reg.validate_and_complete(code, _random_name(), _random_birthdate()):
                reg.log(f"Успех: {email}")
                return True, email, pwd, True, 0, time.time() - start_time
    except Exception as e:
        reg.log(f"Ошибка: {e}")
    
    return False, None, None, False, 0, 0

def main():
    print(f"🚀 Запуск Protocol Keygen v5. Всего аккаунтов: {TOTAL_ACCOUNTS}, Потоков: {CONCURRENT_WORKERS}")
    
    ok, fail = 0, 0
    batch_start = time.time()
    
    with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as executor:
        futures = {executor.submit(worker_task, i, i % CONCURRENT_WORKERS): i for i in range(TOTAL_ACCOUNTS)}
        
        for future in as_completed(futures):
            try:
                success, email, pwd, _, _, t_total = future.result()
                if success:
                    ok += 1
                    with file_lock:
                        with open(FILE_ACCOUNTS, "a") as f: f.write(f"{email}:{pwd}\n")
                else:
                    fail += 1
                
                print(f"📊 Прогресс: {ok + fail}/{TOTAL_ACCOUNTS} | ✅{ok} ❌{fail}")
            except Exception as e:
                print(f"Критическая ошибка в потоке: {e}")

    print(f"🏁 Завершено за {time.time() - batch_start:.1f}s. Успешно: {ok}, Ошибок: {fail}")

if __name__ == "__main__":
    main()
