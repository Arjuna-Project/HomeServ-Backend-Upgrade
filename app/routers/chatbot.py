import os
import json
import re
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.service import Service
from app.models.category import Category
from app.models.booking import Booking

router = APIRouter(prefix="/chat", tags=["Chatbot"])

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


class ChatRequest(BaseModel):
    message: Optional[str] = ""
    image: Optional[str] = None
    user_id: Optional[int] = None


from fastapi import Depends
from app.utils.dependencies import get_current_user


@router.post("/")
def chat_with_bot(req: ChatRequest, current_user=Depends(get_current_user)):

    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="AI key missing")

    if req.image:
        return handle_image(req)

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    return handle_text(req.message, current_user.id)


def search_services(message: str):

    db: Session = SessionLocal()
    try:
        message = message.lower()

        # Category match
        categories = db.query(Category).all()
        for category in categories:
            if category.name.lower() in message:
                services = (
                    db.query(Service).filter(Service.category_id == category.id).all()
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

        # Service match
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


def tool_get_user_bookings(user_id: int):

    db: Session = SessionLocal()
    try:
        bookings = db.query(Booking).filter(Booking.user_id == user_id).all()
        print("CHATBOT USER ID:", user_id)
        if not bookings:
            return "You have no bookings."

        return "\n\n".join(
            [
                f"Booking ID: {b.id}\n"
                f"Date: {b.date}\n"
                f"Time: {b.time}\n"
                f"Status: {b.status}"
                for b in bookings
            ]
        )

    finally:
        db.close()


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


def handle_text(user_message: str, user_id: Optional[int]):

    # 1️⃣ DB search first
    db_reply = search_services(user_message)
    if db_reply:
        return {"type": "text", "reply": db_reply}

    # 2️⃣ AI with MCP tools
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are HomeServ assistant.\n"
                        "You can call tools to fetch booking data.\n"
                        "Use tools when user asks about bookings."
                    ),
                },
                {"role": "user", "content": user_message},
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_user_bookings",
                        "description": "Get all bookings for logged in user",
                        "parameters": {"type": "object", "properties": {}},
                    },
                },
                {
                    "type": "function",
                    "function": {
                        "name": "get_booking_status",
                        "description": "Get booking status by ID",
                        "parameters": {
                            "type": "object",
                            "properties": {"booking_id": {"type": "integer"}},
                            "required": ["booking_id"],
                        },
                    },
                },
            ],
        },
        timeout=30,
    )

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=response.text)

    data = response.json()
    choice = data.get("choices", [{}])[0]
    message = choice.get("message", {})

    # 3️⃣ Check if tool call happened
    tool_calls = message.get("tool_calls")

    if tool_calls:
        tool_call = tool_calls[0]
        function_name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"].get("arguments", "{}"))

        if function_name == "get_user_bookings":
            result = tool_get_user_bookings(user_id)

        elif function_name == "get_booking_status":
            result = tool_get_booking_status(user_id, arguments.get("booking_id"))

        else:
            result = "Tool not recognized."

        return {"type": "text", "reply": result}

    # 4️⃣ Normal AI reply
    ai_reply = message.get("content", "")

    return {"type": "text", "reply": ai_reply or "How can I assist you?"}


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
        raise HTTPException(status_code=500, detail=response.text)

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
                f"Issue identified: {ai_data.get('issue')}\n\n"
                f"Requirements:\n{requirements}\n\n"
                f"Steps:\n{steps}"
            ),
        }

    return {
        "type": "risky",
        "reply": (
            f"Issue identified: {ai_data.get('issue')}\n\n"
            "This issue is risky. Please book a professional."
        ),
    }


def extract_json(text: str):
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON found")
    return json.loads(match.group())
