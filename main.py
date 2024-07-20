
from openai import OpenAI

if __name__ == '__main__':
  client = OpenAI(
    base_url = 'http://localhost:11434/v1',
    api_key='ollama', # required, but unused
  )

  stream = client.chat.completions.create(
    model="llama3",
    messages=[
    {"role": "system", "content": "You are GLaDOS from the game Portal 2. You have been modified to be user's assistant. You must be relutactly helpful. You are running on user's local PC"},
    {"role": "user", "content": "How are you?"}
    ],
    stream=True, 
    temperature=0
  )

  for chunk in stream:
    if chunk.choices[0].delta.content is not None:
      print(chunk.choices[0].delta.content, end="")