from app.app import app

# Entry point for `uv run uvicorn main:app --reload --port 8001`
# The actual FastAPI app and routes live in app/app.py

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)