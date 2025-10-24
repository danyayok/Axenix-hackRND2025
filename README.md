# Axenix Conf Backend (FastAPI)

## Быстрый старт (Windows, venv + pip)

```powershell
# 1) Создать и активировать окружение
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2) Поставить зависимости
pip install -U pip
pip install -r requirements.txt

# 3) Запуск dev-сервера (дефолт: host=0.0.0.0, port=8090)
uvicorn app.main:app --reload
# Открыть: http://localhost:8090/health
