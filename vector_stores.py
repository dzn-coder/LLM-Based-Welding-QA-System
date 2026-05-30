from langchain_chroma import Chroma
import config_data as config

class VectorStoreService:
    def __init__(self,embedding):
        self.embedding = embedding
        self.vector_store = Chroma( # 创建一个数据库对象
            collection_name=config.collection_name, # 集合名
            embedding_function=self.embedding,
            persist_directory=config.persist_directory # 向量数据库存储的路径
        )
    # 返回向量检索器对象
    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={"k": config.top_k}) # 检索器检索后会返回最相似的k条文档
    
