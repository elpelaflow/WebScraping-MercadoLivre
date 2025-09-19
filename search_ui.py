import tkinter as tk
from tkinter import messagebox

from config_utils import save_search_query, load_search_query


def main() -> None:
    root = tk.Tk()
    root.title("Mercado Livre - Configurar búsqueda")

    tk.Label(root, text="Ingresa tu búsqueda:").grid(row=0, column=0, padx=10, pady=(10, 0))

    search_var = tk.StringVar(value=load_search_query())
    entry = tk.Entry(root, textvariable=search_var, width=40)
    entry.grid(row=1, column=0, padx=10, pady=10)
    entry.focus_set()

    def submit(event=None):
        query = search_var.get()
        if not query.strip():
            messagebox.showwarning("Búsqueda inválida", "Por favor ingresa un término de búsqueda.")
            return
        formatted = save_search_query(query)
        messagebox.showinfo("Búsqueda guardada", f"Se configuró la búsqueda: {formatted}")

    button = tk.Button(root, text="Guardar búsqueda", command=submit)
    button.grid(row=2, column=0, padx=10, pady=(0, 10))

    entry.bind('<Return>', submit)

    root.mainloop()


if __name__ == "__main__":
    main()