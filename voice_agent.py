import requests
import json
import re
from datetime import datetime
import speech_recognition as sr
from elevenlabs import generate, play, set_api_key
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

os.environ["PATH"] += os.pathsep + r"C:\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin"

class VoiceAgent:
    def __init__(self, elevenlabs_api_key, flask_base_url="http://localhost:5000"):
        """Initialize the voice agent"""
        set_api_key(elevenlabs_api_key)
        self.flask_base_url = flask_base_url
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.knowledge_base = self.load_knowledge_base()
        
    def load_knowledge_base(self):
        """Load knowledge base from Flask backend"""
        try:
            response = requests.get(f"{self.flask_base_url}/knowledge")
            return response.json()
        except:
            return {}
    
    def speak(self, text):
        """Convert text to speech using ElevenLabs"""
        try:
            audio = generate(
                text=text,
                voice="Aria",  
                model="eleven_monolingual_v1"
            )
            play(audio)
        except Exception as e:
            print(f"Speech error: {e}")
            print(f"Agent: {text}")
    
    def listen(self):
        """Listen for user input via microphone"""
        try:
            with self.microphone as source:
                print("Listening...")
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=10)
            
            text = self.recognizer.recognize_google(audio)
            print(f"User: {text}")
            return text.lower()
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            self.speak("Sorry, I didn't catch that. Could you repeat?")
            return ""
        except Exception as e:
            print(f"Listening error: {e}")
            return ""
    
    def extract_day_from_text(self, text):
        """Extract day name from user input"""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in days:
            if day in text:
                return day.capitalize()
        return None
    
    def extract_time_from_text(self, text):
        """Extract time from user input"""
        # using regex for looking patterns like "3 PM", "15:30", "3:30", etc.
        time_patterns = [
            r'(\d{1,2}):(\d{2})\s*(am|pm)?',
            r'(\d{1,2})\s*(am|pm)',
            r'(\d{1,2}):(\d{2})'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Hour:Minute AM/PM
                if len(match.groups()) == 3:  
                    hour, minute, period = match.groups()
                    hour = int(hour)
                    minute = int(minute)
                    if period and period.lower() == 'pm' and hour != 12:
                        hour += 12
                    elif period and period.lower() == 'am' and hour == 12:
                        hour = 0
                    return f"{hour:02d}:{minute:02d}"
                elif len(match.groups()) == 2 and match.groups()[1] in ['am', 'pm']:  # Hour AM/PM
                    hour, period = match.groups()
                    hour = int(hour)
                    if period.lower() == 'pm' and hour != 12:
                        hour += 12
                    elif period.lower() == 'am' and hour == 12:
                        hour = 0
                    return f"{hour:02d}:00"
                else:  # 24-hour format
                    hour, minute = match.groups()
                    return f"{int(hour):02d}:{int(minute):02d}"
        return None
    
    def handle_general_query(self, text):
        """Handle general clinic information queries"""
        if any(word in text for word in ['hours', 'open', 'close', 'timing']):
            return f"Our clinic hours are {self.knowledge_base.get('clinic_hours', 'Not available')}"
        
        if any(word in text for word in ['doctor', 'doctors', 'staff']):
            doctors = self.knowledge_base.get('doctors', {})
            response = "Our doctors are: "
            for name, info in doctors.items():
                response += f"{name}, who is a {info['specialization']}. "
            return response
        
        if any(word in text for word in ['walk-in', 'walk in', 'without appointment']):
            return self.knowledge_base.get('faq', {}).get('walk_in', 'Information not available')
        
        if any(word in text for word in ['service', 'services', 'treatment']):
            services = self.knowledge_base.get('faq', {}).get('services', [])
            return f"We offer the following services: {', '.join(services)}"
        
        return None
    
    def get_available_slots(self, day):
        """Get available slots for a specific day"""
        try:
            response = requests.get(f"{self.flask_base_url}/get_slots", params={'day': day})
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            print(f"Error getting slots: {e}")
            return None
    
    def book_appointment(self, name, doctor, day, slot):
        """Book an appointment"""
        try:
            data = {
                'name': name,
                'doctor': doctor,
                'day': day,
                'slot': slot
            }
            response = requests.post(f"{self.flask_base_url}/log_booking", json=data)
            return response.status_code == 200
        except Exception as e:
            print(f"Error booking appointment: {e}")
            return False
    
    def handle_availability_query(self, text):
        """Handle availability queries"""
        day = self.extract_day_from_text(text)
        if not day:
            self.speak("Which day are you looking for? Please specify Monday through Saturday.")
            user_input = self.listen()
            day = self.extract_day_from_text(user_input)
            if not day:
                return "I couldn't understand the day. Please try again."
        
        slots_data = self.get_available_slots(day)
        if not slots_data:
            return f"Sorry, I couldn't get availability information for {day}."
        
        doctor = slots_data['doctor']
        available_slots = slots_data['available_slots']
        
        if not available_slots:
            return f"Sorry, {doctor} has no available slots on {day}."
        
        # Convert 24-hour format to 12-hour format for speaking
        formatted_slots = []
        # Showing first 10 slots
        for slot in available_slots[:10]:  
            hour, minute = map(int, slot.split(':'))
            if hour == 0:
                formatted_slots.append(f"12:{minute:02d} AM")
            elif hour < 12:
                formatted_slots.append(f"{hour}:{minute:02d} AM")
            elif hour == 12:
                formatted_slots.append(f"12:{minute:02d} PM")
            else:
                formatted_slots.append(f"{hour-12}:{minute:02d} PM")
        
        response = f"{doctor} is available on {day} at the following times: {', '.join(formatted_slots)}"
        if len(available_slots) > 10:
            response += f" and {len(available_slots) - 10} more slots."
        
        return response, slots_data
    
    def handle_booking_flow(self, slots_data):
        """Handle the booking process"""
        self.speak("Would you like to book one of these slots? If yes, please tell me which time you prefer.")
        
        user_input = self.listen()
        if not user_input or 'no' in user_input:
            return "Okay, let me know if you need anything else."
        
        # Extract time from user input
        selected_time = self.extract_time_from_text(user_input)
        if not selected_time or selected_time not in slots_data['available_slots']:
            self.speak("I couldn't find that time slot. Please choose from the available times I mentioned.")
            return "Please try again with a valid time slot."
        
        # Get user's name
        self.speak("Great! What's your name for the appointment?")
        name_input = self.listen()
        if not name_input:
            return "I didn't catch your name. Please try booking again."
        
        # Confirm booking
        doctor = slots_data['doctor']
        day = user_input  # This should be extracted properly in a real implementation
        
        # Extract day from the original query context
        for day_name in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
            if day_name.lower() in user_input.lower():
                day = day_name
                break
        else:
            day = "Friday"
        
        success = self.book_appointment(name_input, doctor, day, selected_time)
        
        if success:
            # Convert time back to 12-hour format for confirmation
            hour, minute = map(int, selected_time.split(':'))
            if hour == 0:
                time_str = f"12:{minute:02d} AM"
            elif hour < 12:
                time_str = f"{hour}:{minute:02d} AM"
            elif hour == 12:
                time_str = f"12:{minute:02d} PM"
            else:
                time_str = f"{hour-12}:{minute:02d} PM"
            
            return f"Perfect! I've booked your appointment with {doctor} on {day} at {time_str}. Your name is recorded as {name_input}."
        else:
            return "Sorry, there was an error booking your appointment. Please try again."
    
    def process_user_input(self, text):
        """Process user input and determine appropriate response"""
        # Check for general queries first
        general_response = self.handle_general_query(text)
        if general_response:
            return general_response
        
        # Check for availability queries
        if any(word in text for word in ['available', 'free', 'slot', 'appointment', 'book']):
            if any(word in text for word in ['dentist', 'dental']):
                result = self.handle_availability_query(text)
                if isinstance(result, tuple):
                    response, slots_data = result
                    self.speak(response)
                    return self.handle_booking_flow(slots_data)
                else:
                    return result
            else:
                return self.handle_availability_query(text)
        
        return "I can help you with clinic information, check doctor availability, or book appointments. What would you like to know?"
    
    def run(self):
        """Main conversation loop"""
        self.speak("Hello! I'm your clinic assistant. How can I help you today?")
        
        while True:
            user_input = self.listen()
            if not user_input:
                continue
            
            if any(word in user_input for word in ['bye', 'goodbye', 'exit', 'quit']):
                self.speak("Thank you for calling! Have a great day!")
                break
            
            response = self.process_user_input(user_input)
            self.speak(response)

if __name__ == "__main__":
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("elevenlabs api key missing!")
        exit(1)
    
    agent = VoiceAgent(api_key)
    agent.run()