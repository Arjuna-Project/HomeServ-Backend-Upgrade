import os
import json
import re
import requests
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.service import Service
from app.models.category import Category
from app.models.booking import Booking
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/chat", tags=["Chatbot"])

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


# Request schema
class ChatRequest(BaseModel):
    message: Optional[str] = ""
    image: Optional[str] = None
    user_id: Optional[int] = None


# Main route
@router.post("/")
def chat_with_bot(req: ChatRequest, current_user=Depends(get_current_user)):

    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="AI key missing")

    if req.image:
        return handle_image(req)

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    return handle_text(req.message, current_user.id)


# Detect user intent
def detect_intent(message: str):
    msg = message.lower()

    if any(word in msg for word in ["booking", "my bookings", "my orders"]):
        return "booking"

    if any(word in msg for word in ["status", "track"]):
        return "booking_status"

    return "general"


# Extract category from message dynamically
def extract_category_from_message(message: str):
    db: Session = SessionLocal()

    try:
        msg = message.lower()
        categories = db.query(Category).all()

        for category in categories:
            if category.name.lower() in msg:
                return category.name

        return None

    finally:
        db.close()


# Search services from database
def search_services(message: str):
    db: Session = SessionLocal()

    try:
        message = message.lower()

        # Match category
        categories = db.query(Category).all()
        for category in categories:
            if category.name.lower() in message:
                services = (
                    db.query(Service)
                    .filter(Service.category_id == category.id)
                    .all()
                )

                if services:
                    service_list = "\n".join(
                        [f"• {s.name} – ₹{s.price}" for s in services]
                    )

                    return (
                        f"Here are available {category.name} services:\n\n"
                        f"{service_list}\n\n"
                        "Reply with the service name to book."
                    )

        # Match individual service
        services = db.query(Service).all()
        for service in services:
            if service.name.lower() in message:
                return (
                    f"{service.name} – ₹{service.price}\n"
                    f"{service.description}\n\n"
                    "Would you like to book this service?"
                )

        return None

    finally:
        db.close()


# Get user bookings with optional category filter
def tool_get_user_bookings(user_id: int, message: str = ""):
    db: Session = SessionLocal()

    try:
        bookings = db.query(Booking).filter(Booking.user_id == user_id).all()

        if not bookings:
            return "You have no bookings."

        category_filter = extract_category_from_message(message)

        filtered = []

        for b in bookings:
            if not b.service:
                continue

            service_name = b.service.name.lower()
            category_name = (
                b.service.category.name.lower()
                if b.service.category else ""
            )

            # If category mentioned, filter
            if category_filter:
                if category_filter.lower() in category_name:
                    filtered.append(b)
            else:
                filtered.append(b)

        if not filtered:
            return "No bookings found for this category."

        return "\n\n".join(
            [
                f"Booking ID: {b.id}\n"
                f"Service: {b.service.name}\n"
                f"Date: {b.date}\n"
                f"Time: {b.time}\n"
                f"Status: {b.status}"
                for b in filtered
            ]
        )

    finally:
        db.close()


# Get booking status
def tool_get_booking_status(user_id: int, booking_id: int):
    db: Session = SessionLocal()

    try:
        booking = (
            db.query(Booking)
            .filter(Booking.id == booking_id, Booking.user_id == user_id)
            .first()
        )

        if not booking:
            return "Booking not found."

        return f"Booking ID {booking.id} status: {booking.status}"

    finally:
        db.close()


# Handle text messages
def handle_text(user_message: str, user_id: Optional[int]):

    intent = detect_intent(user_message)

    # Handle booking requests
    if intent == "booking":
        return {
            "type": "text",
            "reply": tool_get_user_bookings(user_id, user_message)
        }

    # Handle booking status
    if intent == "booking_status":
        return {
            "type": "text",
            "reply": "Please provide booking ID to check status."
        }

    # Service search
    db_reply = search_services(user_message)
    if db_reply:
        return {"type": "text", "reply": db_reply}

    # AI fallback
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openai/gpt-4o-mini",
            "temperature": 0.3,
            "max_tokens": 300,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are HomeServ assistant. "
                        "Help users with services and bookings."
                    ),
                },
                {"role": "user", "content": user_message},
            ],
        },
        timeout=30,
    )

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=response.text)

    data = response.json()
    ai_reply = data.get("choices", [{}])[0].get("message", {}).get("content", "")

    return {"type": "text", "reply": ai_reply or "How can I assist you?"}


# Handle image input
def handle_image(req: ChatRequest):

    prompt = """
Analyze the image and decide if it is DIY safe.

Respond ONLY in JSON:
{
  "issue": "...",
  "service": "...",
  "diy_safe": true/false,
  "requirements": [],
  "steps": []
}
"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openai/gpt-4o-mini",
            "max_tokens": 500,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": f"data:image/jpeg;base64,{req.image}",
                        },
                    ],
                }
            ],
        },
        timeout=30,
    )

    if response.status_code != 200:
        return {"type": "error", "reply": "AI service unavailable."}

    ai_reply = response.json()["choices"][0]["message"]["content"]

    try:
        ai_data = extract_json(ai_reply)
    except Exception:
        return {"type": "error", "reply": "I couldn't analyze the image properly."}

    if ai_data.get("diy_safe") is True:
        requirements = "\n".join([f"- {r}" for r in ai_data.get("requirements", [])])
        steps = "\n".join(
            [f"{i+1}. {s}" for i, s in enumerate(ai_data.get("steps", []))]
        )

        return {
            "type": "diy",
            "reply": (
                f"Issue: {ai_data.get('issue')}\n\n"
                f"Requirements:\n{requirements}\n\n"
                f"Steps:\n{steps}"
            ),
        }

    return {
        "type": "risky",
        "reply": (
            f"Issue: {ai_data.get('issue')}\n\n"
            "This is risky. Please book a professional."
        ),
    }


# Extract JSON from AI response
def extract_json(text: str):
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON found")
    return json.loads(match.group())