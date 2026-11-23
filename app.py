import sqlite3
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Student Management System", page_icon="🎓", layout="wide")
DB_PATH = Path(__file__).parent / "student_management.db"

def db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, roll TEXT UNIQUE NOT NULL, class_name TEXT NOT NULL, phone TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, day TEXT NOT NULL, status TEXT NOT NULL, UNIQUE(student_id,day))")
        c.execute("CREATE TABLE IF NOT EXISTS exams(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, class_name TEXT NOT NULL, total INTEGER NOT NULL)")
        c.execute("CREATE TABLE IF NOT EXISTS results(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, exam_id INTEGER NOT NULL, marks REAL NOT NULL, UNIQUE(student_id,exam_id))")
        c.execute("CREATE TABLE IF NOT EXISTS fees(id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, amount REAL NOT NULL, day TEXT NOT NULL, status TEXT NOT NULL)")
init_db()

def query(sql, params=()):
    with db() as c: return pd.read_sql_query(sql, c, params=params)
def execute(sql, params=()):
    with db() as c: c.execute(sql, params)
def students(): return query("SELECT id, name, roll, class_name AS 'Class', phone FROM students ORDER BY name")
def student_options():
    df=students()
    return {f"{r['name']} | Roll {r['roll']} | {r['Class']}":int(r['id']) for _,r in df.iterrows()}

