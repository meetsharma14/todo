import re
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, time
from pathlib import Path
from typing import Optional

import bcrypt
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "todo_pro.db"


# ================= PAGE =================

st.set_page_config(page_title="Todo Pro", page_icon="📝", layout="wide")


# ================= DB =================


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _db() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash BLOB NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                task TEXT NOT NULL,
                priority TEXT NOT NULL CHECK (priority IN ('High','Medium','Low')),
                created_at TEXT NOT NULL,
                deadline_at TEXT,
                status TEXT NOT NULL CHECK (status IN ('Pending','Completed')),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )


init_db()


# ================= SESSION =================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "page" not in st.session_state:
    st.session_state.page = "Inbox"


# ================= HELPERS =================


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _dt_label(dt: Optional[datetime]) -> str:
    if not dt:
        return "—"
    return dt.strftime("%d-%m-%Y %I:%M %p")


def _parse_iso(dt_s: Optional[str]) -> Optional[datetime]:
    if not dt_s:
        return None
    try:
        return datetime.fromisoformat(dt_s)
    except ValueError:
        return None


def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def verify_password(password: str, password_hash: bytes) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash)
    except ValueError:
        return False


@dataclass(frozen=True)
class User:
    id: int
    username: str
    email: str


def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    with _db() as conn:
        return conn.execute("SELECT * FROM users WHERE email = ?;", (email,)).fetchone()


def create_user(username: str, email: str, password: str) -> None:
    with _db() as conn:
        conn.execute(
            """
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?);
            """,
            (username, email, hash_password(password), _now_iso()),
        )


def authenticate(email: str, password: str) -> Optional[User]:
    row = get_user_by_email(email)
    if not row:
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return User(id=int(row["id"]), username=str(row["username"]), email=str(row["email"]))


def create_task(
    *,
    user_id: int,
    task: str,
    priority: str,
    deadline_at: Optional[datetime],
) -> None:
    with _db() as conn:
        conn.execute(
            """
            INSERT INTO tasks (user_id, task, priority, created_at, deadline_at, status)
            VALUES (?, ?, ?, ?, ?, 'Pending');
            """,
            (user_id, task, priority, _now_iso(), deadline_at.isoformat(timespec="seconds") if deadline_at else None),
        )


def list_tasks(user_id: int) -> list[sqlite3.Row]:
    with _db() as conn:
        return list(
            conn.execute(
                """
                SELECT *
                FROM tasks
                WHERE user_id = ?
                ORDER BY
                    CASE status WHEN 'Pending' THEN 0 ELSE 1 END,
                    CASE priority WHEN 'High' THEN 0 WHEN 'Medium' THEN 1 ELSE 2 END,
                    COALESCE(deadline_at, '9999-12-31T00:00:00'),
                    id DESC;
                """,
                (user_id,),
            ).fetchall()
        )


def toggle_task_status(task_id: int, user_id: int) -> None:
    with _db() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET status = CASE status WHEN 'Pending' THEN 'Completed' ELSE 'Pending' END
            WHERE id = ? AND user_id = ?;
            """,
            (task_id, user_id),
        )


def delete_task(task_id: int, user_id: int) -> None:
    with _db() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?;", (task_id, user_id))


# ================= CSS =================

st.markdown(
    """
