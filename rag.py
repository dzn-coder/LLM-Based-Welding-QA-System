from vector_stores import VectorStoreService
from langchain_ollama import OllamaEmbeddings
import config_data as config
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory, RunnableLambda, RunnableConfig
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from file_history import get_history
from langchain_core.messages import AIMessage


def print_prompt(prompt):
    print("="*20)
    # ChatPromptValue -> string
    if hasattr(prompt, "to_string"):
        content_str = prompt.to_string()
    else:
        content_str = str(prompt)
    # print(content_str)
    return content_str  # 返回字符串给 ChatOllama

class RagService:
    def __init__(self):
        self.vector_service = VectorStoreService(
            embedding=OllamaEmbeddings(model=config.embedding_model)
        )
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system",
                    """
                    你是一个焊接领域的专家。
                    你的任务是：根据用户提到的内容，并结合参考资料：{context}，
                    来回答用户提问。
                    需要严格按照下面的格式输出：
                    ##### 问题分析：
                    对问题进行分析，并结合参考资料解释原因。
                    ##### 结果总结：
                    简洁总结最终答案。
                    ##### 知识来源：
                    列出回答中所用到的知识的文件名来源，如果指出页码就给页码，没有就不给。
                """),
                ("system","可结合用户的对话历史记录,如下:"),
                MessagesPlaceholder("history"),
                ("user","用户提问：{input}")
            ]
        )
        self.chat_model = ChatOllama(model=config.chat_model)
        self.chain = self.__get_chain()
    
    def __get_chain(self):
        retriever = self.vector_service.get_retriever()

        def format_document(docs: list[Document]):
            if not docs:
                return "无相关参考资料"
            formatted_str = ""
            for doc in docs:
                formatted_str += f"文档片段：{doc.page_content}\n文档元数据：{doc.metadata}\n\n"
            return formatted_str
        
        def temp1(value: dict) -> str:
            return value["input"]
        
        def temp2(value)->dict:
            new_value = {}
            new_value["input"] = value["input"]["input"]
            new_value["context"] = value["context"]
            new_value["history"] = value["input"]["history"]
            return new_value

        chain = (
            {
                "input": RunnablePassthrough(),
                "context": RunnableLambda(temp1)| retriever | format_document 
            } | RunnableLambda(temp2) |self.prompt_template | self.chat_model| StrOutputParser()
        )

        conversation_chain = RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key="input",
            history_messages_key="history",
        )
        return conversation_chain
    
if __name__ == "__main__":
    session_config = {
        "configurable": {"session_id": "user_01",}
    }
    res = RagService().chain.invoke({"input":"我刚才问的什么问题?"},session_config) # type: ignore

    print(res)