from openai import OpenAI
from openai.types.beta import Thread, thread_create_params
import os
from typing import List
import time


class LLMEngine():

    def __init__(self):
        model = os.getenv("OPENAI_MODEL")
        asst_id = os.getenv("OPENAI_ASST_ID")

        if model is None or asst_id is None:
            raise Exception("Trouble getting model selection or assistant ID")

        self.__CLIENT = OpenAI()
        self.__WALARUS_ASST = self.__CLIENT.beta.assistants.retrieve(
            assistant_id=asst_id)
        self.__MODEL = model
        self.__LLM_THREAD = self.create_new_thread()

    def get_llm_response(self, input: str) -> str:
        self.__CLIENT.beta.threads.messages.create(
            thread_id=self.__LLM_THREAD.id,
            role="user",
            content=input
        )
        run = self.__CLIENT.beta.threads.runs.create(
            thread_id=self.__LLM_THREAD.id,
            assistant_id=self.__WALARUS_ASST.id
        )

        while run.status == "queued" or run.status == "in_progress":
            run = self.__CLIENT.beta.threads.runs.retrieve(
                thread_id=self.__LLM_THREAD.id, 
                run_id=run.id
            )
            time.sleep(0.5)

        messages = [message.content[0].text.value for message in self.__CLIENT.beta.threads.messages.list(
            thread_id=self.__LLM_THREAD.id, run_id=run.id)]
        return messages[0]

    def create_new_thread(self, messages: List[thread_create_params.Message] = []) -> Thread:
        return self.__CLIENT.beta.threads.create(messages=messages)
