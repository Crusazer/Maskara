# Maskara 🎭

**Анонимизируй текст — оставайся в тени.**

Maskara — это лёгкий и гибкий сервис для анонимизации персональных данных в тексте. Отправь фрагмент текста, укажи, какие сущности скрыть — и получи чистую версию без следов личной информации. Поддерживает русский язык и работает даже на CPU.

> ⚠️ **Важно**: Это open-source проект, распространяемый «как есть». Автор не несёт ответственности за последствия использования. Применяйте на свой страх и риск.

---

## 🔒 Возможности

- Анонимизация **любых пользовательских сущностей** (указываются через `labels`)
- Два режима обработки:
  - **Маскирование**: замена на теги вида `<NAME>`, `<PHONE>`, и т.д.
  - **Фейковые данные**: подстановка реалистичных, но вымышленных значений (через `faker`)
- Поддержка **русского языка**
- Простой REST API
- Готов к запуску через **Docker**, **uv** или напрямую

---

## 🚀 Быстрый старт

### Требования
- Python 3.12+
- (Опционально) Docker

### Локальный запуск

1. Клонируйте репозиторий:
``` bash
git clone https://github.com/your-username/maskara.git
cd maskara
```

2. Установите зависимости (рекомендуется через [`uv`](https://docs.astral.sh/uv/)):
``` bash
uv sync
```

3. Настройте `.env` (пример в `.env.example`):
``` env
LOG_LEVEL=info
HOST=0.0.0.0
PORT=8000
```

4. Запустите сервер:
``` bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### Через Docker

``` bash
docker build -t maskara .
docker run -p 8000:8000 --env-file .env maskara
```

---

## 📡 API

### `POST /anonymize`

Анонимизирует переданный текст.

**Запрос**:
``` json
{
  "text": "Привет, меня зовут Максим",
  "labels": ["PER"],
  "use_fake": false
}
```

**Ответ**:
``` json
{
  "anonymized_text": "Привет, меня зовут <NAME>",
  "mapping": {
    "<NAME>": "Максим"
  }
}
```

> 💡 `mapping` позволяет при необходимости восстановить оригинальные данные (например, для внутренней обработки).

Параметры:
- `text` (str) — исходный текст
- `labels` (list[str]) — список меток сущностей для анонимизации (например: `["PER", "LOC", "ORG"]`)
- `use_fake` (bool) — если `true`, вместо масок подставляются фейковые данные

---

## 🧪 Пример

**Вход**:
> "Привет, меня зовут Максим, я живу в Москве, мой телефон +7 (999) 123-45-67."

**Запрос**:
``` json
{
  "text": "Привет, меня зовут Максим, я живу в Москве, мой телефон +7 (999) 123-45-67.",
  "labels": ["PER", "LOC", "PHONE"],
  "use_fake": false
}
```

**Выход**:
``` json
{
  "anonymized_text": "Привет, меня зовут <NAME>, я живу в <LOC>, мой телефон <PHONE>.",
  "mapping": {
    "<NAME>": "Максим",
    "<LOC>": "Москве",
    "<PHONE>": "+7 (999) 123-45-67"
  }
}
```

---

## 🧠 Технические детали

- Работает на **CPU** (GPU-поддержка планируется)
- Использует современные NLP-методы для извлечения сущностей
- Лёгкий и без излишеств — только то, что нужно для анонимизации

---

## 👥 Для кого это?

- Юристы и аналитики, обрабатывающие конфиденциальные документы  
- Разработчики, интегрирующие анонимизацию в свои сервисы  
- Исследователи, работающие с текстами, содержащими PII  
- Любой, кому нужно **быстро и безопасно** убрать личные данные из текста

---

## 📄 Лицензия

Распространяется под лицензией **MIT**.

```
MIT License

Copyright (c) 2025 Maskara

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

> 🛑 **Предупреждение**: Это ПО предоставляется «как есть». Автор не гарантирует полную защиту данных и не несёт ответственности за использование в production-средах.

---

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue)](https://python.org)
[![Runs on CPU](https://img.shields.io/badge/Device-CPU-orange)](https://your-repo-url)

---

Сделано с ❤️ и заботой о приватности.  
**Maskara** — потому что не всё, что написано, должно быть узнаваемо.