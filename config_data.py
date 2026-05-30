
# md5 list
md5_path = "./Data_Registry/md5.json"

# Chroma
collection_name = "welding_knowledges"
persist_directory = "Vector_Lib"

# spliter
chunk_size = 120 # 文本分割后的最大长度
chunk_overlap = 40 # 连续文本段之间的字符重叠数量
separators = ["\n\n", "\n", "。", "？", "！", ".", "?", "!"," ",""]


# retriever
top_k  = 6    #检索返回匹配的文档数量

# Chat Model
chat_model = "qwen2.5:7b"

# "qwen2.5:7b"
# "qwen3.5:9b"
# "qwen3-vl:4b"
# "qwen3-vl:235b-cloud"
# Embedding Model
embedding_model = "bge-m3"
# bge-m3
# nomic-embed-text
# shaw/dmeta-embedding-zh