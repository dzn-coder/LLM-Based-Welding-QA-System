import streamlit as st
import time
import tempfile
from rag import RagService
from file_history import get_history, FileChatMessageHistory
import config_data as config
from data_lib import DataLibService
from langchain_core.messages import HumanMessage, AIMessage
from session_store import load_sessions, save_sessions, delete_session
from langchain_community.document_loaders import PyPDFLoader
st.set_page_config(layout="wide")

# ================= 初始化 =================
if "rag" not in st.session_state:
    st.session_state["rag"] = RagService()

if "service" not in st.session_state:
    st.session_state["service"] = DataLibService()

if "session_list" not in st.session_state:
    st.session_state["session_list"] = load_sessions()

if "current_session" not in st.session_state:
    st.session_state["current_session"] = "默认会话"

# ================= 左侧 Sidebar =================
with st.sidebar:

    # ================= 知识库 =================
    with st.container(border=True): 
        st.header("知识库")

        upload_file = st.file_uploader("上传文件", type=["txt", "pdf", "docx"])
        txt = None
        tmp_path = None
        if upload_file:
            file_type = upload_file.type

            if file_type == "text/plain":
                txt = upload_file.getvalue().decode("utf-8")
            elif file_type == "application/pdf":
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(upload_file.getvalue())
                    tmp_path = tmp_file.name
            elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
                    tmp_file.write(upload_file.getvalue())
                    tmp_path = tmp_file.name

            if st.button("加入知识库"):
                if txt:
                    result = st.session_state["service"].upload_by_str(
                        txt,
                        upload_file.name
                    )

                elif tmp_path:
                    # ===== PDF =====
                    if upload_file.type == "application/pdf":
                        result = st.session_state["service"].upload_pdf(
                            tmp_path,
                            upload_file.name
                        )

                    # ===== Word =====
                    elif upload_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                        result = st.session_state["service"].upload_word(
                            tmp_path,
                            upload_file.name
                        )

                else:
                    result = "[失败]未识别文件类型或内容为空"
    
                st.success(result)

        st.divider()

    # ===== 初始化状态 =====
        if "show_files" not in st.session_state:
            st.session_state["show_files"] = True

        with st.expander("已有文件"):
            if st.session_state["show_files"]:
                files = st.session_state["service"].list_files()
                if not files:
                    st.write("暂无文件")
                else:
                    for f in files:
                        col1, col2 = st.columns([3, 1])
                        col1.write(f"{f}")
                        if col2.button("X", key=f):
                            st.session_state["service"].delete_file(f)
                            st.rerun()
        st.divider()

    # ================= 会话管理（新增）=================
    st.header("会话")

    # 切换会话
    selected = st.selectbox(
        "当前会话",
        st.session_state["session_list"],
        index=st.session_state["session_list"].index(st.session_state["current_session"])
    )

    st.session_state["current_session"] = selected

    # 新建会话
    new_session = st.text_input("新建会话名称")

    if st.button("➕ 新建会话"):
        if new_session and new_session not in st.session_state["session_list"]:
            st.session_state["session_list"].append(new_session)
            save_sessions(st.session_state["session_list"])
            st.session_state["current_session"] = new_session
            st.rerun()

# ================= 删除会话（新增）=================

    delete_session_name = st.selectbox(
        "选择要删除的会话",
        st.session_state["session_list"],
        key="delete_session_select"
    )

    if st.button("🗑️ 删除会话"):
        if delete_session_name == "默认会话":
            st.warning("默认会话不能删除")
        else:
            # 删除 session + 文件
            st.session_state["session_list"] = delete_session(
                delete_session_name,
                st.session_state["session_list"]
            )

            save_sessions(st.session_state["session_list"])

            # 如果删的是当前会话 → 回退
            if delete_session_name == st.session_state["current_session"]:
                st.session_state["current_session"] = "默认会话"

            st.rerun()
# ================= 主聊天区 =================
st.title("焊接工艺问答系统")
st.divider()

session = st.session_state["current_session"]
history = get_history(session)
messages = history.messages

# ===== 渲染历史 =====
for msg in messages:
    if msg.type == "human":
        st.chat_message("user").write(msg.content)
    else:
        st.chat_message("assistant").write(msg.content)

# ================= 输入 =================
prompt = st.chat_input("请输入问题...")

if prompt:
    st.chat_message("user").write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            
            session_config = {
                "configurable": {"session_id": st.session_state["current_session"],}
            }
            res = st.session_state["rag"].chain.stream(
                {"input": prompt},
                session_config
            )
            ai_text = st.write_stream(res)
