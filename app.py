import os

from d4d_app.main import app


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", "8000"))
    uvicorn.run("d4d_app.main:app", host=host, port=port, reload=False)
