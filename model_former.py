import json
import os

from torch import bfloat16
from transformers import AutoModelForCausalLM, AutoTokenizer

from multi_func import func_multiplier

from selectable_functions import Functions




class PatModel:
    def __init__(self, model_str: str):
        self.model_str = model_str
        self.model = None
        self.tokenizer = None
        self.path_to_prompt = None
        self.prompt = None
        self.tools = None
        self.multi_tools = None
        self.memory_cells = 3

    def load_model(self, path_to_prompt:str="prompt.txt", gpu:bool=True):
        self.path_to_prompt = path_to_prompt
        self.reload_prompt()
        self.reload_tools()

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_str,
            device_map="cuda" if gpu else "auto",
            torch_dtype=bfloat16# use float16 or float32 if bfloat16 is not available to you.
        )
        self.model.save_pretrained(r"patent_model/model")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_str,
            device_map="cuda" if gpu else "auto"
        )

    def model_step(self, history_message:list[dict[str:str]], multy_func:bool, tools:list[any]=None):
        inputs = self.tokenizer.apply_chat_template(
            history_message,
            tokenize=False,
            add_generation_prompt=True,  # adding prompt for generation
            tools=(self.multi_tools if multy_func else self.tools) if tools is None else tools
        )
        terminator_ids = [
            self.tokenizer.eos_token_id,
            self.tokenizer.convert_tokens_to_ids("<end_of_turn>"),
        ]
        prompt_ids = self.tokenizer.encode(inputs, add_special_tokens=False, return_tensors='pt').to(self.model.device)
        generated_ids = self.model.generate(
            prompt_ids,
            do_sample=True,
            temperature=0.2,
            top_k=40,
            top_p=0.95,
            min_p=0.5,
            max_new_tokens=512,
            eos_token_id=terminator_ids,
            bos_token_id=self.tokenizer.bos_token_id
        )

        generated_response = self.tokenizer.decode(generated_ids[0][prompt_ids.shape[-1]:], skip_special_tokens=False)
        return generated_response

    def get_response(self, message:str, path_to_history:str, multy_func:bool=False):
        history_messages = []
        generated_response = self.model_step([{"role": "user", "content": message}], multy_func)
        if "Вызов функции: {" in generated_response:
            generated_response = generated_response[generated_response.find('{'):generated_response.find('<')]
            response_dict = json.loads(generated_response)
            func = getattr(self, response_dict['name'])
            try:
                returnable_value = func(**response_dict['arguments'])
            except Exception as e:
                return 'Ошибка:\n' + str(e)
            history_messages.append({"role": "user", "content": message})
            if func.is_answer:
                generated_response = func.answer.replace("val", str(returnable_value))
            else:
                history_messages.append({"role": "function-call", "content": generated_response})
                history_messages.append({"role": "function-response", "content": str({func.name_returnable_value:
                                                                                          returnable_value})})
                generated_response = self.model_step(history_messages, multy_func)
                del history_messages[-1], history_messages[-1]
                generated_response = generated_response[:generated_response.find("<")]
            history_messages.append({"role": "model","content": generated_response})

            print(history_messages)
            messages_count = sum(1 for message in history_messages if message['role']=='user')
            if messages_count == self.memory_cells+1:
                del history_messages[1], history_messages[1]
            self.update_history(history_messages, path_to_history)
            return generated_response
        else:
            history_messages.append({"role": "user", "content": message})
            generated_response = generated_response[:generated_response.find('<')]
            history_messages.append({"role": "model", "content": generated_response})
            self.update_history(history_messages, path_to_history)
            return generated_response

    def reload_prompt(self):
        with open(self.path_to_prompt, "r", encoding='utf-8') as file:
            self.prompt = '\n'.join(file.readlines())

    def reload_tools(self):
        Functions.__init__(self)
        self.tools = [getattr(Functions(), func) for func in dir(Functions()) if callable(getattr(Functions(), func)) and not func.startswith("__")]
        #self.multi_tools = func_multiplier(self.tools)


    def clear_message_history(self, path_to_history:str):
        with open(path_to_history, 'w', encoding='utf-8') as file:
            history_messages = {'text': [{"role": "system",
                                "content": self.prompt}]}
            json.dump(history_messages, file, ensure_ascii=False)

    def get_history(self, path_to_history:str):
        if not os.path.exists(path_to_history):
            self.clear_message_history(path_to_history)
        with open(path_to_history, 'r', encoding='utf-8') as file:
            history_messages = json.load(file)['text']

        return history_messages

    def update_history(self, new_history_messages:list[dict[str:str]], path_to_history:str):
        history_messages = self.get_history(path_to_history)
        history_messages += new_history_messages
        with open(path_to_history, 'w', encoding='utf-8') as file:
            history_messages = {'text': history_messages}
            json.dump(history_messages, file, ensure_ascii=False)

    def reformat_history(self,):pass