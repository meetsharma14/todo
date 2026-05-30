import streamlit as st

# Page settings
st.set_page_config(page_title="To-Do List", page_icon="📝")

# Title
st.title("📝 To-Do List App")

# Store tasks
if "tasks" not in st.session_state:
    st.session_state.tasks = []

# Input field
new_task = st.text_input("Enter a task")

# Add task
if st.button("Add Task"):
    if new_task.strip() != "":
        st.session_state.tasks.append({
            "task": new_task,
            "status": "Pending"
        })
        st.success("Task Added!")

# Display tasks
st.subheader("Your Tasks")

if len(st.session_state.tasks) == 0:
    st.info("No tasks available")

for index, item in enumerate(st.session_state.tasks):

    col1, col2, col3 = st.columns([5, 2, 2])

    # Task display
    with col1:
        if item["status"] == "Completed":
            st.markdown(
                f"~~{item['task']}~~ ✅ **Completed**"
            )
        else:
            st.markdown(
                f"{item['task']} ⏳ **Pending**"
            )

    # Toggle button
    with col2:
        if st.button("Toggle Status", key=f"toggle{index}"):

            if st.session_state.tasks[index]["status"] == "Pending":
                st.session_state.tasks[index]["status"] = "Completed"
            else:
                st.session_state.tasks[index]["status"] = "Pending"

            st.rerun()

    # Delete button
    with col3:
        if st.button("Delete", key=f"delete{index}"):
            st.session_state.tasks.pop(index)
            st.rerun()

# Summary
completed_count = sum(
    1 for task in st.session_state.tasks
    if task["status"] == "Completed"
)

pending_count = sum(
    1 for task in st.session_state.tasks
    if task["status"] == "Pending"
)

st.markdown("---")
st.write(f"✅ Completed Tasks: {completed_count}")
st.write(f"⏳ Pending Tasks: {pending_count}")