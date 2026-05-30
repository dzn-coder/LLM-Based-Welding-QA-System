import os
import json
import config_data as config
import hashlib
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import Docx2txtLoader
from datetime import datetime

# 读取注册表中记录的字典
def load_md5_map(): 
    if not os.path.exists(config.md5_path): # 判断注册表是否存在
        return {}
    with open(config.md5_path, "r", encoding="utf-8") as f: # 读取注册表中记录的字典并返回
        return json.load(f)

# 将字典存入注册表中
def save_md5_map(md5_map):
    with open(config.md5_path, "w", encoding="utf-8") as f: # 将整个字典覆写到注册表中
        json.dump(md5_map, f, ensure_ascii=False, indent=2)

# 检查传入的md5字符串是否被记录过
def check_md5(md5_str: str):
    md5_map = load_md5_map()
    return md5_str in md5_map.values() # 匹配字典中的所有值

# 添加文件到注册表中
def save_md5(file_name: str, md5_str: str):
    md5_map = load_md5_map()
    md5_map[file_name] = md5_str
    save_md5_map(md5_map)

# 将传入的字符串转换成md5字符串
def get_string_md5(input_str: str):
    str_bytes = input_str.encode(encoding="utf-8")  # 将传入字符串编码为字节数组
    md5_obj = hashlib.md5()     # 创建md5对象
    md5_obj.update(str_bytes)   # 传入需要转化成md5的字节数组
    md5_hex = md5_obj.hexdigest()   # 得到md5的十六进制字符串
    return md5_hex


class DataLibService(object):
    def __init__(self) -> None:
        # 如果数据库文件夹不存在即创建
        os.makedirs(config.persist_directory, exist_ok=True)

        # 向量数据库对象
        self.chroma = Chroma(
            collection_name=config.collection_name, # 数据库表名
            embedding_function=OllamaEmbeddings(model=config.embedding_model),# 嵌入模型
            persist_directory=config.persist_directory, # 数据库本地存储文件夹
        )

        # 文本分割器对象
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size = config.chunk_size, # 分割文本段的最大长度
            chunk_overlap = config.chunk_overlap, #连续文本段之间的字符重叠数量
            separators = config.separators, # 自然段落划分的符号
            length_function = len
        )     

    # 将传入的字符串进行向量化,并存入向量数据库
    def upload_by_str(self, data: str, file_name):
        md5_hex = get_string_md5(data)
        if check_md5(md5_hex):
            return  "[跳过]内容已经存在向量库中"
        if len(data) > config.chunk_size:
            data_chunks = self.spliter.split_text(data) # 返回切分好的片段列表
        else:
            data_chunks = [data]

        meta_data = {
            "source": file_name,
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator": "邓振南"
        }

        # 将文本片段列表及其元数据存入数据库
        self.chroma.add_texts(
            data_chunks,
            metadatas=[meta_data for _ in data_chunks]# 描述信息
        )
        save_md5(file_name, md5_hex)
        return "[成功]内容已加载到向量库中"
    
    def upload_pdf(self, file_path, file_name):

        # ===== 1. 用 PDFLoader 读取（按页生成 Document）=====
        loader = PyPDFLoader(file_path=file_path, mode="page")
        docs = loader.load()

        # ===== 2. 拼接全文用于MD5去重 =====
        full_text = "\n".join([
            doc.page_content
            for doc in docs
            if doc.page_content and doc.page_content.strip()
        ])

        md5_hex = get_string_md5(full_text)

        # ===== 3. 去重判断 =====
        if check_md5(md5_hex):
            return "[跳过]内容已经存在向量库中"

        # ===== 4. 按语义切分=====
        split_docs = self.spliter.split_documents(docs)

        # ===== 5. 构造 metadata =====
        for doc in split_docs:
            doc.metadata.update({
                "source": file_name,
                "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "operator": "邓振南"
            })

        # ===== 6. 写入向量数据库 =====
        self.chroma.add_documents(split_docs)

        # ===== 7. 保存MD5 =====
        save_md5(file_name, md5_hex)

        return "[成功]PDF内容已加载到向量库中"
    
    # ===== 上传 Word 文档 =====
    def upload_word(self, file_path, file_name):

        # ===== 1. 读取 Word =====
        loader = Docx2txtLoader(file_path)
        docs = loader.load()

        # ===== 2. 拼接全文用于 MD5 =====
        full_text = "\n".join([
            doc.page_content
            for doc in docs
            if doc.page_content and doc.page_content.strip()
        ])

        md5_hex = get_string_md5(full_text)

        # ===== 3. 去重判断 =====
        if check_md5(md5_hex):
            return "[跳过]内容已经存在向量库中"

        # ===== 4. 文本切分 =====
        split_docs = self.spliter.split_documents(docs)

        # ===== 5. metadata =====
        for doc in split_docs:
            doc.metadata.update({
                "source": file_name,
                "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "operator": "邓振南"
            })

        # ===== 6. 写入向量库 =====
        self.chroma.add_documents(split_docs)

        # ===== 7. 保存MD5 =====
        save_md5(file_name, md5_hex)

        return "[成功]Word内容已加载到向量库中"
    

    def list_files(self):
        data = self.chroma.get(include=["metadatas"])

        if not data or "metadatas" not in data:
            return []

        file_set = set()

        for meta in data["metadatas"]:
            if meta and "source" in meta:
                file_set.add(meta["source"])

        return list(file_set)
    
    def delete_file(self, file_name):
        # 1. 删除向量库
        self.chroma.delete(where={"source": file_name})
        # 2. 删除 md5记录
        md5_map = load_md5_map()
        if file_name in md5_map:
            md5_map.pop(file_name)
        save_md5_map(md5_map)