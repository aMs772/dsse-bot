import streamlit as st

from src.chatbot import get_response


st.set_page_config(
    page_title="IITB Department Assistant",
    page_icon="🎓"
)

st.title("IITB Department Assistant")
st.write("Ask questions about courses, the department, administration, and related topics.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

prompt = st.chat_input("Ask a question...")

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.write(prompt)

    answer = get_response(prompt, st.session_state.messages)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    with st.chat_message("assistant"):
        st.write(answer)

