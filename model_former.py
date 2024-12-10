import asyncio
import json
import os

import httpx
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageToolCall
from openai.types.chat.chat_completion import Choice

from selectable_functions import Functions
from openai import AsyncOpenAI
from transformers.utils import get_json_schema  # (choices: ["tea", "coffee"]) для аргументов

ChatCompletionMessage.model_config['from_attributes']=True




class PatModel:
    def __init__(self, api_key: str, proxy: str, path_to_prompt:str="prompt.txt") -> None:
        self.api_key = api_key
        self.proxy = proxy
        self.path_to_prompt = path_to_prompt
        self.prompt = None
        self.tools = None
        self.client = None
        self.model = None
        self.memory_cells = None

    def load_model(self, model:str, memory_cells:int) -> None:
        self.reload_prompt()
        self.reload_tools()
        self.client = AsyncOpenAI(http_client=httpx.AsyncClient(proxy=self.proxy, timeout=35),api_key=self.api_key)
        self.model = model
        self.memory_cells = memory_cells

    async def model_step(self, history_message: list[dict[str: str]]) -> Choice:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=history_message,
            tools=self.tools
        )
        return response.choices[0]

    async def get_response(self, message:str, path_to_history:str) -> str:
        history_messages = self.get_history(path_to_history)
        history_messages.append({"role": "user", "content": message})
        generated_response = await self.model_step(history_messages)

        if generated_response.finish_reason == 'tool_calls':
            try:
                funcs_result = await self.all_func_run(generated_response.message.tool_calls)
            except Exception as e:
                return 'Ошибка:\n' + str(e)
            history_messages.append(generated_response.message)
            history_messages += funcs_result

            generated_response = await self.model_step(history_messages)

        history_messages.append({"role": "assistant", "content": generated_response.message.content})
        for idx in range(len(history_messages)):
            if type(history_messages[idx]) != dict:
                history_messages[idx] = history_messages[idx].to_dict()
                history_messages[idx]["to_dict_product"] = 1
        user_messages_count = sum(1 for message in history_messages if message['role'] == 'user')
        if user_messages_count == self.memory_cells + 1:
            del history_messages[1]
            while history_messages[1]['role'] != 'user':
                del history_messages[1]
        self.update_history(history_messages, path_to_history)
        return generated_response.message.content

    async def all_func_run(self, functions: list[ChatCompletionMessageToolCall]) -> list[dict[str:str]]:
        tasks = []
        for func in functions:
            tasks.append(
                asyncio.create_task(getattr(Functions(), func.function.name)(**json.loads(func.function.arguments))))
        await asyncio.gather(*tasks)
        ret_values = [task.result() for task in tasks]
        final = []
        for ret_value, func in zip(ret_values, functions):
            final.append({
                "role": "tool",
                "content": json.dumps(json.loads(func.function.arguments) |
                                      {f"{getattr(Functions(), func.function.name).ret_value_name}": ret_value},
                                      ensure_ascii=False),
                "name": func.function.name,
                "tool_call_id": func.id
            })
        return final

    def reload_prompt(self) -> None:
        with open(self.path_to_prompt, "r", encoding='utf-8') as file:
            self.prompt = '\n'.join(file.readlines())

    def reload_tools(self) -> None:
        Functions.__init__(self)
        self.tools = [get_json_schema(getattr(Functions(), func)) for func in dir(Functions())
                      if callable(getattr(Functions(), func)) and not func.startswith("__")]


    def clear_message_history(self, path_to_history:str) -> None :
        with open(path_to_history, 'w', encoding='utf-8') as file:
            history_messages = [{"role": "system", "content": self.prompt}]
            json.dump(history_messages, file, ensure_ascii=False)

    def get_history(self, path_to_history:str) -> list[dict[str:str]]:
        if not os.path.exists(path_to_history):
            self.clear_message_history(path_to_history)
        with open(path_to_history, 'r', encoding='utf-8') as file:
            history_messages = json.load(file)
        for idx in range(len(history_messages)):
            if history_messages[idx].get("to_dict_product", 0):
                history_messages[idx] = ChatCompletionMessage.model_validate(history_messages[idx])
        return history_messages

    def update_history(self, history_messages:list[dict[str: str]], path_to_history:str):
        with open(path_to_history, 'w', encoding='utf-8') as file:
            json.dump(history_messages, file, ensure_ascii=False)