import tkinter as tk  
from tkinter import messagebox
import requests
import uuid
import yaml


with open("config.yaml", "r") as f:
 config = yaml.safe_load(f)

SERVER_URL = config['URLS']['server_url'] 
CHECK_URL  = config['URLS']['check_url']

def get_mac_address():
    mac = uuid.getnode()
    return ':'.join(['{:02x}'.format((mac >> ele) & 0xff)
                     for ele in range(0, 8*6, 8)][::-1])

def fetch_absence_data():
    mac_address = get_mac_address()
    try:
        response = requests.post(CHECK_URL, json={"Mac_address": mac_address}, timeout=5)
        if response.status_code == 200:
            absent_days = response.json().get('total_absent_days', 0)
            remaining_days = 13 - absent_days
            
            absent_label.config(text=f"Days Absent: {absent_days}")
            remaining_label.config(text=f"Days Remaining: {remaining_days}")
            
            if remaining_days <= 3:
                remaining_label.config(fg="#e74c3c") 
            else:
                remaining_label.config(fg="#2ecc71")
    except Exception as e:
        absent_label.config(text="Days Absent: Connection Error")
        remaining_label.config(text="Days Remaining: --")

def submit_attendance():
    btn_submit.config(state=tk.DISABLED)
    status_label.config(text="Connecting to server...", fg="blue")
    root.update()

    mac_address = get_mac_address()
    data = {"Mac_address": mac_address}

    try:
        response = requests.post(SERVER_URL, json=data, timeout=10)
        result = response.json()
        
        if response.status_code == 200:
            status_label.config(text=f"✅ {result['message']}", fg="#2ecc71")
            messagebox.showinfo("Success", result['message'])
            fetch_absence_data() 
        else:
            status_label.config(text=f"❌ {result['message']}", fg="#e74c3c")
            messagebox.showerror("Error", result['message'])
            
    except Exception as e:
        status_label.config(text="❌ Connection Error", fg="#e74c3c")
        messagebox.showerror("Fail", f"Could not connect to server\n{e}")
    
    btn_submit.config(state=tk.NORMAL)

root = tk.Tk()
root.title("Elsewedy Attendance System")
root.geometry("400x450")
root.configure(bg="#f5f6fa")

main_frame = tk.Frame(root, bg="white", padx=20, pady=20, relief="groove", borderwidth=2)
main_frame.place(relx=0.5, rely=0.5, anchor="center")

tk.Label(main_frame, text="Student Attendance", font=("Arial", 16, "bold"), bg="white", fg="#2f3640").pack(pady=10)

info_frame = tk.Frame(main_frame, bg="#f9f9f9", padx=10, pady=10)
info_frame.pack(fill="x", pady=5)

absent_label = tk.Label(info_frame, text="Days Absent: --", font=("Arial", 10, "bold"), bg="#f9f9f9", fg="#34495e")
absent_label.pack()

remaining_label = tk.Label(info_frame, text="Days Remaining: --", font=("Arial", 10, "bold"), bg="#f9f9f9", fg="#2ecc71")
remaining_label.pack()

my_mac = get_mac_address()
tk.Label(main_frame, text=f"Your Device MAC:", font=("Arial", 9), bg="white", fg="#7f8c8d").pack(pady=(10,0))
tk.Label(main_frame, text=my_mac, font=("Courier", 10, "bold"), bg="#f1f2f6", fg="#2f3640").pack(pady=5)

status_label = tk.Label(main_frame, text="Ready to record", font=("Arial", 10), bg="white", fg="#7f8c8d")
status_label.pack(pady=10)

btn_submit = tk.Button(main_frame, text="REGISTER ATTENDANCE", command=submit_attendance, 
                       bg="#3498db", fg="white", font=("Arial", 10, "bold"), 
                       padx=20, pady=10, cursor="hand2", relief="flat")
btn_submit.pack(pady=10)

fetch_absence_data()

tk.Label(root, text="System Date: 2026-01-01", font=("Arial", 8), bg="#f5f6fa", fg="#95a5a6").pack(side="bottom", pady=5)

root.mainloop()