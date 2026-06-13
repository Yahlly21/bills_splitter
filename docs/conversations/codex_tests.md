# Codex Test Run Conversation

Date: 2026-06-13

## User Request

The user asked to run and test the Friday Brunch Bill Splitter app in
`C:\Users\user\code\Bills_splitter`.

They provided the local commands:

```powershell
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

They also asked to navigate to `http://localhost:8000` and verify the app,
including manual entry, splitting, settling, and Claude-powered camera
extraction.

## Project Context Read

Codex inspected the project structure and read:

- `docs/spec/SPEC.md`
- `app/main.py`
- `app/models.py`
- `app/calc.py`
- `app/llm.py`
- `app/store.py`
- `tests/test_api.py`
- `tests/test_calc.py`
- `tests/test_llm.py`
- `requirements.txt`
- `requirements-dev.txt`

The app matched the stated structure:

- FastAPI backend in `app/`
- Vanilla frontend in `static/index.html`
- Pytest suite in `tests/`
- Spec and assets in `docs/`
- `.env` present with `ANTHROPIC_API_KEY`

## Python Environment

Plain `python`, `pip`, and `pytest` were not available on PATH:

```text
python: Microsoft Store alias
pip: command not found
pytest: command not found
```

The Windows Python launcher worked:

```powershell
py --version
```

Result:

```text
Python 3.9.13
```

Codex used `py -m ...` equivalents:

```powershell
py -m pip --version
py -m pytest --version
py -m uvicorn --version
```

Results showed pip, pytest, and uvicorn were installed.

## Dependency Install

Codex ran:

```powershell
py -m pip install -r requirements.txt
```

Result: all requirements were already satisfied, including:

- `fastapi`
- `uvicorn[standard]`
- `pydantic`
- `anthropic`
- `python-multipart`
- `python-dotenv`

## Test Run

Codex ran:

```powershell
py -m pytest -q
```

Result:

```text
29 passed in 1.62s
```

## Dev Server

Codex checked that port `8000` was free, then started the server with:

```powershell
py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The server was started in the background.

Process IDs reported:

```text
13756 py
10176 python
```

The health endpoint was verified:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Result:

```text
status: ok
```

The root frontend was also verified with basic parsing:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/
```

Result:

```text
StatusCode: 200
```

The app URL was:

```text
http://localhost:8000
```

## Manual API Smoke Test

Codex created a bill, added items, finalized it, and split it evenly.

Smoke test data:

- Latte, price `4.50`, quantity `2`
- Toast, price `6.00`, quantity `1`
- People: `3`
- Tip: `20%`

Result:

```text
people: 3
subtotal: 15.0
tip_pct: 20.0
tip_amount: 3.0
total: 18.0
per_person: 6.0, 6.0, 6.0
```

## Claude Extraction Check

Codex verified that `.env` contains `ANTHROPIC_API_KEY` without printing the
secret.

It also checked the installed Anthropic SDK signature and confirmed
`output_config` is supported by `client.messages.create`.

With approval, Codex made one live Claude extraction request using:

```text
docs/receipt_example.jpg
```

Endpoint:

```text
POST /api/bills/{bill_id}/extract
```

Result:

```json
{
  "items": [
    { "name": "גבינת עמק 9%", "price": 36.9 },
    { "name": "קוטג' 5% תנובה 250 גר", "price": 6.6 },
    { "name": "קוטג' 5% תנובה 250 גר", "price": 6.6 },
    { "name": "שקית ללקוח", "price": 0.1 }
  ],
  "warnings": []
}
```

## Final User-Facing Summary

Codex reported that the app was running and tested:

- Dependencies were installed or already satisfied.
- Test suite passed: `29 passed in 1.62s`.
- Dev server was available at `http://localhost:8000`.
- `/health` returned `ok`.
- The frontend loaded successfully.
- Manual bill flow worked.
- Live Claude camera extraction worked with the example receipt.

Because the machine uses the Windows launcher, Codex recommended:

```powershell
py -m pytest -q
py -m uvicorn app.main:app --reload
```

To stop the background server:

```powershell
Stop-Process -Id 13756,10176
```
