from bw_secrets import OPENAI_MODEL, OPENAI_ASST_ID
import discord
import logging
from openai import OpenAI
from openai.types.beta import Thread, thread_create_params
import os
from typing import List, Optional
import time


class LLMEngine():

    FAILURE_MESSAGE = "Sorry, I kinda just shat maself"

    def __init__(self):
        self.log: logging.Logger = logging.getLogger(f"{__name__}.LLMEngine")

        if OPENAI_MODEL is None or OPENAI_ASST_ID is None:
            self.log.error("Trouble getting model selection or assistant ID")
            raise Exception("Trouble getting model selection or assistant ID")

        self.__CLIENT = OpenAI()
        self.__WALARUS_ASST = self.__CLIENT.beta.assistants.retrieve(
            assistant_id=OPENAI_ASST_ID)
        self.__MODEL = OPENAI_MODEL
        self.__LLM_THREAD = self.create_new_thread()

    def _wait_for_run_completion(
        self,
        thread_id: str,
        run_id: str,
        timeout: float = 120.0,
        poll_interval: float = 0.5,
    ) -> str:
        """Polls the run until it reaches a terminal state and returns the final status.

        Terminal statuses include: 'completed', 'failed', 'cancelled', 'expired', 'requires_action'.
        """
        start = time.time()
        status = "queued"
        while True:
            run = self.__CLIENT.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            status = getattr(run, "status", None) or "unknown"
            if status not in ("queued", "in_progress"):
                return status
            if time.time() - start > timeout:
                return "timeout"
            time.sleep(poll_interval)

    def _extract_text_from_message(self, message) -> str:
        """Extracts text from a message, concatenating all text parts if present."""
        parts: List[str] = []
        for block in getattr(message, "content", []) or []:
            block_type = getattr(block, "type", None)
            if block_type == "text":
                text_obj = getattr(block, "text", None)
                value = getattr(text_obj, "value", None) if text_obj else None
                if value:
                    parts.append(value)
        return "\n".join(parts).strip()

    def _get_latest_assistant_text(self, thread_id: str) -> Optional[str]:
        """Returns the latest assistant message text in the thread, if any."""
        msgs = self.__CLIENT.beta.threads.messages.list(
            thread_id=thread_id,
            order="desc",
            limit=20,
        )
        # Iterate through the latest messages to find the most recent assistant response
        for msg in getattr(msgs, "data", []) or []:
            if getattr(msg, "role", None) == "assistant":
                text = self._extract_text_from_message(msg)
                if text:
                    return text
        return None

    def get_llm_response(self, author: discord.Member, input: str) -> str:
        user_text = f"from {author.name}: {input}"
        # Add user message to the thread
        self.__CLIENT.beta.threads.messages.create(
            thread_id=self.__LLM_THREAD.id,
            role="user",
            content=user_text,
        )
        # Start a run for the assistant
        run = self.__CLIENT.beta.threads.runs.create(
            thread_id=self.__LLM_THREAD.id,
            assistant_id=self.__WALARUS_ASST.id,
        )

        # Wait until the run is completed or another terminal state
        final_status = self._wait_for_run_completion(
            self.__LLM_THREAD.id, run.id)

        if final_status == "completed":
            # Fetch the latest assistant message safely
            text = self._get_latest_assistant_text(self.__LLM_THREAD.id)
            if text:
                return text
            self.log.error("Received no text from assistant")
            return LLMEngine.FAILURE_MESSAGE
        elif final_status in ("requires_action", "failed", "cancelled", "expired", "timeout"):
            self.log.error(
                "Got a non-'completed' status from AI assistant: status=%s", final_status)
            return LLMEngine.FAILURE_MESSAGE
        else:
            # Unknown status safeguard
            return LLMEngine.FAILURE_MESSAGE

    def create_new_thread(
        self,
        messages: Optional[List[thread_create_params.Message]] = None,
    ) -> Thread:
        return self.__CLIENT.beta.threads.create(messages=messages or [])
