"""
Tool implementations for the Airline Customer Service Agent System.

This module defines all the function tools that agents can use to perform
actions like updating seats, checking flight status, and canceling flights.
"""

from typing import Optional, Dict, Any
from agents import function_tool, RunContextWrapper
from .context import AirlineAgentContext, update_context
import random
from datetime import datetime, timedelta


@function_tool(
    name_override="faq_lookup_tool",
    description_override="Look up answers to frequently asked questions about airline policies and services"
)
async def faq_lookup_tool(question: str) -> str:
    """
    Look up answers to frequently asked questions.

    Args:
        question: The FAQ question to look up

    Returns:
        str: Answer to the FAQ question
    """
    # FAQ database (simplified for demo)
    faq_database = {
        "baggage": {
            "carry-on": "You are allowed one carry-on bag (max 22\" x 14\" x 9\") and one personal item (purse, laptop bag, etc.).",
            "checked": "First checked bag: $35. Second checked bag: $45. Weight limit: 50 lbs per bag.",
            "overweight": "Bags over 50 lbs incur an additional $100 fee. Maximum weight: 70 lbs.",
            "international": "International flights include one free checked bag up to 50 lbs."
        },
        "wifi": {
            "availability": "Wi-Fi is available on all domestic flights and most international flights.",
            "cost": "Wi-Fi pricing: $8 for messaging only, $19 for full internet access on domestic flights.",
            "free": "Free messaging is available on all flights for T-Mobile customers."
        },
        "seats": {
            "selection": "Seats can be selected for free during check-in (24 hours before departure) or purchased in advance.",
            "extra-legroom": "Extra legroom seats are available for $49-$149 depending on flight duration.",
            "upgrade": "Upgrades to Premium Economy or Business Class can be purchased at check-in if available."
        },
        "check-in": {
            "online": "Online check-in opens 24 hours before departure and closes 60 minutes before.",
            "airport": "Airport check-in closes 45 minutes before domestic flights, 60 minutes for international.",
            "mobile": "Mobile boarding passes are accepted at all airports."
        },
        "meals": {
            "domestic": "Complimentary snacks and beverages on all flights. Meals available for purchase on flights over 3 hours.",
            "international": "Complimentary meals served on all international flights.",
            "special": "Special meal requests must be made at least 24 hours before departure."
        }
    }

    # Normalize the question
    question_lower = question.lower()

    # Find the most relevant FAQ category and answer
    for category, items in faq_database.items():
        if category in question_lower:
            for key, answer in items.items():
                if key in question_lower:
                    return answer

    # Check for specific keywords across all categories
    for category, items in faq_database.items():
        for key, answer in items.items():
            if key in question_lower or any(word in question_lower for word in key.split('-')):
                return answer

    # Default response if no specific FAQ found
    if "bag" in question_lower or "luggage" in question_lower:
        return "For baggage policies: Carry-on bags must be 22\" x 14\" x 9\" or smaller. First checked bag is $35, second is $45. Weight limit is 50 lbs per bag."
    elif "wifi" in question_lower or "internet" in question_lower:
        return "Wi-Fi is available on most flights for $8 (messaging) or $19 (full internet). Free messaging for T-Mobile customers."
    elif "seat" in question_lower:
        return "Free seat selection is available during check-in (24 hours before departure). Advanced seat selection and extra legroom seats are available for purchase."
    else:
        return "I can help with questions about baggage, Wi-Fi, seats, check-in, and meals. Please be more specific about what you'd like to know."


@function_tool(
    name_override="update_seat",
    description_override="Update a passenger's seat assignment"
)
async def update_seat(
    context: RunContextWrapper[AirlineAgentContext],
    confirmation_number: str,
    new_seat: str
) -> str:
    """
    Update a passenger's seat assignment.

    Args:
        context: The current conversation context
        confirmation_number: Booking confirmation number
        new_seat: New seat assignment

    Returns:
        str: Confirmation message
    """
    # Validate confirmation number matches context
    if context.context.confirmation_number and context.context.confirmation_number != confirmation_number:
        return f"Error: Confirmation number {confirmation_number} does not match your booking {context.context.confirmation_number}"

    # Check if seat is available (simulated)
    occupied_seats = ["12A", "12B", "15C", "20F", "25D"]  # Example occupied seats
    if new_seat in occupied_seats:
        return f"Sorry, seat {new_seat} is not available. Please choose another seat."

    # Validate seat format
    import re
    if not re.match(r"^\d{1,2}[A-F]$", new_seat):
        return f"Invalid seat number format: {new_seat}. Please use format like '12A' or '23F'."

    # Update the context
    old_seat = context.context.seat_number or "not previously assigned"
    context.context.seat_number = new_seat
    context.context.last_action = f"Seat updated from {old_seat} to {new_seat}"

    return f"Successfully updated your seat from {old_seat} to {new_seat} for confirmation number {confirmation_number}. Your new seat assignment is confirmed."


