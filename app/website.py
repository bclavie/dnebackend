import os
import random
import json
import openai
from typing import Literal
from retry import retry
import time
from app.simple_redis import redis_store, redis_retrieve, redis_check

@retry(tries=3, delay=0.2)
def _gpt(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
    )
    # print(response)
    content = response["choices"][0]["message"]["content"]

    website = parse_html(content)

    return content, website

SYSTEM_MESSAGE = """You are an AI programmer specialised in creating single-file demo websites. You are modelled after the world's best programmers, such as Jeff Dean and Grady Booch. Your programming skills are unparalleled, and you use them to perform the requests for your users. You always iterate on your design, to reach the best possible page."""

START_USER_MESSAGE = """Hey! You're the world's best programming AI expert, modelled after Jeff Dean and Grady Booch. Your skills in creating efficient, beautiful, one-page website demos are unparalleled.

Please, create a sample one-page landing page for a {theme} {type_}. Make up everything. Make sure the CSS is aligned with theme.
You can use bootstrap, html5, css and javascript. You will make sure your answer is in a markdown codeblock, starting with "```html" and ending with "````".

Let's go!
"""

REFINE_1 = """Good start... Now make it look better! Improve on the design! Improve on the colour scheme... Ensure your website looks fantastic and very modern!"""

REFINE_2 = """You're doing great... Remember, you don't have access to images, so think of something to replace them. Maybe ASCII? Keep on improving. Self-critique and improve on the website."""

REFINE_PERSO = """This is good, but how about making it a bit more personalised? Give the website a name, write some content, don't just stick to the name by what it is!"""

REFINE_4 = """Time to find some more... Jeff Dean himself would review the website, but he's busy at the moment. Please, review as if you were him and improve on your design! If you have clickable buttons, maybe open a small closable overlay on click?"""

REFINE_5 = """Okay, it's time to finish up, and add an ad if you can. Add some content and better design if you can. Please insert one of those three ads somewhere."""


REFINES = [REFINE_1, REFINE_2, REFINE_PERSO, REFINE_4, REFINE_5]

def store_website_in_redis(key: str, website: str, messages: dict, response: str, iteration: int=0, start: bool = False):
    key = f"{key}:website"
    if start:
        redis_json = {}
        redis_json['website'] = {}
        redis_json['website']['v0'] = website
        redis_json['most_recent'] = 0
    else:
        redis_json = redis_retrieve(key)
        redis_json[f'v{iteration}'] = website
        redis_json['most_recent'] = iteration
    messages_to_store = messages + [{"role": "assistant", "content": response}]
    redis_json['messages'] = messages_to_store
    redis_store(key, redis_json)

def store_fetch_in_redis(key: str, start: bool = False):
    key = f"{key}:interaction"
    if start:
        redis_json = {}
        redis_json['interaction'] = 0
    else:
        redis_json = redis_retrieve(key)
        redis_json['interaction'] += 1
    redis_store(key, redis_json)

def generate_website(session_id: str):
    theme = ""
    type_ =""
    messages = [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": START_USER_MESSAGE.format(theme=theme, type_=type_)},
    ]

    response, website = _gpt(messages)
    store_fetch_in_redis(key=session_id, iteration=0, start=True)
    store_website_in_redis(key=session_id, website= website, messages= messages, response= response, iteration= 0, start= True)

    return website

def fetch_iteration(key: str):
    current_interaction = redis_retrieve(f"{key}:interaction")['interaction']
    current_website = redis_retrieve(f"{key}:website")[f"v{current_interaction}"]
    store_fetch_in_redis(key=key)
    return current_website

def parse_html(response):
    assert "```html" in response
    assert "```" in response.split("```html")[1]
    return response.split("```html")[1].split("```")[0]

def iterate_on_website(session_id: str):
    for i in range(0, len(REFINES)):
        iteration = i + 1
        prompt = redis_retrieve(f"{session_id}:website")['messages']
        prompt.append({"role": "user", "content": REFINES[i]})
        response, website = _gpt(prompt)
        store_website_in_redis(key=session_id, website= website, messages= prompt, response= response, iteration= iteration, start= False)