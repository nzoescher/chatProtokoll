import tkinter as tk
import threading

class ChatWindow:
    def __init__(self):
        self._root = None
        self._text = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        self._root = tk.Tk()
        self._root.title("Empfangene Nachrichten")
        self._root.geometry("600x400")

        self._text = tk.Text(self._root, state=tk.DISABLED)
        self._text.pack(fill=tk.BOTH, expand=True)

        self._root.mainloop()

    def show(self, nachricht: str):
        if self._text:
            self._text.configure(state=tk.NORMAL)
            self._text.insert(tk.END, nachricht + "\n")
            self._text.configure(state=tk.DISABLED)
            self._text.see(tk.END)