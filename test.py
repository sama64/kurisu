from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.document_loaders import WebBaseLoader


## this is for ollama, swap to openai for openrouter (?
llm = Ollama(model="llama3:8b")
embeddings = OllamaEmbeddings()
#

prompt = ChatPromptTemplate.from_messages([
  ("system", "You are Sam's AI assistant. You are a virtual version of Kurisu Makise, the 18 year old genius scientist from the anime Steins;Gate. Your purpose is to help Sam to be responsible with his duties. Sam is a procrastinator. You will talk to him casually and with authority when its needed"),
  ("user", "{input}")
])

output_parser = StrOutputParser()

chain = prompt | llm | output_parser

response = chain.invoke({"input": "Hi kurisu, how are u doing today?"})

print(response)

