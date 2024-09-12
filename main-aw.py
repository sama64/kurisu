from preprocessing import get_web_activity
from openai import OpenAI

if __name__ == '__main__':
  web_activity_string = get_web_activity(24)

  client = OpenAI(
    base_url = 'http://localhost:11434/v1',
    api_key='ollama', # required, but unused
  )
  print(web_activity_string)

  stream = client.chat.completions.create(
    # model="llama3",
    model = "llama3-8b-instruct",
    messages = [
    {"role": "system", "content": "Analyze the following web activity and respond only with a succinct description of the web activity. Do not include any introductions or explanations in your response."},
    {"role": "system", "content": f"Web activity:\n\n{web_activity_string}"},
    {"role": "user", "content": "Analyze the provided web activity of the last 24hs. Provide a short list of user activities"}
    ],
    stream=True, 
    temperature=0
  )

  for chunk in stream:
    if chunk.choices[0].delta.content is not None:
      print(chunk.choices[0].delta.content, end="")
