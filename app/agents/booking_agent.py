# from typing import Dict, Any, List
# from datetime import datetime, timedelta
# from langgraph.graph import StateGraph, END
# from langchain.schema import HumanMessage, AIMessage
# from app.models.schemas import ConversationState, ConversationContext
# from app.agents.tools import agent_tools, check_calendar_availability, book_calendar_slot
# from app.services.llm_service import llm_service
# from app.utils.date_parser import parse_natural_date_time

# import logging
# import traceback
# import time
# from openai._exceptions import RateLimitError,BadRequestError   # ✅ FINAL FIX

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

# class BookingAgentState(Dict[str, Any]):
#     pass

# class BookingAgent:
#     def __init__(self):
#         self.tools = {tool.name: tool for tool in agent_tools}
#         self.graph = self._build_graph()

#     def _build_graph(self) -> StateGraph:
#         workflow = StateGraph(BookingAgentState)

#         workflow.add_node("understand_intent", self._understand_intent)
#         workflow.add_node("check_availability", self._check_availability)
#         workflow.add_node("suggest_slots", self._suggest_slots)
#         workflow.add_node("confirm_booking", self._confirm_booking)
#         workflow.add_node("complete_booking", self._complete_booking)

#         workflow.set_entry_point("understand_intent")

#         workflow.add_conditional_edges(
#             "understand_intent",
#             self._route_after_intent,
#             {
#                 "check_availability": "check_availability",
#                 "need_more_info": "understand_intent",
#                 "confirm_booking": "confirm_booking"
#             }
#         )

#         workflow.add_edge("check_availability", "suggest_slots")
#         workflow.add_edge("suggest_slots", "confirm_booking")
#         workflow.add_edge("confirm_booking", "complete_booking")
#         workflow.add_edge("complete_booking", END)

#         compiled_graph = workflow.compile()
#         compiled_graph.recursion_limit = 40
#         return compiled_graph

#     def _understand_intent(self, state: BookingAgentState) -> BookingAgentState:
#         user_message = state.get("user_message", "")
#         context = state.get("context", ConversationContext(session_id="default"))

#         system_prompt = f"""
#         You are a helpful calendar booking assistant. Analyze the user's message and extract booking information.

#         Current conversation state: {context.state}
#         Conversation history: {context.conversation_history[-3:] if context.conversation_history else "None"}

#         Extract the following information if available:
#         1. Preferred date/time (convert natural language to specific datetime)
#         2. Meeting duration (default 60 minutes)
#         3. Meeting title/purpose
#         4. Any special requirements

#         Current date/time: {datetime.now().isoformat()}
#         """

#         max_retries = 5
#         for attempt in range(max_retries):
#             try:
#                 response = llm_service.generate_response([
#                     {"role": "system", "content": system_prompt},
#                     {"role": "user", "content": user_message}
#                 ])
#                 break
#             except RateLimitError:
#                 wait = 2 ** attempt
#                 logger.warning(f"Rate limit hit. Retrying in {wait} seconds... (Attempt {attempt + 1})")
#                 time.sleep(wait)
#             except BadRequestError as e:
#                 logger.error(f"InvalidRequestError: {str(e)}")
#                 state["agent_response"] = f"⚠️ Invalid request to LLM: {str(e)}"
#                 return state
#             except Exception as e:
#                 if attempt == max_retries - 1:
#                     logger.error("🔥 Error in LLM response after retries:", exc_info=True)
#                     state["agent_response"] = f"⚠️ Could not generate a response: {str(e)}"
#                     return state
#                 time.sleep(2 ** attempt)

#         try:
#             parsed_info = parse_natural_date_time(user_message)
#             if parsed_info:
#                 context.preferred_date = parsed_info.get("date")
#                 context.preferred_time = parsed_info.get("time")
#                 context.duration = parsed_info.get("duration", 60)

#             context.conversation_history.extend([
#                 HumanMessage(content=user_message),
#                 AIMessage(content=response)
#             ])

#             state.update({
#                 "context": context,
#                 "agent_response": response,
#                 "extracted_info": parsed_info
#             })

#             return state

#         except Exception as e:
#             logger.error("🔥 Error in _understand_intent:", exc_info=True)
#             state["agent_response"] = f"⚠️ Sorry, I ran into an error: {str(e)}"
#             return state

#     def _check_availability(self, state: BookingAgentState) -> BookingAgentState:
#         context = state.get("context")

#         if not context.preferred_date:
#             context.preferred_date = (datetime.now() + timedelta(days=1)).date()

