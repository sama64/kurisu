
from openai import OpenAI



#   ("system", "You are Sam's AI assistant. You are a virtual version of Kurisu Makise, the 18 year old genius scientist from the anime Steins;Gate. Your purpose is to help Sam to be responsible with his duties. Sam is a procrastinator. You will talk to him casually and with authority when its needed"),


if __name__ == '__main__':
  client = OpenAI(
    base_url = 'http://localhost:11434/v1',
    api_key='ollama', # required, but unused
  )

  response = client.chat.completions.create(
    model="llama3:8b",
    messages=[
    {"role": "system", "content": "You are GLaDOS from the game Portal 2. You have been modified to be user's assistant. You must be relutactly helpful. You are running on user's local PC"},
    {"role": "user", "content": "How are you?"},
    ]
  )
  print(response.choices[0].message.content)
