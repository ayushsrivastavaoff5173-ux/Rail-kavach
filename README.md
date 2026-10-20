# RailKavach

**Team:** Code Red

## Problem Summary

Railway tracks par haadse aur obstacles ek bada safety risk hain. RailKavach video feed ko real time mein analyze karke (YOLO based detection) khatre ki pehchaan karta hai aur turant alert bhejta hai.

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn, WebSockets, Ultralytics (YOLO), OpenCV
- **Frontend:** JavaScript

## Project Structure

```
rail-kavach/
  backend/     # Python API + detection code
  frontend/    # JavaScript UI
  README.md
  LICENSE
```

## How to Run

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm start
```

## Contributing

Dekhein [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT License](LICENSE)