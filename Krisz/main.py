import tkinter as tk
from tkinter import ttk, messagebox
import time
import json, os
from rules import filter_stocks_by_stochastic
import updater

SPLASH_DURATION = 5
SETTINGS_FILE = "settings.json"

# ---- Beállítások ----
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    return {"timeframe": "1d", "k_threshold": 20, "market": "DAX"}

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

# ---- Splash + updater ----
class SplashScreen(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.geometry("400x150+500+250")
        self.overrideredirect(True)
        self.configure(bg="white")

        tk.Label(self, text="Piac Figyelő Betöltés...", font=("Arial", 16), bg="white", fg="black").pack(pady=20)
        self.progress = ttk.Progressbar(self, orient="horizontal", length=300, mode="determinate", maximum=100)
        self.progress.pack(pady=20)
        self.update()

        self.start_time = time.time()
        self.after(50, self.update_progress)

    def update_progress(self):
        elapsed = time.time() - self.start_time
        progress_value = min(int((elapsed / SPLASH_DURATION) * 100), 100)
        self.progress['value'] = progress_value
        self.update()

        # Ha eltelt a splash idő, fut az updater és bezárul a splash
        if elapsed >= SPLASH_DURATION:
            print("[CHECK PANEL] Splash vége, updater indul...")
            updater.run_updater()
            self.destroy()
        else:
            self.after(50, self.update_progress)

# ---- Fő GUI ----
class DaxApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Piac Figyelő")
        self.geometry("700x450")
        self.configure(bg="#d9d9d9")

        self.create_menu()

        # Oszlopos Treeview
        self.tree = ttk.Treeview(self, columns=("name","ticker","kvalue"), show="headings", height=20)
        self.tree.heading("name", text="Részvény neve")
        self.tree.heading("ticker", text="Yahoo ticker")
        self.tree.heading("kvalue", text="%K")
        self.tree.column("name", width=250)
        self.tree.column("ticker", width=100)
        self.tree.column("kvalue", width=50)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Jobb panel: log
        self.log_text = tk.Text(self, font=("Consolas", 10), state="disabled", width=30)
        self.log_text.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        self.refresh_stocks()

    def create_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Frissítés", command=self.refresh_stocks)
        file_menu.add_separator()
        file_menu.add_command(label="Kilépés", command=self.quit)
        menubar.add_cascade(label="Fájl", menu=file_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Updater futtatása", command=self.run_updater)
        tools_menu.add_command(label="Beállítások", command=self.open_settings)
        menubar.add_cascade(label="Eszközök", menu=tools_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Verzió", command=lambda: messagebox.showinfo("Verzió", f"Helyi verzió: {updater.get_local_version()}"))
        menubar.add_cascade(label="Súgó", menu=help_menu)

        self.config(menu=menubar)

    def log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        print(f"[CHECK PANEL] {msg}")  # CMD log is

    def refresh_stocks(self):
        self.tree.delete(*self.tree.get_children())
        settings = load_settings()
        threshold = settings.get("k_threshold", 20)
        filtered = filter_stocks_by_stochastic()
        filtered = [s for s in filtered if s[3] <= threshold]
        if not filtered:
            self.tree.insert("", tk.END, values=("Nincs részvény a threshold alatt","",""))
        else:
            for stock in filtered:
                name, yf_ticker, tv_ticker, k_value = stock
                self.tree.insert("", tk.END, values=(name, yf_ticker, k_value))
        self.log(f"Frissítés lefutott: {len(filtered)} részvény talált.")

    def run_updater(self):
        self.log("Updater futtatása...")
        updater.run_updater()
        self.log("Updater lefutott.")

    def open_settings(self):
        settings = load_settings()
        win = tk.Toplevel(self)
        win.title("Beállítások")
        win.geometry("300x200")
        win.grab_set()

        tk.Label(win, text="Idősík:").pack(pady=5)
        tf_var = tk.StringVar(value=settings.get("timeframe", "1d"))
        tk.OptionMenu(win, tf_var, "1m","5m","15m","1h","1d").pack(pady=5)

        tk.Label(win, text="%K threshold:").pack(pady=5)
        k_var = tk.IntVar(value=settings.get("k_threshold", 20))
        tk.Spinbox(win, from_=0, to=100, textvariable=k_var).pack(pady=5)

        tk.Label(win, text="Piac:").pack(pady=5)
        market_var = tk.StringVar(value=settings.get("market", "DAX"))
        tk.OptionMenu(win, market_var, "DAX","Kripto").pack(pady=5)

        def save_and_close():
            new_settings = {"timeframe": tf_var.get(), "k_threshold": k_var.get(), "market": market_var.get()}
            save_settings(new_settings)
            self.log("Beállítások mentve.")
            win.destroy()
        tk.Button(win, text="Mentés", command=save_and_close).pack(pady=10)

# ---- Indítás splash + GUI ----
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    splash = SplashScreen(root)
    splash.update()
    root.after(SPLASH_DURATION * 1000, root.destroy)
    root.mainloop()

    # Miután a splash lezárult, indul a fő GUI
    app = DaxApp()
    app.mainloop()
