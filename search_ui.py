import subprocess
import sys
import tkinter as tk
from tkinter import messagebox

from config_utils import load_search_query, save_search_query


def main() -> None:
    root = tk.Tk()
    root.title("Mercado Livre - Configurar búsqueda")

    tk.Label(root, text="Ingresa tu búsqueda:").grid(row=0, column=0, padx=10, pady=(10, 0))

    search_var = tk.StringVar(value=load_search_query().replace("-", " "))
    entry = tk.Entry(root, textvariable=search_var, width=40)
    entry.grid(row=1, column=0, padx=10, pady=10)
    entry.focus_set()

    def submit(event=None):
        query = search_var.get()
        if not query.strip():
            messagebox.showwarning("Búsqueda inválida", "Por favor ingresa un término de búsqueda.")
            return
        formatted = save_search_query(query)
        try:
            subprocess.run([sys.executable, "crawl.py"], check=True)
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            messagebox.showerror(
                "Error al generar búsqueda",
                "Ocurrió un error al ejecutar el proceso de extracción."
                + (f"\nCódigo de salida: {exc.returncode}" if isinstance(exc, subprocess.CalledProcessError) else ""),
            )
            return

        search_var.set(query.strip())
        messagebox.showinfo(
            "Búsqueda generada",
            "Se configuró la búsqueda y se generó la información"
            f" para: {search_var.get() or formatted.replace('-', ' ')}",
        )

    button = tk.Button(root, text="Generar búsqueda", command=submit)
    button.grid(row=2, column=0, padx=10, pady=(0, 5))

    def open_dashboard() -> None:
        subprocess.Popen(
            ["streamlit", "run", "dashboard/dashboard.py"],
            start_new_session=True,
        )

    dashboard_button = tk.Button(root, text="Ver dashboard", command=open_dashboard)
    dashboard_button.grid(row=3, column=0, padx=10, pady=(0, 10))

    entry.bind('<Return>', submit)

    root.mainloop()


if __name__ == "__main__":
    main()