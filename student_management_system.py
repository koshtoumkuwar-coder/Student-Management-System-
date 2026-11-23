import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import date

DB = "student_management.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,roll TEXT,class_name TEXT,phone TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY AUTOINCREMENT,student_id INTEGER,day TEXT,status TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS exams(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,class_name TEXT,total INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS results(id INTEGER PRIMARY KEY AUTOINCREMENT,student_id INTEGER,exam_id INTEGER,marks INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS fees(id INTEGER PRIMARY KEY AUTOINCREMENT,student_id INTEGER,amount REAL,day TEXT,status TEXT)")
conn.commit()

root = tk.Tk()
root.title("Student Management System")
root.geometry("1120x720")
root.minsize(850, 600)
root.configure(bg="#f4f7fb")

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", font=("Segoe UI", 10), rowheight=28, background="white", fieldbackground="white")
style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e8eef8", foreground="#24324b")
style.configure("TNotebook", background="#f4f7fb", borderwidth=0)
style.configure("TNotebook.Tab", padding=(14, 9), font=("Segoe UI", 10, "bold"))
style.configure("TButton", font=("Segoe UI", 10), padding=7)

# Header
header = tk.Frame(root, bg="#172b4d", height=95)
header.pack(fill="x")
header.pack_propagate(False)
tk.Label(header, text="🎓  STUDENT MANAGEMENT SYSTEM", font=("Segoe UI", 21, "bold"), bg="#172b4d", fg="white").pack(anchor="w", padx=24, pady=(17, 0))
tk.Label(header, text="Admission  •  Attendance  •  Examination  •  Results  •  Fees", font=("Segoe UI", 10), bg="#172b4d", fg="#c8d8f2").pack(anchor="w", padx=27, pady=3)

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=18, pady=16)

def page(name):
    frame = tk.Frame(notebook, bg="#f4f7fb")
    notebook.add(frame, text=name)
    return frame

def card(parent, title):
    f = tk.LabelFrame(parent, text=title, bg="white", fg="#24324b", font=("Segoe UI", 10, "bold"), padx=12, pady=12)
    f.pack(fill="x", padx=8, pady=8)
    return f

def tree(parent, columns, widths=None):
    wrap = tk.Frame(parent, bg="white")
    wrap.pack(fill="both", expand=True, padx=8, pady=8)
    t = ttk.Treeview(wrap, columns=columns, show="headings")
    for i, col in enumerate(columns):
        t.heading(col, text=col)
        t.column(col, width=(widths[i] if widths else 130), anchor="center")
    sb = ttk.Scrollbar(wrap, orient="vertical", command=t.yview)
    t.configure(yscrollcommand=sb.set)
    t.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return t

def student_list():
    cur.execute("SELECT id,name,roll,class_name,phone FROM students ORDER BY id DESC")
    return cur.fetchall()

def student_names():
    cur.execute("SELECT id,name,roll FROM students ORDER BY name")
    return [f"{i} | {n} ({r})" for i,n,r in cur.fetchall()]

def student_id_from(choice):
    try: return int(choice.split("|")[0].strip())
    except: return None

# Dashboard
p_dash = page("Dashboard")
dash_top = tk.Frame(p_dash, bg="#f4f7fb")
dash_top.pack(fill="x", padx=8, pady=14)
stat_cards = []
for title, color in [("Total Students", "#3b82f6"), ("Examinations", "#8b5cf6"), ("Fee Records", "#14b8a6")]:
    box = tk.Frame(dash_top, bg=color, height=100)
    box.pack(side="left", fill="x", expand=True, padx=7)
    box.pack_propagate(False)
    tk.Label(box, text=title, font=("Segoe UI", 11), bg=color, fg="white").pack(pady=(15, 2))
    value = tk.Label(box, text="0", font=("Segoe UI", 24, "bold"), bg=color, fg="white")
    value.pack()
    stat_cards.append(value)
summary = tk.Label(p_dash, text="Welcome! Use the tabs above to manage your school records.", font=("Segoe UI", 12), bg="#f4f7fb", fg="#44536a")
summary.pack(pady=24)

