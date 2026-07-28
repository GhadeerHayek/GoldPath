from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def send_hello():
    return {"message": "Hi there"}


@app.get("/health")
def health_service():
    return {"status": "ok"}

@app.get("/greet")
def greet_service():
    return {"greet": "Hello World"}