# Styling
st.markdown("""<style>
.block-container{padding-top:1.6rem;padding-bottom:2rem;max-width:1400px}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#10213d,#172f52)}
[data-testid="stSidebar"] *{color:#f4f7ff}
.hero{padding:1.4rem 1.6rem;border-radius:18px;background:linear-gradient(110deg,#142b4d,#2360a5);color:white;margin-bottom:1rem}
.hero h1{margin:0;font-size:2rem}.hero p{color:#d8e7ff;margin:.35rem 0 0}
div[data-testid="stMetric"]{padding:14px;border:1px solid #e7edf5;border-radius:14px;background:#fff}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("# 🎓 SMS Portal")
    st.caption("Student Management System")
    page=st.radio("Navigation", ["Dashboard","Students","Attendance","Examinations","Results","Fee Management"], label_visibility="collapsed")
    st.divider()
    st.caption("Python • Streamlit • SQLite")
    st.caption("Academic project")

st.markdown('<div class="hero"><h1>🎓 Student Management System</h1><p>Manage admissions, attendance, exams, academic results and fee records in one place.</p></div>',unsafe_allow_html=True)

# Dashboard
if page=="Dashboard":
    s=students(); exam_count=int(query("SELECT COUNT(*) n FROM exams").iloc[0]['n']); fee_count=int(query("SELECT COUNT(*) n FROM fees").iloc[0]['n'])
    c1,c2,c3,c4=st.columns(4)
    c1.metric("👨‍🎓 Total Students",len(s)); c2.metric("📝 Examinations",exam_count); c3.metric("💳 Fee Records",fee_count); c4.metric("📋 Attendance Entries",int(query("SELECT COUNT(*) n FROM attendance").iloc[0]['n']))
    st.subheader("Quick overview")
    left,right=st.columns([1.3,1])
    with left:
        st.markdown("#### Recently registered students")
        st.dataframe(s.head(8),use_container_width=True,hide_index=True)
    with right:
        st.markdown("#### Fee payment status")
        f=query("SELECT status, COUNT(*) AS Records, SUM(amount) AS Amount FROM fees GROUP BY status")
        if f.empty: st.info("Fee records will appear here when added.")
        else: st.dataframe(f,use_container_width=True,hide_index=True)
        st.markdown("#### Attendance summary")
        a=query("SELECT status,COUNT(*) AS Entries FROM attendance GROUP BY status")
        if a.empty: st.info("Attendance records will appear here.")
        else: st.bar_chart(a.set_index("status"))
    st.info("Use the sidebar to open a module. Data is stored in the app's SQLite database file.")

# Students
elif page=="Students":
    st.subheader("Student admission & records")
    with st.expander("➕ Register a new student",expanded=True):
        with st.form("add_student",clear_on_submit=True):
            a,b=st.columns(2); name=a.text_input("Student name *"); roll=b.text_input("Roll number *")
            c,d=st.columns(2); cls=c.text_input("Class / Section *",placeholder="e.g. B.Tech CSE / 2A"); phone=d.text_input("Phone number")
            submitted=st.form_submit_button("Add student",type="primary",use_container_width=True)
            if submitted:
                if not name.strip() or not roll.strip() or not cls.strip(): st.error("Name, roll number and class are required.")
                else:
                    try: execute("INSERT INTO students(name,roll,class_name,phone) VALUES(?,?,?,?)",(name.strip(),roll.strip(),cls.strip(),phone.strip())); st.success("Student added successfully!"); st.rerun()
                    except sqlite3.IntegrityError: st.error("This roll number already exists.")
    df=students(); search=st.text_input("🔎 Search by name, roll, class or phone")
    if search: df=df[df.astype(str).apply(lambda row: row.str.contains(search,case=False,na=False).any(),axis=1)]
    st.dataframe(df.drop(columns=["id"],errors="ignore"),use_container_width=True,hide_index=True)
    if not df.empty:
        st.download_button("⬇️ Download student records (CSV)",df.to_csv(index=False).encode("utf-8"),"students.csv","text/csv")
        with st.expander("🗑️ Delete student record"):
            selected=st.selectbox("Select student",df.apply(lambda r:f"{r['name']} | Roll {r['roll']} (ID {r['id']})",axis=1))
            if st.button("Delete selected student",type="secondary"):
                sid=int(selected.split("ID ")[1].rstrip(")")); execute("DELETE FROM students WHERE id=?",(sid,)); execute("DELETE FROM attendance WHERE student_id=?",(sid,)); execute("DELETE FROM results WHERE student_id=?",(sid,)); execute("DELETE FROM fees WHERE student_id=?",(sid,)); st.success("Student and linked records removed."); st.rerun()

# Attendance
elif page=="Attendance":
    st.subheader("Attendance")
    opts=student_options()
    if not opts: st.info("Register students first to record attendance.")
    else:
        with st.form("attendance_form"):
            student=st.selectbox("Student",list(opts.keys())); day=st.date_input("Attendance date",value=date.today()); status=st.radio("Status",["Present","Absent","Late"],horizontal=True); save=st.form_submit_button("Save attendance",type="primary")
            if save:
                try: execute("INSERT INTO attendance(student_id,day,status) VALUES(?,?,?)",(opts[student],day.isoformat(),status)); st.success("Attendance saved."); st.rerun()
                except sqlite3.IntegrityError: st.warning("Attendance for this student and date already exists.")
    at=query("SELECT a.day AS Date,s.name AS Student,s.roll AS Roll,s.class_name AS Class,a.status AS Status FROM attendance a JOIN students s ON s.id=a.student_id ORDER BY a.day DESC")
    st.markdown("#### Attendance register"); st.dataframe(at,use_container_width=True,hide_index=True)
    if not at.empty: st.download_button("Download attendance CSV",at.to_csv(index=False).encode(),"attendance.csv","text/csv")

# Exams
elif page=="Examinations":
    st.subheader("Examination management")
    with st.form("exam_form"):
        x,y,z=st.columns(3); title=x.text_input("Exam name"); cls=y.text_input("Class / Section"); total=z.number_input("Maximum marks",min_value=1,value=100,step=1); save=st.form_submit_button("Create examination",type="primary")
        if save:
            if title.strip() and cls.strip(): execute("INSERT INTO exams(title,class_name,total) VALUES(?,?,?)",(title.strip(),cls.strip(),int(total))); st.success("Exam created."); st.rerun()
            else: st.error("Enter exam name and class.")
    exams=query("SELECT id,title AS 'Examination',class_name AS 'Class',total AS 'Maximum Marks' FROM exams ORDER BY id DESC")
    st.dataframe(exams.drop(columns=["id"],errors="ignore"),use_container_width=True,hide_index=True)
    if not exams.empty:
        with st.expander("Delete examination"):
            ex=st.selectbox("Select examination",exams.apply(lambda r:f"{r['Examination']} | {r['Class']} (ID {r['id']})",axis=1))
            if st.button("Delete exam"): eid=int(ex.split("ID ")[1].rstrip(")")); execute("DELETE FROM results WHERE exam_id=?",(eid,)); execute("DELETE FROM exams WHERE id=?",(eid,)); st.rerun()

# Results
elif page=="Results":
    st.subheader("Results & marks")
    opts=student_options(); ex=query("SELECT id,title,class_name,total FROM exams ORDER BY title")
    if not opts or ex.empty: st.info("Add students and create an examination first.")
    else:
        exam_labels={f"{r['title']} | {r['class_name']} | Max {r['total']} (ID {r['id']})":(int(r['id']),int(r['total'])) for _,r in ex.iterrows()}
        with st.form("result_form"):
            student=st.selectbox("Student",list(opts.keys())); exam_label=st.selectbox("Examination",list(exam_labels.keys())); maxmarks=exam_labels[exam_label][1]; marks=st.number_input("Marks obtained",min_value=0.0,max_value=float(maxmarks),step=1.0); save=st.form_submit_button("Save result",type="primary")
            if save:
                eid=exam_labels[exam_label][0]
                try: execute("INSERT INTO results(student_id,exam_id,marks) VALUES(?,?,?)",(opts[student],eid,marks)); st.success("Result saved."); st.rerun()
                except sqlite3.IntegrityError: st.warning("A result for this student and exam already exists. Delete the old record first.")
    res=query("SELECT s.name AS Student,s.roll AS Roll,s.class_name AS Class,e.title AS Examination,r.marks AS Marks,e.total AS 'Maximum Marks',ROUND(r.marks*100.0/e.total,2) AS 'Percentage' FROM results r JOIN students s ON s.id=r.student_id JOIN exams e ON e.id=r.exam_id ORDER BY e.title,s.name")
    st.markdown("#### Result register"); st.dataframe(res,use_container_width=True,hide_index=True)
    if not res.empty: st.download_button("Download results CSV",res.to_csv(index=False).encode(),"results.csv","text/csv")

# Fees
elif page=="Fee Management":
    st.subheader("Fee management")
    opts=student_options()
    if not opts: st.info("Register students first to add fees.")
    else:
        with st.form("fee_form"):
            student=st.selectbox("Student",list(opts.keys())); amount=st.number_input("Fee amount (₹)",min_value=0.0,step=100.0); day=st.date_input("Payment / record date",value=date.today()); status=st.selectbox("Payment status",["Paid","Pending","Partial"]); save=st.form_submit_button("Add fee record",type="primary")
            if save:
                if amount<=0: st.error("Amount must be greater than zero.")
                else: execute("INSERT INTO fees(student_id,amount,day,status) VALUES(?,?,?,?)",(opts[student],amount,day.isoformat(),status)); st.success("Fee record saved."); st.rerun()
    fees=query("SELECT s.name AS Student,s.roll AS Roll,s.class_name AS Class,f.amount AS 'Amount (₹)',f.day AS Date,f.status AS Status FROM fees f JOIN students s ON s.id=f.student_id ORDER BY f.day DESC")
    f1,f2,f3=st.columns(3); f1.metric("Total recorded (₹)",f"{fees['Amount (₹)'].sum():,.2f}" if not fees.empty else "0.00"); f2.metric("Paid (₹)",f"{fees.loc[fees['Status']=='Paid','Amount (₹)'].sum():,.2f}" if not fees.empty else "0.00"); f3.metric("Pending records",int((fees['Status']=='Pending').sum()) if not fees.empty else 0)
    st.markdown("#### Fee register"); st.dataframe(fees,use_container_width=True,hide_index=True)
    if not fees.empty: st.download_button("Download fee register CSV",fees.to_csv(index=False).encode(),"fees.csv","text/csv")

st.caption("Student Management System • Academic project • Built with Python, Streamlit & SQLite")
