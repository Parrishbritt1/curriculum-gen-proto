import os, sys
import urllib.request
from bs4 import BeautifulSoup
from openai import OpenAI
import json


OPENAI_SYSTEM_CONTENT = "You are a teaching assistant that provides learning curriculums. \
                            User will provide a topic they want to learn and you should provide a brief summary and \
                            the links to learning resources that you get from the supplied tools. \
                            Make sure that the links you provide don't have `page not found` in their content. \
                            Give a 6 question multiple choice quiz based on the content so that the user can test their knowledge. \
                            Provide the answers to the quiz questions as well."


def search_internet(search_query: str):
    print("GPT SEARCH QUERY: ", search_query)
    search_query = search_query.replace(" ", "+")
    html_content = urllib.request.urlopen(f"https://www.google.com/search?q={search_query}").read()
    soup = BeautifulSoup(html_content, features="html.parser")
    cleaned_text = soup.get_text()
    # print(cleaned_text)
    return cleaned_text

def main(learning_topic: str):
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_internet",
                "description": "Get current information on the topic the user wants to learn about. Call this for every user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_query": {
                            "type": "string",
                            "description": "The search query that is passed into the search engine. Used to find current information on the learning topic",
                        },
                    },
                    "required": ["search_query"],
                    "additionalProperties": False,
                }
            }
        }
    ]

    openai_api_key = os.getenv("OPENAI_API_KEY")

    client = OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "developer", "content": OPENAI_SYSTEM_CONTENT},
            {
                "role": "user",
                "content": f"I would like to learn about {learning_topic}"
            }
        ],
        tools=tools
    )

    if response.choices[0].message.tool_calls != None:
        tool_call = response.choices[0].message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)

        search_query = arguments.get('search_query')
        search_result = search_internet(search_query)

        function_call_result_message = {
            "role": "tool",
            "content": json.dumps({
                "search_query": search_query,
                "search_result": search_result
            }),
            "tool_call_id": response.choices[0].message.tool_calls[0].id
        }

        completion_payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": OPENAI_SYSTEM_CONTENT},
                {"role": "user", "content": f"{learning_topic}"},
                response.choices[0].message,
                function_call_result_message
            ]
        }

        response = client.chat.completions.create(
            model=completion_payload["model"],
            messages=completion_payload["messages"]
        )
        print(response.choices[0].message.content.strip())


if __name__ == "__main__":
    learning_topic = input("What topic do you want to learn? ")
    main(learning_topic)