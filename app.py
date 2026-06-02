import streamlit as st
from datetime import datetime, date

# ================= PAGE =================

st.set_page_config(
    page_title="Todo Pro",
    page_icon="📝",
    layout="wide"
)

# ================= SESSION =================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "page" not in st.session_state:
    st.session_state.page = "Inbox"


# ================= CSS =================

st.markdown("""
<style>

.stApp{
background:#f5f6fa;
}

#MainMenu{
visibility:hidden;
}

footer{
visibility:hidden;
}

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
""", unsafe_allow_html=True)

# ================= LOGIN PAGE =================

if not st.session_state.logged_in:

    c1,c2,c3=st.columns([1,1.2,1])

    with c2:

        st.markdown("""

        <div class='login-card'>

        <center>
        <h1>📝 Todo Pro</h1>
        <p>Organize work and life</p>
        </center>

        """, unsafe_allow_html=True)

        tab1,tab2=st.tabs(
            ["Login","Register"]
        )

        with tab1:

            email=st.text_input(
                "Email",
                key="login_email"
            )

            password=st.text_input(
                "Password",
                type="password",
                key="login_password"
            )

            if st.button(
                "Login",
                key="login_btn"
            ):

                if email and password:

                    st.session_state.logged_in=True
                    st.rerun()

                else:

                    st.error(
                        "Enter credentials"
                    )

        with tab2:

            username=st.text_input(
                "Username",
                key="register_username"
            )

            reg_email=st.text_input(
                "Email",
                key="register_email"
            )

            reg_password=st.text_input(
                "Password",
                type="password",
                key="register_password"
            )

            confirm=st.text_input(
                "Confirm Password",
                type="password",
                key="confirm_password"
            )

            if st.button(
                "Create Account",
                key="register_btn"
            ):

                if reg_password!=confirm:

                    st.error(
                        "Passwords do not match"
                    )

                else:

                    st.success(
                        "Account created"
                    )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )


# ================= DASHBOARD =================

else:

    # Sidebar

    st.sidebar.title(
        "📝 Todo Pro"
    )

    if st.sidebar.button(
        "📥 Inbox",
        use_container_width=True
    ):
        st.session_state.page="Inbox"

    if st.sidebar.button(
        "⭐ Important",
        use_container_width=True
    ):
        st.session_state.page="Important"

    if st.sidebar.button(
        "📅 Today",
        use_container_width=True
    ):
        st.session_state.page="Today"

    if st.sidebar.button(
        "📁 Projects",
        use_container_width=True
    ):
        st.session_state.page="Projects"

    st.sidebar.divider()

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):
        st.session_state.logged_in=False
        st.rerun()


    st.title(
        st.session_state.page
    )


    # Metrics

    total=len(st.session_state.tasks)

    completed=sum(
        1 for t in st.session_state.tasks
        if t["status"]=="Completed"
    )

    pending=total-completed


    a,b,c=st.columns(3)

    with a:

        st.markdown(
        f"""
        <div class='metric'>
        <h1>{total}</h1>
        Total Tasks
        </div>
        """,
        unsafe_allow_html=True
        )

    with b:

        st.markdown(
        f"""
        <div class='metric'>
        <h1>{completed}</h1>
        Completed
        </div>
        """,
        unsafe_allow_html=True
        )

    with c:

        st.markdown(
        f"""
        <div class='metric'>
        <h1>{pending}</h1>
        Pending
        </div>
        """,
        unsafe_allow_html=True
        )

    st.progress(
        completed/total if total else 0
    )

    st.divider()


    # Add task

    task=st.text_input(
        "Task Name",
        key="task"
    )

    c1,c2,c3=st.columns([3,2,2])

    with c1:

        priority=st.selectbox(
            "Priority",
            ["High","Medium","Low"]
        )

    with c2:

        deadline_date=st.date_input(
            "Deadline Date",
            value=date.today()
        )

    with c3:

        deadline_time=st.time_input(
            "Deadline Time"
        )

    if st.button(
        "Add Task"
    ):

        current=datetime.now().strftime(
            "%d-%m-%Y %I:%M %p"
        )

        deadline=datetime.combine(
            deadline_date,
            deadline_time
        ).strftime(
            "%d-%m-%Y %I:%M %p"
        )

        st.session_state.tasks.append({

            "task":task,
            "priority":priority,
            "created":current,
            "deadline":deadline,
            "status":"Pending"

        })

        st.rerun()

    st.divider()


    # Filters

    filtered=[]

    for t in st.session_state.tasks:

        if st.session_state.page=="Inbox":

            filtered.append(t)

        elif (
            st.session_state.page=="Important"
            and t["priority"]=="High"
        ):

            filtered.append(t)

        elif (
            st.session_state.page=="Today"
            and t["deadline"][:10]
            ==
            datetime.now().strftime(
                "%d-%m-%Y"
            )
        ):

            filtered.append(t)

        elif (
            st.session_state.page=="Projects"
            and t["priority"]!="High"
        ):

            filtered.append(t)


    # Show Tasks

    for i,t in enumerate(filtered):

        c1,c2,c3=st.columns(
            [8,1,1]
        )

        with c1:

            icon={

                "High":"🔴",
                "Medium":"🟡",
                "Low":"🟢"

            }[t["priority"]]

            status=(
                "✅"
                if t["status"]=="Completed"
                else "⏳"
            )

            st.markdown(
            f"""
            <div class='task-card'>

            <b>{icon} {t["task"]}</b>

            <br><br>

            {status}

            <br><br>

            Created:
            {t["created"]}

            <br>

            Deadline:
            {t["deadline"]}

            </div>
            """,
            unsafe_allow_html=True
            )


        with c2:

            if st.button(
                "✅",
                key=f"done{i}"
            ):

                t["status"]=(
                    "Completed"
                    if t["status"]=="Pending"
                    else "Pending"
                )

                st.rerun()


        with c3:

            if st.button(
                "🗑️",
                key=f"delete{i}"
            ):

                st.session_state.tasks.remove(t)

                st.rerun()