def refresh_dashboard():
    cur.execute("SELECT COUNT(*) FROM students"); stat_cards[0].config(text=cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM exams"); stat_cards[1].config(text=cur.fetchone()[0])
    cur.execute("SELECT COUNT(*) FROM fees"); stat_cards[2].config(text=cur.fetchone()[0])

# Admission
p_students = page("Student Admission")
form = card(p_students, "Add New Student")
fields = {}
for label in ["Full Name", "Roll Number", "Class", "Phone"]:
    row = tk.Frame(form, bg="white")
    row.pack(fill="x", pady=4)
    tk.Label(row, text=label, width=14, anchor="w", bg="white", font=("Segoe UI", 10)).pack(side="left")
    entry = ttk.Entry(row)
    entry.pack(side="left", fill="x", expand=True)
    fields[label] = entry
student_table = tree(p_students, ["ID", "Name", "Roll", "Class", "Phone"], [55, 210, 120, 100, 150])

def refresh_students():
    student_table.delete(*student_table.get_children())
    for row in student_list(): student_table.insert("", "end", values=row)
    refresh_choices()
    refresh_dashboard()

def add_student():
    vals = [fields[x].get().strip() for x in fields]
    if not all(vals):
        messagebox.showwarning("Missing information", "Please fill all student fields."); return
    cur.execute("INSERT INTO students(name,roll,class_name,phone) VALUES(?,?,?,?)", vals)
    conn.commit()
    for e in fields.values(): e.delete(0, "end")
    refresh_students(); messagebox.showinfo("Saved", "Student admitted successfully!")

def delete_student():
    sel = student_table.selection()
    if not sel: messagebox.showwarning("Select", "Select a student to delete."); return
    sid = student_table.item(sel[0], "values")[0]
    if messagebox.askyesno("Confirm", "Delete selected student record?"):
        cur.execute("DELETE FROM students WHERE id=?", (sid,)); conn.commit(); refresh_students()
btnrow = tk.Frame(form, bg="white"); btnrow.pack(fill="x", pady=(8, 0))
tk.Button(btnrow, text="➕  Add Student", command=add_student, bg="#2563eb", fg="white", relief="flat", padx=12, pady=7).pack(side="left")
tk.Button(btnrow, text="🗑  Delete Selected", command=delete_student, bg="#ef4444", fg="white", relief="flat", padx=12, pady=7).pack(side="left", padx=8)

# Attendance
p_att = page("Attendance")
att_form = card(p_att, "Mark Daily Attendance")
att_student = ttk.Combobox(att_form, state="readonly", width=45)
att_student.pack(side="left", padx=5, fill="x", expand=True)
att_status = ttk.Combobox(att_form, values=["Present", "Absent", "Late"], state="readonly", width=12)
att_status.set("Present"); att_status.pack(side="left", padx=5)
att_day = ttk.Entry(att_form, width=13); att_day.insert(0, str(date.today())); att_day.pack(side="left", padx=5)
tk.Button(att_form, text="Save Attendance", bg="#16a34a", fg="white", relief="flat", command=lambda: save_attendance()).pack(side="left", padx=5)
att_table = tree(p_att, ["ID", "Student", "Date", "Status"], [70, 250, 140, 140])
def refresh_att():
    att_table.delete(*att_table.get_children())
    cur.execute("SELECT attendance.id,students.name,attendance.day,attendance.status FROM attendance LEFT JOIN students ON students.id=attendance.student_id ORDER BY attendance.id DESC")
    for row in cur.fetchall(): att_table.insert("", "end", values=row)
def save_attendance():
    sid = student_id_from(att_student.get())
    if not sid or not att_day.get().strip(): messagebox.showwarning("Missing", "Choose a student and date."); return
    cur.execute("INSERT INTO attendance(student_id,day,status) VALUES(?,?,?)", (sid, att_day.get().strip(), att_status.get()))
    conn.commit(); refresh_att(); messagebox.showinfo("Saved", "Attendance saved.")

# Exams
p_exam = page("Examination")
exam_form = card(p_exam, "Create Examination")
exam_title = ttk.Entry(exam_form); exam_title.pack(side="left", fill="x", expand=True, padx=5); exam_title.insert(0, "Exam Name")
exam_class = ttk.Entry(exam_form, width=14); exam_class.pack(side="left", padx=5); exam_class.insert(0, "Class")
exam_total = ttk.Entry(exam_form, width=12); exam_total.pack(side="left", padx=5); exam_total.insert(0, "100")
tk.Button(exam_form, text="Add Exam", bg="#7c3aed", fg="white", relief="flat", command=lambda: add_exam()).pack(side="left", padx=5)
exam_table = tree(p_exam, ["ID", "Exam", "Class", "Total Marks"], [70, 260, 120, 120])
def refresh_exams():
    exam_table.delete(*exam_table.get_children()); cur.execute("SELECT * FROM exams ORDER BY id DESC")
    for row in cur.fetchall(): exam_table.insert("", "end", values=row)
def add_exam():
    try: total = int(exam_total.get())
    except: messagebox.showwarning("Invalid", "Total marks must be a number."); return
    if not exam_title.get().strip() or not exam_class.get().strip(): messagebox.showwarning("Missing", "Enter exam name and class."); return
    cur.execute("INSERT INTO exams(title,class_name,total) VALUES(?,?,?)", (exam_title.get().strip(), exam_class.get().strip(), total)); conn.commit(); refresh_exams(); refresh_choices(); refresh_dashboard(); messagebox.showinfo("Added", "Examination created.")

# Results
p_result = page("Results")
res_form = card(p_result, "Enter Student Result")
res_student = ttk.Combobox(res_form, state="readonly", width=38); res_student.pack(side="left", padx=5, fill="x", expand=True)
res_exam = ttk.Combobox(res_form, state="readonly", width=30); res_exam.pack(side="left", padx=5)
res_marks = ttk.Entry(res_form, width=12); res_marks.pack(side="left", padx=5); res_marks.insert(0, "Marks")
tk.Button(res_form, text="Save Result", bg="#0f766e", fg="white", relief="flat", command=lambda: save_result()).pack(side="left", padx=5)
res_table = tree(p_result, ["Student", "Exam", "Marks", "Percentage"], [220, 220, 100, 120])
def refresh_results():
    res_table.delete(*res_table.get_children())
    cur.execute("SELECT students.name,exams.title,results.marks,ROUND(results.marks*100.0/exams.total,1)||'%' FROM results JOIN students ON students.id=results.student_id JOIN exams ON exams.id=results.exam_id ORDER BY results.id DESC")
    for row in cur.fetchall(): res_table.insert("", "end", values=row)
def save_result():
    sid = student_id_from(res_student.get())
    try: marks = int(res_marks.get())
    except: messagebox.showwarning("Invalid", "Marks must be a number."); return
    try: eid = int(res_exam.get().split("|")[0].strip())
    except: messagebox.showwarning("Missing", "Choose an examination."); return
    cur.execute("SELECT total FROM exams WHERE id=?", (eid,)); row=cur.fetchone()
    if not sid or not row: messagebox.showwarning("Missing", "Select student and exam."); return
    if marks < 0 or marks > row[0]: messagebox.showwarning("Invalid marks", f"Marks must be between 0 and {row[0]}."); return
    cur.execute("INSERT INTO results(student_id,exam_id,marks) VALUES(?,?,?)", (sid,eid,marks)); conn.commit(); refresh_results(); messagebox.showinfo("Saved", "Result saved.")

# Fees
p_fees = page("Fee Management")
fee_form = card(p_fees, "Record Fee Payment")
fee_student = ttk.Combobox(fee_form, state="readonly", width=38); fee_student.pack(side="left", padx=5, fill="x", expand=True)
fee_amount = ttk.Entry(fee_form, width=13); fee_amount.pack(side="left", padx=5); fee_amount.insert(0, "Amount")
fee_day = ttk.Entry(fee_form, width=13); fee_day.pack(side="left", padx=5); fee_day.insert(0, str(date.today()))
fee_status = ttk.Combobox(fee_form, values=["Paid", "Pending"], state="readonly", width=12); fee_status.set("Paid"); fee_status.pack(side="left", padx=5)
tk.Button(fee_form, text="Save Fee", bg="#ea580c", fg="white", relief="flat", command=lambda: save_fee()).pack(side="left", padx=5)
fee_table = tree(p_fees, ["ID", "Student", "Amount (₹)", "Date", "Status"], [70, 220, 130, 130, 100])
def refresh_fees():
    fee_table.delete(*fee_table.get_children()); cur.execute("SELECT fees.id,students.name,fees.amount,fees.day,fees.status FROM fees LEFT JOIN students ON students.id=fees.student_id ORDER BY fees.id DESC")
    for row in cur.fetchall(): fee_table.insert("", "end", values=row)
def save_fee():
    sid = student_id_from(fee_student.get())
    try: amount = float(fee_amount.get())
    except: messagebox.showwarning("Invalid", "Enter a valid fee amount."); return
    if not sid or amount <= 0: messagebox.showwarning("Missing", "Choose student and enter a positive amount."); return
    cur.execute("INSERT INTO fees(student_id,amount,day,status) VALUES(?,?,?,?)", (sid,amount,fee_day.get().strip(),fee_status.get())); conn.commit(); refresh_fees(); refresh_dashboard(); messagebox.showinfo("Saved", "Fee record saved.")

# Refresh linked dropdowns
def refresh_choices():
    choices = student_names()
    for cb in [att_student, res_student, fee_student]:
        cb["values"] = choices
    cur.execute("SELECT id,title,class_name FROM exams ORDER BY id DESC")
    res_exam["values"] = [f"{i} | {t} - Class {c}" for i,t,c in cur.fetchall()]

refresh_students(); refresh_att(); refresh_exams(); refresh_results(); refresh_fees(); refresh_choices(); refresh_dashboard()

root.mainloop()
conn.close()