<style>
.stApp{ background:#f5f6fa; }
#MainMenu{ visibility:hidden; }
footer{ visibility:hidden; }
[data-testid="stSidebar"]{
  background:white;
  border-right:1px solid #eaeaea;
}
.login-card{
  background:white;
  padding:35px;
  border-radius:25px;
  margin-top:60px;
  box-shadow:0px 4px 20px rgba(0,0,0,.08);
}
.metric{
  background:white;
  padding:20px;
  border-radius:15px;
  text-align:center;
  box-shadow:0px 2px 8px rgba(0,0,0,.05);
}
.task-card{
  background:white;
  padding:20px;
  border-radius:15px;
  margin-bottom:10px;
  border:1px solid #eee;
}
.stButton>button{
  width:100%;
  border-radius:10px;
  height:42px;
}
</style>
""",
    unsafe_allow_html=True,
)


# ================= LOGIN PAGE =================

if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1, 1.2, 1])

    with c2:
        st.markdown(
            """
            <div class='login-card'>
              <center>
                <h1>📝 Todo Pro</h1>
                <p>Organize work and life</p>
              </center>
            """,
            unsafe_allow_html=True,
        )

        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")

            if st.button("Login", key="login_btn"):
                email = email.strip().lower()
                if not email or not password:
                    st.error("Enter credentials")
                else:
                    user = authenticate(email, password)
                    if not user:
                        st.error("Invalid email or password")
                    else:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user.id
                        st.rerun()

        with tab2:
            username = st.text_input("Username", key="register_username").strip()
            reg_email = st.text_input("Email", key="register_email").strip().lower()
            reg_password = st.text_input("Password", type="password", key="register_password")
            confirm = st.text_input("Confirm Password", type="password", key="confirm_password")

            if st.button("Create Account", key="register_btn"):
                if not username:
                    st.error("Enter username")
                elif not reg_email or not EMAIL_RE.match(reg_email):
                    st.error("Enter a valid email")
                elif not reg_password:
                    st.error("Enter password")
                elif reg_password != confirm:
                    st.error("Passwords do not match")
                elif get_user_by_email(reg_email):
                    st.error("Email already registered")
                else:
                    create_user(username, reg_email, reg_password)
                    st.success("Account created. Please login.")

        st.markdown("</div>", unsafe_allow_html=True)


# ================= DASHBOARD =================

else:
    if not st.session_state.user_id:
        st.session_state.logged_in = False
        st.rerun()

    user_id = int(st.session_state.user_id)

    # Sidebar
    st.sidebar.title("📝 Todo Pro")

    if st.sidebar.button(" Inbox", use_container_width=True):
        st.session_state.page = "Inbox"

    if st.sidebar.button(" Important", use_container_width=True):
        st.session_state.page = "Important"

    if st.sidebar.button(" Today", use_container_width=True):
        st.session_state.page = "Today"

    if st.sidebar.button(" Projects", use_container_width=True):
        st.session_state.page = "Projects"

    st.sidebar.divider()

    if st.sidebar.button(" Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.rerun()

    st.title(st.session_state.page)

    # Load tasks (SQLite)
    tasks = list_tasks(user_id)

    # Metrics
    total = len(tasks)
    completed = sum(1 for t in tasks if t["status"] == "Completed")
    pending = total - completed

    a, b, c = st.columns(3)

    with a:
        st.markdown(
            f"""
            <div class='metric'>
              <h1>{total}</h1>
              Total Tasks
            </div>
            """,
            unsafe_allow_html=True,
        )

    with b:
        st.markdown(
            f"""
            <div class='metric'>
              <h1>{completed}</h1>
              Completed
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c:
        st.markdown(
            f"""
            <div class='metric'>
              <h1>{pending}</h1>
              Pending
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.progress(completed / total if total else 0)
    st.divider()

    # Add task
    task_name = st.text_input("Task Name", key="task").strip()

    c1, c2, c3 = st.columns([3, 2, 2])

    with c1:
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])

    with c2:
        deadline_date = st.date_input("Deadline Date", value=date.today())

    with c3:
        deadline_time = st.time_input("Deadline Time", value=time(23, 59))

    if st.button("Add Task"):
        if not task_name:
            st.error("Enter a task name")
        else:
            deadline_dt = datetime.combine(deadline_date, deadline_time)
            create_task(user_id=user_id, task=task_name, priority=priority, deadline_at=deadline_dt)
            st.rerun()

    st.divider()

    # Filters
    filtered: list[sqlite3.Row] = []
    today = date.today()

    for t in tasks:
        deadline_dt = _parse_iso(t["deadline_at"])
        deadline_d = deadline_dt.date() if deadline_dt else None

        if st.session_state.page == "Inbox":
            filtered.append(t)
        elif st.session_state.page == "Important" and t["priority"] == "High":
            filtered.append(t)
        elif st.session_state.page == "Today" and deadline_d == today:
            filtered.append(t)
        elif st.session_state.page == "Projects" and t["priority"] != "High":
            filtered.append(t)

    # Show Tasks
    for t in filtered:
        c1, c2, c3 = st.columns([8, 1, 1])

        with c1:
            icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}[t["priority"]]
            status_icon = "✅" if t["status"] == "Completed" else "⏳"

            created_dt = _parse_iso(t["created_at"])
            deadline_dt = _parse_iso(t["deadline_at"])

            st.markdown(
                f"""
                <div class='task-card'>
                  <b>{icon} {t["task"]}</b>
                  <br><br>
                  {status_icon}
                  <br><br>
                  Created: {_dt_label(created_dt)}
                  <br>
                  Deadline: {_dt_label(deadline_dt)}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            if st.button("✅", key=f"done{t['id']}"):
                toggle_task_status(int(t["id"]), user_id)
                st.rerun()

        with c3:
            if st.button("🗑️", key=f"delete{t['id']}"):
                delete_task(int(t["id"]), user_id)
                st.rerun()
