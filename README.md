# Voice Agent Clinic Assistant

A voice-powered clinic assistant built with ElevenLabs and Flask that helps users:
- Get clinic information
- Check doctor availability 
- Book appointments

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your ElevenLabs API key:**
   ```bash
   set ELEVENLABS_API_KEY=your_api_key_here
   ```

3. **Start the Flask backend:**
   ```bash
   python app.py
   ```

4. **Run the voice agent (in another terminal):**
   ```bash
   python voice_agent.py
   ```
5. **Requires ffmpeg to actually use the ElevenLabs voice to run in your local, otherwise the agent logs response in your terminal** <br>
   Use this doc for ffmpeg installation setup & guide: https://docs.google.com/document/d/1_9FnwigR8fp5mSDvYnggvf8Ls5CXNG9D52Ad6b70L08/edit?usp=sharing <br>


## Usage

The voice agent can handle:

### General Queries
- "What are your clinic hours?"
- "Who are the doctors?"
- "Do you accept walk-ins?"
- "What services do you offer?"

### Availability Checks
- "Is the dentist available on Friday?"
- "Can I get a slot with the dentist on Saturday?"
- "What times are free on Monday?"

### Booking Appointments
After checking availability, the agent will guide you through:
1. Selecting a time slot
2. Providing your name
3. Confirming the booking

## API Endpoints

### GET `/get_slots?day=Friday`
Returns available slots for the specified day:
```json
{
  "doctor": "Dr. Nair",
  "available_slots": ["09:00", "09:30", "10:00", ...],
  "date": "2025-08-01"
}
```

### POST `/log_booking`
Books an appointment:
```json
{
  "name": "Aditya Gupta",
  "doctor": "Dr. Nair", 
  "day": "Friday",
  "slot": "09:00"
}
```

### GET `/knowledge`
Returns the knowledge base with clinic info, doctors, and FAQs.

## Files

- `a.py` - Used this for testing ElevenLabs api for realtime speech-to-text and text-to-speech utitlities
- `app.py` - Flask backend with booking logic
- `voice_agent.py` - ElevenLabs voice agent
- `knowledge_base.json` - Clinic information and FAQs
- `schedules.json` - Doctor schedules by day
- `appointments.json` - Existing appointments

## Features

- **Smart scheduling:** Respects working hours (9 AM - 6 PM) and lunch break (1-2 PM)
- **Alternating dentists:** Dr. Nair and Dr. Sharma alternate days
- **Conflict detection:** Automatically excludes booked time slots
- **Voice interaction:** Natural conversation flow with speech recognition and synthesis
- **Booking persistence:** Appointments are logged and saved to JSON file