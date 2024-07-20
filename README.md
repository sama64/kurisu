# Concept
Kurisu is meant to be a localhost lightweight-ish anti-procrastination system that uses an AI companion based on Kurisu Makise from Steins;Gate

![kurisu](https://github.com/user-attachments/assets/4046b66b-a138-40a1-9a7d-312903ed6f71)

The core idea is to have an AI character avatar pop up in the user's screen to persuade them to stop procrastinating and get back to doing their tasks. 
Procrastination is determined through an LLM interpreter that consumes a list of tasks and user activity provided by [ActivityWatch](https://github.com/ActivityWatch/activitywatch)
Potentially having actions to close tabs and windows in the future.\
\
It uses the [openai](https://github.com/openai/openai-python) library. 
Currently supports ollama but can be easily swapped to any api compatible with openai standards.

# Features
- [Basic tasks app](https://github.com/sama64/kurisu-gui) ✅
- Settings panel
- Generate periodic user-procrastination reports (Only web activity for now)
- Static avatar for character dialogue
- Main process for periodic generations and avatar popup
- Long term memory

### FAQ
*__Q: Why ActivityWatch?__*

**A:** We chose AW because it has a rich ecosystem of ['watchers'](https://docs.activitywatch.net/en/latest/watchers.html) 
that allow you to track even when you go to the bathroom if that's what you want with minimal configuration.\
This can allow users to give Kurisu access to tracking way more things in the future with minimal changes.

*__Q: Do you really need an LLM to interpret the user activity data?__*

**A:** We want to offload the reasoning from the character prompt so it can roleplay better and be more consistent with the character.

*__Q: Why is the main code in python and the GUI in C?? What's wrong with you?!?__*

**A:** We're planning on doing a 3d avatar for kurisu in the future with OpenGL, but don't tell anyone yet.