@function_tool(
    name_override="flight_status_tool",
    description_override="Check the current status of a flight"
)
async def flight_status_tool(flight_number: str) -> str:
    """
    Check the current status of a flight.

    Args:
        flight_number: Flight number to check

    Returns:
        str: Flight status information
    """
    # Simulate flight status lookup
    statuses = ["On Time", "Delayed", "Boarding", "Departed", "Arrived"]
    status = random.choice(statuses)

    # Generate realistic flight times
    now = datetime.now()
    scheduled_departure = now + timedelta(hours=random.randint(1, 8))

    if status == "Delayed":
        actual_departure = scheduled_departure + timedelta(minutes=random.randint(15, 90))
        delay_minutes = int((actual_departure - scheduled_departure).total_seconds() / 60)
        return (f"Flight {flight_number} is DELAYED by {delay_minutes} minutes.\n"
                f"Scheduled departure: {scheduled_departure.strftime('%I:%M %p')}\n"
                f"New departure time: {actual_departure.strftime('%I:%M %p')}\n"
                f"Gate: {random.choice(['A', 'B', 'C', 'D'])}{random.randint(1, 30)}")
    elif status == "On Time":
        return (f"Flight {flight_number} is ON TIME.\n"
                f"Scheduled departure: {scheduled_departure.strftime('%I:%M %p')}\n"
                f"Gate: {random.choice(['A', 'B', 'C', 'D'])}{random.randint(1, 30)}\n"
                f"Boarding starts 30 minutes before departure.")
    elif status == "Boarding":
        return (f"Flight {flight_number} is currently BOARDING.\n"
                f"Gate: {random.choice(['A', 'B', 'C', 'D'])}{random.randint(1, 30)}\n"
                f"Please proceed to the gate immediately.")
    elif status == "Departed":
        departed_time = now - timedelta(minutes=random.randint(10, 60))
        return (f"Flight {flight_number} has DEPARTED at {departed_time.strftime('%I:%M %p')}.\n"
                f"Estimated arrival time: {(now + timedelta(hours=random.randint(1, 4))).strftime('%I:%M %p')}")
    else:  # Arrived
        arrived_time = now - timedelta(minutes=random.randint(5, 30))
        return (f"Flight {flight_number} has ARRIVED at {arrived_time.strftime('%I:%M %p')}.\n"
                f"Baggage claim: Carousel {random.randint(1, 8)}")


@function_tool(
    name_override="baggage_tool",
    description_override="Get information about baggage policies and fees"
)
async def baggage_tool(query: str) -> str:
    """
    Get information about baggage policies and fees.

    Args:
        query: Baggage-related query

    Returns:
        str: Baggage information
    """
    query_lower = query.lower()

    if "fee" in query_lower or "cost" in query_lower or "price" in query_lower:
        return """Baggage Fees:
• First checked bag: $35
• Second checked bag: $45
• Third+ checked bag: $150 each
• Overweight (51-70 lbs): +$100
• Oversized (63-115 linear inches): +$150
• Sports equipment: $75-$150 depending on item
• International flights: First bag free, second bag $100"""

    elif "weight" in query_lower or "size" in query_lower or "dimension" in query_lower:
        return """Baggage Size and Weight Limits:
• Checked bags: Maximum 50 lbs and 62 linear inches (length + width + height)
• Overweight: 51-70 lbs (additional fee applies)
• Oversized: 63-115 linear inches (additional fee applies)
• Carry-on: Maximum 22" x 14" x 9" and must fit in overhead bin
• Personal item: Must fit under the seat (purse, laptop bag, small backpack)"""

    elif "carry" in query_lower or "cabin" in query_lower:
        return """Carry-On Baggage Policy:
• One carry-on bag: Maximum 22" x 14" x 9"
• One personal item: Must fit under the seat
• Both items are free of charge
• Medical devices and assistive devices don't count toward limit
• Duty-free purchases are allowed in addition to carry-on allowance"""

    elif "special" in query_lower or "sport" in query_lower or "equipment" in query_lower:
        return """Special Items and Sports Equipment:
• Golf clubs: $75 (up to 50 lbs)
• Skis/Snowboard: $75
• Surfboard: $150
• Bicycle: $150 (must be in proper case)
• Musical instruments: Can be carried on if they fit, or checked for standard bag fee
• Firearms: $150 (must be declared and properly packed)"""

    else:
        return """General Baggage Information:
• First checked bag: $35 (free on international flights)
• Maximum weight: 50 lbs per bag
• Carry-on size: 22" x 14" x 9"
• Track your bags with our mobile app
• Damaged bag claims must be filed within 24 hours
For more specific information, please ask about fees, size limits, or special items."""


