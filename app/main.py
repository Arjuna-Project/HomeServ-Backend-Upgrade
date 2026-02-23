from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import engine, Base

# Import models so tables register
from app.models import (
    user,
    category,
    service,
    booking,
    review,
    complaint,
    area
)

# Import ALL routers
from app.routers import (
    auth,
    categories,
    services,
    bookings,
    reviews,
    complaints,
    admin,
    users,
    chatbot
)

app = FastAPI(
    title="HomeServ API",
    description="Premium Home Services Marketplace Backend",
    version="1.0.0",
)

origins = [
    "http://127.0.0.1:5501",
    "http://localhost:5501",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:5502",
    "http://localhost:5502",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(services.router)
app.include_router(bookings.router)
app.include_router(reviews.router)
app.include_router(complaints.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(chatbot.router)


@app.get("/")
def root():
    return {"message": "HomeServ Backend Running 🚀"}


@app.get("/health")
def health():
    return {"status": "ok"}
