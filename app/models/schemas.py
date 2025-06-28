from pydantic import BaseModel, Field
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from enum import Enum
from langchain.schema import BaseMessage
class EventStatus(str, Enum):
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"

class BookingIntent(str, Enum):
    SCHEDULE = "schedule"
    RESCHEDULE = "reschedule"
    CANCEL = "cancel"
    CHECK_AVAILABILITY = "check_availability"
    LIST_EVENTS = "list_events"

class ConversationState(str, Enum):
    INITIAL = "initial"
    COLLECTING_INFO = "collecting_info"
    CHECKING_AVAILABILITY = "checking_availability"
    CONFIRMING_BOOKING = "confirming_booking"
    COMPLETED = "completed"
    ERROR = "error"

class UserMessage(BaseModel):
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str

class AgentResponse(BaseModel):
    message: str
    state: ConversationState
    intent: Optional[BookingIntent] = None
    suggested_slots: Optional[List[Dict[str, Any]]] = None
    booking_confirmation: Optional[Dict[str, Any]] = None
    requires_confirmation: bool = False
    next_action: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class BookingRequest(BaseModel):
    title: str = "Meeting"
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    attendees: List[str] = []
    location: Optional[str] = None
    status: EventStatus = EventStatus.CONFIRMED

class CalendarEvent(BaseModel):
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    attendees: List[str] = []
    location: Optional[str] = None
    status: EventStatus = EventStatus.CONFIRMED

# class AvailabilitySlot(BaseModel):
#     start: datetime
#     end: datetime
#     duration_minutes: int = 60
class AvailabilitySlot(BaseModel):
    """Represents an available time slot in the calendar"""
    start: datetime
    end: datetime
    duration_minutes: int = Field(
        default=60,
        description="Duration of the slot in minutes",
        gt=0,
        le=1440  # Max 24 hours
    )
    is_available: bool = Field(
        default=True,
        description="Whether the slot is currently available"
    )

class BookingResponse(BaseModel):
    message: str
    intent: Optional[BookingIntent] = None
    proposed_event: Optional[CalendarEvent] = None
    available_slots: List[AvailabilitySlot] = []
    requires_confirmation: bool = False
    next_action: Optional[str] = None

class AgentState(BaseModel):
    messages: List[Dict[str, str]] = []
    current_intent: Optional[BookingIntent] = None
    proposed_event: Optional[CalendarEvent] = None
    user_confirmations: Dict[str, bool] = {}
    context: Dict[str, Any] = {}

class ConversationContext(BaseModel):
    session_id: str
    state: ConversationState = ConversationState.INITIAL
    user_intent: Optional[BookingIntent] = None
    preferred_date: Optional[date] = None
    preferred_time: Optional[time] = None
    duration: int = 60  # minutes
    meeting_title: str = "Meeting"
    meeting_description: Optional[str] = None
    suggested_slots: List[AvailabilitySlot] = []
    selected_slot: Optional[AvailabilitySlot] = None
    conversation_history: List[BaseMessage] = []
    current_booking: Optional[BookingRequest] = None



