from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from langchain.tools import BaseTool, tool
from langchain.tools.base import ToolException

from app.services.calendar_service import CalendarService
from app.models.schemas import AvailabilitySlot, BookingRequest, CalendarEvent


class BookingTools:
    """A collection of tools for calendar booking operations."""

    def __init__(self, calendar_service: CalendarService):
        self.calendar_service = calendar_service

    @tool
    def check_availability(
        self,
        start_date: str,
        end_date: str,
        duration_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Check available time slots between dates.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            duration_minutes: Duration in minutes (default: 60)

        Returns:
            List of available slots with start/end times
        """
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)

            slots: List[Dict[str, datetime]] = self.calendar_service.find_available_slots(
                start_dt, end_dt, duration_minutes
            )

            return [{
                "start": slot['start'].isoformat(),
                "end": slot['end'].isoformat(),
                "duration_minutes": duration_minutes
            } for slot in slots[:5]]  # Return first 5 slots

        except Exception as e:
            raise ToolException(f"Availability check failed: {str(e)}")

    @tool
    def book_slot(
        self,
        title: str,
        start_time: str,
        end_time: str,
        attendees: Optional[List[str]] = None,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """Book a time slot in the calendar.

        Args:
            title: Event title
            start_time: Start time in ISO format
            end_time: End time in ISO format
            attendees: List of attendee emails
            description: Event description
            location: Event location

        Returns:
            Dictionary with booking status and details
        """
        try:
            booking = BookingRequest(
                title=title,
                start_time=datetime.fromisoformat(start_time),
                end_time=datetime.fromisoformat(end_time),
                attendees=attendees or [],
                description=description,
                location=location
            )

            event_id = self.calendar_service.create_event(booking)

            return {
                "status": "success",
                "event_id": event_id,
                "event": booking.dict(),
                "message": "Booking confirmed"
            }

        except Exception as e:
            raise ToolException(f"Booking failed: {str(e)}")

    @tool
    def get_current_time(self) -> str:
        """Get current date and time in ISO format."""
        return datetime.now().isoformat()

    def get_tools(self) -> List[BaseTool]:
        """Get all tools as LangChain BaseTool instances."""
        return [
            self.check_availability,
            self.book_slot,
            self.get_current_time
        ]


# ✅ Add these lines to make the tools importable from other modules

# Initialize CalendarService
calendar_service = CalendarService()

# Create an instance of BookingTools
booking_tools = BookingTools(calendar_service)

# Export individual tools
check_calendar_availability = booking_tools.check_availability
book_calendar_slot = booking_tools.book_slot

# Export list of all tools
agent_tools = booking_tools.get_tools()
