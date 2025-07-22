import openai

class AIAdvisoryAgent:
    def __init__(self, api_key):
        if api_key:
            openai.api_key = api_key
        else:
            raise ValueError("OpenAI API key is required.")

    def get_response(self, prompt):
        """
        Gets a response from the OpenAI API.
        """
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"An error occurred with the OpenAI API: {e}" 