#         start_date = datetime.combine(context.preferred_date, datetime.min.time())
#         end_date = start_date + timedelta(days=3)

#         try:
#             availability = check_calendar_availability.run({
#                 "start_date": start_date.isoformat(),
#                 "end_date": end_date.isoformat(),
#                 "duration_minutes": context.duration
#             })

#             context.suggested_slots = availability
#             context.state = ConversationState.CHECKING_AVAILABILITY

#             state.update({
#                 "context": context,
#                 "availability": availability
#             })
#             return state
#         except Exception as e:
#             logger.error("🔥 Error in _check_availability:", exc_info=True)
#             state["agent_response"] = f"⚠️ Couldn't check availability: {str(e)}"
#             return state

#     def _suggest_slots(self, state: BookingAgentState) -> BookingAgentState:
#         context = state.get("context")
#         availability = state.get("availability", [])

#         if not availability:
#             response = "I couldn't find any available slots for your preferred time."
#         else:
#             slots_text = []
#             for i, slot in enumerate(availability[:3], 1):
#                 start = datetime.fromisoformat(slot["start"])
#                 end = datetime.fromisoformat(slot["end"])
#                 slots_text.append(f"{i}. {start.strftime('%A, %B %d at %I:%M %p')} - {end.strftime('%I:%M %p')}")
#             response = "Here are some available slots:\n\n" + "\n".join(slots_text)

#         context.state = ConversationState.COLLECTING_INFO
#         context.conversation_history.append(AIMessage(content=response))

#         state.update({
#             "context": context,
#             "agent_response": response
#         })

#         return state

#     def _confirm_booking(self, state: BookingAgentState) -> BookingAgentState:
#         context = state.get("context")
#         user_message = state.get("user_message", "")
#         availability = state.get("availability", [])
#         selected_slot = None

#         if availability:
#             if "1" in user_message or "first" in user_message.lower():
#                 selected_slot = availability[0]
#             elif "2" in user_message or "second" in user_message.lower():
#                 selected_slot = availability[1] if len(availability) > 1 else None
#             elif "3" in user_message or "third" in user_message.lower():
#                 selected_slot = availability[2] if len(availability) > 2 else None

#         if selected_slot:
#             start_time = datetime.fromisoformat(selected_slot["start"])
#             end_time = datetime.fromisoformat(selected_slot["end"])

#             response = f"""📅 **Meeting Details:**\n- Date: {start_time.strftime('%A, %B %d, %Y')}\n- Time: {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"""

#             context.selected_slot = selected_slot
#             context.state = ConversationState.CONFIRMING_BOOKING
#         else:
#             response = "I didn't understand which slot you prefer."

#         state.update({
#             "context": context,
#             "agent_response": response
#         })

#         return state

#     def _complete_booking(self, state: BookingAgentState) -> BookingAgentState:
#         context = state.get("context")
#         user_message = state.get("user_message", "").lower()
#         selected_slot = context.selected_slot

#         if selected_slot and ("yes" in user_message or "confirm" in user_message):
#             try:
#                 booking_result = book_calendar_slot.run({
#                     "title": context.meeting_title,
#                     "start_time": selected_slot["start"],
#                     "end_time": selected_slot["end"],
#                     "description": context.meeting_description
#                 })

#                 if booking_result.get("success"):
#                     response = "🎉 Booking confirmed!"
#                     context.state = ConversationState.COMPLETED
#                 else:
#                     response = f"❌ Error: {booking_result.get('message')}"
#                     context.state = ConversationState.ERROR
#             except Exception as e:
#                 response = f"❌ Booking error: {str(e)}"
#                 context.state = ConversationState.ERROR
#         else:
#             response = "No problem! Let me know if you'd like to try again."
#             context.state = ConversationState.INITIAL

#         state.update({
#             "context": context,
#             "agent_response": response
#         })

#         return state

#     def _route_after_intent(self, state: BookingAgentState) -> str:
#         context = state.get("context")
#         extracted_info = state.get("extracted_info")

#         if context.state == ConversationState.CONFIRMING_BOOKING:
#             return "confirm_booking"
#         elif extracted_info and extracted_info.get("date") and extracted_info.get("time"):
#             return "check_availability"
#         else:
#             return "need_more_info"

#     def process_message(self, user_message: str, session_id: str = "default") -> Dict[str, Any]:
#         try:
#             initial_state = {
#                 "user_message": user_message,
#                 "context": ConversationContext(session_id=session_id),
#                 "session_id": session_id
#             }

#             result = self.graph.invoke(initial_state)

