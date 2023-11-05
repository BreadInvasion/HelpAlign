from api.routes.locate import router as locate_router
from api.routes.message import router as message_router
from api.routes.patient import router as patient_router
from api.routes.provider import router as provider_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(locate_router)
app.include_router(message_router)
app.include_router(patient_router)
app.include_router(provider_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "localhost",
        "*",
    ],  # For development, you might want to restrict this later!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)