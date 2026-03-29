import tkinter as tk
from tkinter import messagebox, Toplevel, ttk
import time
import csv
import json
import os
from datetime import datetime
import winsound
import threading

# 1. حساب السعر حسب اليوم
def get_price_per_min():
    today = datetime.now().strftime('%A')
    return 1.5 if today in ['Thursday', 'Friday'] else 1.0

class KidsCenterPro:
    def __init__(self, root):
        self.root = root
        self.root.title("🟢 نظام كيدز ايريا وشوشني - الإصدار الاحترافي")
        self.root.geometry("1000x750")
        self.root.config(bg="#f0f2f5")

        self.kids = {} 
        self.total_revenue = 0.0 
        self.temp_file = "active_session.json" # ملف حماية البيانات من انقطاع الكهرباء
        
        self.setup_ui()
        self.load_previous_session() # استعادة الأطفال لو البرنامج قفل فجأة
        self.update_clock()

    def setup_ui(self):
        # --- العنوان العلوي ---
        header_frame = tk.Frame(self.root, bg="#03045e", height=80)
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="👁️ كيدز ايريا وشوشني - المحاسب الذكي 👁️", 
                 font=("Arial", 24, "bold"), bg="#03045e", fg="white").pack(pady=10)

        # --- منطقة التحكم ---
        control_frame = tk.Frame(self.root, bg="#f0f2f5")
        control_frame.pack(pady=10, fill=tk.X, padx=20)

        btns_frame = tk.Frame(control_frame, bg="#f0f2f5")
        btns_frame.pack(side=tk.TOP, pady=5)

        tk.Button(btns_frame, text="➕ تسجيل دخول طفل", font=("Arial", 11, "bold"), 
                  bg="#00b4d8", fg="white", width=20, height=2, command=self.open_add_kid_window).grid(row=0, column=0, padx=10)
        
        tk.Button(btns_frame, text="💳 خروج وحساب", font=("Arial", 11, "bold"), 
                  bg="#ef233c", fg="white", width=20, height=2, command=self.check_out_selected).grid(row=0, column=1, padx=10)

        # --- شريط البحث ---
        search_frame = tk.Frame(control_frame, bg="#f0f2f5")
        search_frame.pack(side=tk.TOP, pady=10)
        tk.Label(search_frame, text="🔍 بحث عن اسم:", font=("Arial", 11), bg="#f0f2f5").grid(row=0, column=0, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_table)
        self.search_ent = tk.Entry(search_frame, textvariable=self.search_var, font=("Arial", 12), width=30)
        self.search_ent.grid(row=0, column=1)

        # --- الجدول ---
        style = ttk.Style()
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("Treeview", font=("Arial", 11), rowheight=30)

        self.tree = ttk.Treeview(self.root, columns=("name", "booked", "time", "price"), show='headings')
        self.tree.heading("name", text="اسم الطفل")
        self.tree.heading("booked", text="المدة المحجوزة")
        self.tree.heading("time", text="الوقت المتبقي")
        self.tree.heading("price", text="الحساب الحالي")
        
        for col in ("name", "booked", "time", "price"):
            self.tree.column(col, anchor="center", width=150)
        self.tree.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        # --- الإيرادات ---
        self.revenue_frame = tk.Frame(self.root, bg="#03045e", bd=2, relief=tk.RAISED)
        self.revenue_frame.pack(pady=10, side=tk.BOTTOM)
        self.rev_label = tk.Label(self.revenue_frame, text=f"إجمالي الإيرادات: {self.total_revenue} EGP", 
                                 font=("Arial", 16, "bold"), bg="#03045e", fg="#00f5d4", padx=20, pady=5)
        self.rev_label.pack()

    # --- وظائف حماية البيانات ---
    def save_session_to_disk(self):
        with open(self.temp_file, "w", encoding="utf-8") as f:
            json.dump(self.kids, f, ensure_ascii=False)

    def load_previous_session(self):
        if os.path.exists(self.temp_file):
            try:
                with open(self.temp_file, "r", encoding="utf-8") as f:
                    self.kids = json.load(f)
                self.filter_table()
            except: pass

    # --- وظائف الإضافة ---
    def open_add_kid_window(self):
        self.add_win = Toplevel(self.root)
        self.add_win.title("إضافة طفل")
        self.add_win.geometry("300x250")
        self.add_win.grab_set()

        tk.Label(self.add_win, text="اسم الطفل:").pack(pady=5)
        self.name_ent = tk.Entry(self.add_win, font=("Arial", 12))
        self.name_ent.pack()
        self.name_ent.focus_set()
        self.name_ent.bind('<Return>', lambda e: self.time_ent.focus_set())

        tk.Label(self.add_win, text="الدقائق:").pack(pady=5)
        self.time_ent = tk.Entry(self.add_win, font=("Arial", 12))
        self.time_ent.pack()
        self.time_ent.bind('<Return>', lambda e: self.save_kid())

        tk.Button(self.add_win, text="حفظ (Enter)", command=self.save_kid, bg="#00b4d8", fg="white", width=15).pack(pady=20)

    def save_kid(self):
        name = self.name_ent.get().strip()
        mins = self.time_ent.get().strip()
        if name and mins.isdigit():
            kid_id = "ID" + str(time.time())
            self.kids[kid_id] = {"name": name, "booked": int(mins), "start": time.time(), "notified": False}
            self.save_session_to_disk() # حفظ فوري للملف المؤقت
            self.filter_table()
            self.add_win.destroy()
        else:
            messagebox.showerror("خطأ", "بيانات غير صحيحة")

    def filter_table(self, *args):
        search_term = self.search_var.get().lower()
        for item in self.tree.get_children(): self.tree.delete(item)
        for kid_id, data in self.kids.items():
            if search_term in data["name"].lower():
                self.tree.insert("", "end", iid=kid_id, values=(data["name"], f"{data['booked']} دقيقة", "00:00", "0 EGP"))

    def update_clock(self):
        now = time.time()
        price_rate = get_price_per_min()
        for kid_id, data in list(self.kids.items()):
            elapsed_sec = now - data["start"]
            remaining_sec = max(0, (data["booked"] * 60) - int(elapsed_sec))
            m, s = divmod(remaining_sec, 60)
            elapsed_min = int(elapsed_sec // 60) 
            if self.tree.exists(kid_id):
                self.tree.item(kid_id, values=(data["name"], f"{data['booked']} دقيقة", f"{int(m):02d}:{int(s):02d}", f"{elapsed_min * price_rate} EGP"))
            if remaining_sec <= 0 and not data["notified"]:
                data["notified"] = True
                threading.Thread(target=lambda: winsound.Beep(1000, 1000), daemon=True).start()
                messagebox.showwarning("⏰", f"انتهى وقت {data['name']}")
        self.root.after(1000, self.update_clock)

    def check_out_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("تنبيه", "اختار طفل أولاً!")
            return
        
        kid_id = selected[0]
        data = self.kids[kid_id]
        elapsed_min = int((time.time() - data["start"]) // 60) 
        final_price = elapsed_min * get_price_per_min()
        
        self.total_revenue += final_price
        self.rev_label.config(text=f"إجمالي الإيرادات: {self.total_revenue} EGP")

        # الحفظ في CSV مع عناوين وفواصل منقوطة
        file_name = "kids_records.csv"
        file_exists = os.path.isfile(file_name)
        with open(file_name, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=';')
            if not file_exists:
                writer.writerow(["التاريخ", "الاسم", "المدة", "المبلغ"])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M"), data['name'], elapsed_min, final_price])
            
        del self.kids[kid_id]
        self.save_session_to_disk() # تحديث ملف الطوارئ (حذف الطفل منه)
        self.tree.delete(kid_id)
        messagebox.showinfo("فاتورة", f"تم الحساب: {final_price} EGP")

if __name__ == "__main__":
    root = tk.Tk()
    app = KidsCenterPro(root)
    root.mainloop()
    