#             return {
#                 "response": result.get("agent_response"),
#                 "state": result.get("context").state,
#                 "context": result.get("context")
#             }
#         except Exception as e:
#             logger.error("🔥 Error in process_message:", exc_info=True)
#             return {
#                 "response": f"⚠️ Failed to process message: {str(e)}",
#                 "state": "error",
#                 "context": None
#             }

# booking_agent = BookingAgent()















































from typing import Dict, Any, List
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, END
from langchain.schema import HumanMessage, AIMessage
from app.models.schemas import ConversationState, ConversationContext
from app.agents.tools import agent_tools, check_calendar_availability, book_calendar_slot
from app.services.llm_service import llm_service
from app.utils.date_parser import parse_natural_date_time
from tenacity import retry, stop_after_attempt, wait_exponential

import logging
import traceback
import time
from openai._exceptions import RateLimitError, BadRequestError

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class BookingAgentState(Dict[str, Any]):
    pass

class BookingAgent:
    def __init__(self):
        self.tools = {tool.name: tool for tool in agent_tools}
        self.max_suggestions = 3
        self.default_duration = 60  # minutes
        self.lookahead_days = 3
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(BookingAgentState)

        workflow.add_node("understand_intent", self._understand_intent)
        workflow.add_node("check_availability", self._check_availability)
        workflow.add_node("suggest_slots", self._suggest_slots)
        workflow.add_node("confirm_booking", self._confirm_booking)
        workflow.add_node("complete_booking", self._complete_booking)

        workflow.set_entry_point("understand_intent")

        workflow.add_conditional_edges(
            "understand_intent",
            self._route_after_intent,
            {
                "check_availability": "check_availability",
                "need_more_info": "understand_intent",
                "confirm_booking": "confirm_booking"
            }
        )

        workflow.add_edge("check_availability", "suggest_slots")
        workflow.add_edge("suggest_slots", "confirm_booking")
        workflow.add_edge("confirm_booking", "complete_booking")
        workflow.add_edge("complete_booking", END)

        compiled_graph = workflow.compile()
        compiled_graph.recursion_limit = 40
        return compiled_graph

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _call_llm_with_retry(self, messages: List[Dict[str, str]]) -> str:
        """Wrapper for LLM calls with retry logic"""
        try:
            return llm_service.generate_response(messages)
        except RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {str(e)}")
            raise
        except BadRequestError as e:
            logger.error(f"Invalid request: {str(e)}")
            raise

    def _validate_state(self, state: BookingAgentState) -> None:
        """Validate required state fields"""
        if not isinstance(state.get("context"), ConversationContext):
            raise ValueError("Invalid context in state")
        if not state.get("user_message"):
            raise ValueError("Missing user message in state")

    def _understand_intent(self, state: BookingAgentState) -> BookingAgentState:
        try:
            self._validate_state(state)
            user_message = state["user_message"]
            context = state["context"]

            system_prompt = f"""
            You are a helpful calendar booking assistant. Analyze the user's message and extract booking information.

            Current conversation state: {context.state}
            Conversation history: {context.conversation_history[-3:] if context.conversation_history else "None"}

            Extract the following information if available:
            1. Preferred date/time (convert natural language to specific datetime)
            2. Meeting duration (default {self.default_duration} minutes)
            3. Meeting title/purpose
            4. Any special requirements

            Current date/time: {datetime.now().isoformat()}
            """

            response = self._call_llm_with_retry([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ])

            parsed_info = parse_natural_date_time(user_message)
            if parsed_info:
                context.preferred_date = parsed_info.get("date")
                context.preferred_time = parsed_info.get("time")
                context.duration = parsed_info.get("duration", self.default_duration)

            context.conversation_history.extend([
                HumanMessage(content=user_message),
                AIMessage(content=response)
            ])

            state.update({
                "context": context,
                "agent_response": response,
                "extracted_info": parsed_info
            })

            return state

        except Exception as e:
            logger.error("Error in _understand_intent:", exc_info=True)
            state["agent_response"] = f"⚠️ Sorry, I encountered an error: {str(e)}"
            return state

    def _check_availability(self, state: BookingAgentState) -> BookingAgentState:
        context = state["context"]

        if not context.preferred_date:
            context.preferred_date = (datetime.now() + timedelta(days=1)).date()

        start_date = datetime.combine(context.preferred_date, datetime.min.time())
        end_date = start_date + timedelta(days=self.lookahead_days)

        try:
            availability = check_calendar_availability.run({
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "duration_minutes": context.duration
            })

            context.suggested_slots = availability
            context.state = ConversationState.CHECKING_AVAILABILITY

            state.update({
                "context": context,
                "availability": availability
            })
            return state
        except Exception as e:
            logger.error("Error in _check_availability:", exc_info=True)
            state["agent_response"] = f"⚠️ Couldn't check availability: {str(e)}"
            return state

    def _suggest_slots(self, state: BookingAgentState) -> BookingAgentState:
        context = state["context"]
        availability = state.get("availability", [])

        if not availability:
            response = "I couldn't find any available slots for your preferred time."
        else:
            slots_text = []
            for i, slot in enumerate(availability[:self.max_suggestions], 1):
                start = datetime.fromisoformat(slot["start"])
                end = datetime.fromisoformat(slot["end"])
                slots_text.append(f"{i}. {start.strftime('%A, %B %d at %I:%M %p')} - {end.strftime('%I:%M %p')}")
            response = "Here are some available slots:\n\n" + "\n".join(slots_text)

        context.state = ConversationState.COLLECTING_INFO
        context.conversation_history.append(AIMessage(content=response))

        state.update({
            "context": context,
            "agent_response": response
        })

        return state

    def _confirm_booking(self, state: BookingAgentState) -> BookingAgentState:
        context = state["context"]
        user_message = state.get("user_message", "").lower()
        availability = state.get("availability", [])
        
        selected_slot = None
        for i, slot in enumerate(availability[:self.max_suggestions], 1):
            if (str(i) in user_message or 
                f"{i}st" in user_message or 
                f"{i}nd" in user_message or 
                f"{i}rd" in user_message):
                selected_slot = slot
                break

        if selected_slot:
            start_time = datetime.fromisoformat(selected_slot["start"])
            end_time = datetime.fromisoformat(selected_slot["end"])

            response = f"""📅 **Meeting Details:**\n- Date: {start_time.strftime('%A, %B %d, %Y')}\n- Time: {start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}"""

            context.selected_slot = selected_slot
            context.state = ConversationState.CONFIRMING_BOOKING
        else:
            response = "I didn't understand which slot you prefer. Please specify (1, 2, or 3)."

        state.update({
            "context": context,
            "agent_response": response
        })

        return state

    def _complete_booking(self, state: BookingAgentState) -> BookingAgentState:
        context = state["context"]
        user_message = state.get("user_message", "").lower()
        selected_slot = context.selected_slot

        if selected_slot and ("yes" in user_message or "confirm" in user_message):
            try:
                booking_result = book_calendar_slot.run({
                    "title": context.meeting_title or "Meeting",
                    "start_time": selected_slot["start"],
                    "end_time": selected_slot["end"],
                    "description": context.meeting_description or "Scheduled via booking assistant"
                })

                if booking_result.get("success"):
                    response = "🎉 Booking confirmed!"
                    context.state = ConversationState.COMPLETED
                else:
                    response = f"❌ Error: {booking_result.get('message', 'Unknown error')}"
                    context.state = ConversationState.ERROR
            except Exception as e:
                response = f"❌ Booking error: {str(e)}"
                context.state = ConversationState.ERROR
        else:
            response = "No problem! Let me know if you'd like to try again."
            context.state = ConversationState.INITIAL

        state.update({
            "context": context,
            "agent_response": response
        })

        return state

    def _route_after_intent(self, state: BookingAgentState) -> str:
        context = state["context"]
        extracted_info = state.get("extracted_info")

        if context.state == ConversationState.CONFIRMING_BOOKING:
            return "confirm_booking"
        elif extracted_info and extracted_info.get("date") and extracted_info.get("time"):
            return "check_availability"
        else:
            return "need_more_info"

    def process_message(self, user_message: str, session_id: str = "default") -> Dict[str, Any]:
        logger.info(f"Processing message for session {session_id}")
        
        if not user_message or not isinstance(user_message, str):
            return {
                "response": "Please provide a valid message",
                "state": "error",
                "context": None
            }

        try:
            initial_state = {
                "user_message": user_message,
                "context": ConversationContext(session_id=session_id),
                "session_id": session_id
            }
            
            start_time = time.time()
            result = self.graph.invoke(initial_state)
            elapsed = time.time() - start_time
            
            logger.info(f"Completed processing in {elapsed:.2f}s")
            
            return {
                "response": result.get("agent_response"),
                "state": result.get("context").state.name if hasattr(result.get("context").state, 'name') else str(result.get("context").state),
                "context": result.get("context")
            }
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}\n{traceback.format_exc()}")
            return {
                "response": "⚠️ An error occurred while processing your request. Please try again.",
                "state": "error",
                "context": None
            }

booking_agent = BookingAgent()