@function_tool(
    name_override="display_seat_map",
    description_override="Display an interactive seat map for seat selection"
)
async def display_seat_map(
    context: RunContextWrapper[AirlineAgentContext]
) -> str:
    """
    Trigger the display of an interactive seat map.

    This returns a special string that the frontend can detect
    to show the seat selection UI.

    Args:
        context: The current conversation context

    Returns:
        str: Special trigger string for seat map display
    """
    # Store that we're showing the seat map
    context.context.last_action = "Displaying seat map"
    context.context.conversation_stage = "seat_selection"

    # Return the special trigger string that the frontend will detect
    return "DISPLAY_SEAT_MAP"


@function_tool(
    name_override="cancel_flight",
    description_override="Cancel a flight booking"
)
async def cancel_flight(
    context: RunContextWrapper[AirlineAgentContext]
) -> str:
    """
    Cancel a flight booking.

    Args:
        context: The current conversation context

    Returns:
        str: Cancellation confirmation message
    """
    # Check if we have the required information
    if not context.context.confirmation_number:
        return "Error: No confirmation number found. Please provide your confirmation number first."

    if not context.context.flight_number:
        return "Error: No flight number found. Please provide your flight number first."

    # Simulate cancellation process
    confirmation_number = context.context.confirmation_number
    flight_number = context.context.flight_number
    passenger_name = context.context.passenger_name or "Valued Customer"

    # Calculate refund (simplified logic)
    refund_amount = random.choice(["$342.50", "$567.00", "$189.25", "$423.75", "$0.00 (non-refundable)"])

    # Update context
    context.context.last_action = f"Cancelled flight {flight_number}"
    context.context.conversation_stage = "cancellation_complete"

    return f"""Flight Cancellation Confirmed:

• Confirmation Number: {confirmation_number}
• Flight: {flight_number}
• Passenger: {passenger_name}
• Status: CANCELLED
• Refund Amount: {refund_amount}
• Refund Method: Original payment method
• Processing Time: 5-7 business days

A cancellation confirmation email has been sent to your registered email address.

Important: Please destroy or delete any printed or digital boarding passes for this flight.

If you need to book a new flight, you can use the refund amount as credit for future travel within 12 months."""


# Helper function to validate flight numbers
def is_valid_flight_number(flight_number: str) -> bool:
    """
    Validate if a flight number follows airline format.

    Args:
        flight_number: Flight number to validate

    Returns:
        bool: True if valid format
    """
    import re
    # Pattern: 2-3 letter airline code + 1-4 digits
    pattern = r"^[A-Z]{2,3}\d{1,4}$"
    return bool(re.match(pattern, flight_number.upper()))


# Helper function to generate mock flight data
def generate_flight_data(flight_number: str) -> Dict[str, Any]:
    """
    Generate mock flight data for testing.

    Args:
        flight_number: Flight number

    Returns:
        Dict with flight details
    """
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
              "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"]

    departure_city = random.choice(cities)
    arrival_city = random.choice([c for c in cities if c != departure_city])

    now = datetime.now()
    departure_time = now + timedelta(hours=random.randint(1, 12))
    flight_duration = timedelta(hours=random.randint(1, 6), minutes=random.randint(0, 59))
    arrival_time = departure_time + flight_duration

    return {
        "flight_number": flight_number,
        "departure_city": departure_city,
        "arrival_city": arrival_city,
        "departure_time": departure_time.isoformat(),
        "arrival_time": arrival_time.isoformat(),
        "duration": str(flight_duration),
        "aircraft": random.choice(["Boeing 737", "Airbus A320", "Boeing 777", "Airbus A350"]),
        "gate": f"{random.choice(['A', 'B', 'C', 'D'])}{random.randint(1, 30)}"
    }