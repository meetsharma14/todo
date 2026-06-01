import streamlit as st
import sqlite3
import bcrypt

# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title="Secure To-Do App",
    page_icon="📝"
)

# ---------------- DATABASE ---------------- #

conn = sqlite3.connect(
    "todo.db",
    check_same_thread=False
)

cursor = conn.cursor()

# Create users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password BLOB
)
""")

# Create tasks table
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    task TEXT,
    status TEXT
)
""")

conn.commit()


# ---------------- PASSWORD FUNCTIONS ---------------- #

def hash_password(password):

    salt = bcrypt.gensalt()

    hashed_password = bcrypt.hashpw(
        password.encode(),
        salt
    )

    return hashed_password


def verify_password(
        entered_password,
        stored_password
):

    return bcrypt.checkpw(
        entered_password.encode(),
        stored_password
    )


# ---------------- USER FUNCTIONS ---------------- #

def register_user(
        username,
        password
):

    try:

        hashed = hash_password(password)

        cursor.execute(
            """
            INSERT INTO users
            (username,password)
            VALUES (?,?)
            """,
            (
                username,
                hashed
            )
        )

        conn.commit()

        return True

    except:

        return False


def login_user(
        username,
        password
):

    cursor.execute(
        """
        SELECT id,password
        FROM users
        WHERE username=?
        """,
        (username,)
    )

    user = cursor.fetchone()

    if user:

        user_id = user[0]
        stored_password = user[1]

        if verify_password(
                password,
                stored_password
        ):

            return user_id

    return None


# ---------------- TASK FUNCTIONS ---------------- #

def add_task(
        user_id,
        task
):

    cursor.execute(
        """
        INSERT INTO tasks
        (user_id,task,status)
        VALUES (?,?,?)
        """,
        (
            user_id,
            task,
            "Pending"
        )
    )

    conn.commit()


def get_tasks(user_id):

    cursor.execute(
        """
        SELECT id,task,status
        FROM tasks
        WHERE user_id=?
        """,
        (user_id,)
    )

    return cursor.fetchall()


def toggle_task(
        task_id,
        status
):

    new_status = (
        "Completed"
        if status == "Pending"
        else "Pending"
    )

    cursor.execute(
        """
        UPDATE tasks
        SET status=?
        WHERE id=?
        """,
        (
            new_status,
            task_id
        )
    )

    conn.commit()


def delete_task(task_id):

    cursor.execute(
        """
        DELETE FROM tasks
        WHERE id=?
        """,
        (task_id,)
    )

    conn.commit()


# ---------------- SESSION ---------------- #

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None


# ---------------- LOGIN / REGISTER PAGE ---------------- #

if not st.session_state.logged_in:

    st.title("🔐 Secure To-Do App")

    page = st.sidebar.selectbox(
        "Choose",
        ["Login", "Register"]
    )

    username = st.text_input(
        "Username"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    if page == "Register":

        if st.button("Register"):

            if username and password:

                success = register_user(
                    username,
                    password
                )

                if success:

                    st.success(
                        "Registration successful"
                    )

                else:

                    st.error(
                        "Username already exists"
                    )

            else:

                st.warning(
                    "Fill all fields"
                )

    else:

        if st.button("Login"):

            user_id = login_user(
                username,
                password
            )

            if user_id:

                st.session_state.logged_in = True

                st.session_state.user_id = user_id

                st.success(
                    "Login successful"
                )

                st.rerun()

            else:

                st.error(
                    "Invalid username/password"
                )


# ---------------- TODO PAGE ---------------- #

else:

    st.title("📝 My To-Do List")

    if st.button("Logout"):

        st.session_state.logged_in = False
        st.session_state.user_id = None

        st.rerun()

    st.write("---")

    task = st.text_input(
        "Enter task"
    )

    if st.button(
            "Add Task"
    ):

        if task.strip() != "":

            add_task(
                st.session_state.user_id,
                task
            )

            st.success(
                "Task Added"
            )

            st.rerun()

    st.subheader(
        "Your Tasks"
    )

    tasks = get_tasks(
        st.session_state.user_id
    )

    if len(tasks) == 0:

        st.info(
            "No tasks available"
        )

    for task_id, task_text, status in tasks:

        col1, col2, col3 = st.columns(
            [5,2,2]
        )

        with col1:

            if status == "Completed":

                st.markdown(
                    f"~~{task_text}~~ ✅"
                )

            else:

                st.markdown(
                    f"{task_text} ⏳"
                )

        with col2:

            if st.button(
                    "Toggle",
                    key=f"toggle{task_id}"
            ):

                toggle_task(
                    task_id,
                    status
                )

                st.rerun()

        with col3:

            if st.button(
                    "Delete",
                    key=f"delete{task_id}"
            ):

                delete_task(
                    task_id
                )

                st.rerun()

    # Summary

    completed_count = sum(
        1 for task in tasks
        if task[2] == "Completed"
    )

    pending_count = sum(
        1 for task in tasks
        if task[2] == "Pending"
    )

    st.write("---")

    st.write(
        f"✅ Completed Tasks: {completed_count}"
    )

    st.write(
        f"⏳ Pending Tasks: {pending_count}"
    )
