from langchain_core.chat_history import BaseChatMessageHistory
import os
import json
from typing import Sequence
from langchain_core.messages import BaseMessage, AIMessage, message_to_dict, messages_from_dict

def get_history(session_id): # 返回文件消息历史对象
    return FileChatMessageHistory(session_id, "./Chat_History")

class FileChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id, storage_path):
        self.session_id = session_id
        self.storage_path = storage_path
        self.file_path = os.path.join(self.storage_path, f"{self.session_id}.json")
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def add_message(self, messages) -> None:

        all_messages = list(self.messages)  # 已有的消息列表

        def flatten(msg):
            if isinstance(msg, BaseMessage):# 如果消息类型是BaseMessage
                return [msg]
            elif isinstance(msg, (tuple, list)):# 如果消息类型是tuple或list
                result = []
                for m in msg:
                    result.extend(flatten(m))
                return result
            else:
                # 其他类型（str）直接转 AIMessage
                return [AIMessage(content=str(msg))]

        new_msgs = flatten(messages)
        all_messages.extend(new_msgs)

        # 转 dict 并写入文件
        new_messages_dict = [message_to_dict(m) for m in all_messages]
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(new_messages_dict, f, ensure_ascii=False, indent=2)
        
    @property
    def messages(self) -> list[BaseMessage]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                messages_data = json.load(f)
                return messages_from_dict(messages_data)
        except FileNotFoundError:
            return []

    def clear(self) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump([], f)