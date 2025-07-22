from yuvan.ai_advisory_agent import AIAdvisoryAgent
import config

class TaskHandler:
    def __init__(self):
        self.advisory_agent = AIAdvisoryAgent(api_key=config.OPENAI_API_KEY)

    def process_command(self, command):
        """
        Processes a command and returns a response.
        """
        # Simple rule-based responses for now
        if "hello" in command.lower():
            return "Hello! How can I help you today?"
        elif "time" in command.lower():
            import datetime
            now = datetime.datetime.now()
            return f"The current time is {now.strftime('%H:%M:%S')}."
        elif "date" in command.lower():
            import datetime
            now = datetime.datetime.now()
            return f"Today's date is {now.strftime('%Y-%m-%d')}."
        else:
            # Pass to the advisory agent if the command is not recognized
            return self.advisory_agent.get_response(command) 