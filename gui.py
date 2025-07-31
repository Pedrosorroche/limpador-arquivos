import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from controller import find_large_files, excluir_arquivos, mover_arquivos
from utils import format_size

class LimpadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Limpador de Arquivos Grandes")
        self.geometry("900x650")
        ctk.set_appearance_mode("light")
        self.checkboxes = []

        self._build_interface()

    def _build_interface(self):
        # Título
        titulo = ctk.CTkLabel(self, text="🔍 Limpador de Arquivos Grandes", font=("Arial", 20, "bold"))
        titulo.pack(pady=10)

        # Frame de entrada
        entrada_frame = ctk.CTkFrame(self)
        entrada_frame.pack(pady=10, padx=20, fill='x')

        # Linha 1 – Pasta
        ctk.CTkLabel(entrada_frame, text="Pasta:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.pasta_entry = ctk.CTkEntry(entrada_frame, width=500)
        self.pasta_entry.grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(entrada_frame, text="Selecionar", command=self.selecionar_pasta).grid(row=0, column=2, padx=5)

        # Linha 2 – Limite
        ctk.CTkLabel(entrada_frame, text="Tamanho mínimo (MB):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.limite_entry = ctk.CTkEntry(entrada_frame, width=100)
        self.limite_entry.insert(0, "100")
        self.limite_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        ctk.CTkButton(entrada_frame, text="Analisar", command=self.analisar).grid(row=1, column=2, padx=5)

        # Lista de arquivos (scrollable)
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=800, height=400)
        self.scroll_frame.pack(padx=20, pady=10, fill='both', expand=True)

        # Rodapé com botões
        botoes = ctk.CTkFrame(self)
        botoes.pack(pady=10)

        ctk.CTkButton(botoes, text="Selecionar Todos", command=self.selecionar_todos).grid(row=0, column=0, padx=10)
        ctk.CTkButton(botoes, text="Excluir Selecionados", fg_color="red", command=self.excluir).grid(row=0, column=1, padx=10)
        ctk.CTkButton(botoes, text="Mover Selecionados", command=self.mover).grid(row=0, column=2, padx=10)
        ctk.CTkButton(botoes, text="Fechar", command=self.quit).grid(row=0, column=3, padx=10)

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory()
        if pasta:
            self.pasta_entry.delete(0, 'end')
            self.pasta_entry.insert(0, pasta)

    def analisar(self):
        pasta = self.pasta_entry.get()
        try:
            limite = float(self.limite_entry.get())
        except:
            messagebox.showerror("Erro", "Digite um valor válido.")
            return

        arquivos = find_large_files(pasta, limite)
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.checkboxes.clear()

        if not arquivos:
            ctk.CTkLabel(self.scroll_frame, text="Nenhum arquivo grande encontrado.").pack()
            return

        for path, size in arquivos:
            var = ctk.BooleanVar()
            texto = f"{path} ({format_size(size)})"
            check = ctk.CTkCheckBox(self.scroll_frame, text=texto, variable=var)
            check.pack(anchor="w", pady=2)
            self.checkboxes.append((var, path))

    def get_selecionados(self):
        return [path for var, path in self.checkboxes if var.get()]

    def excluir(self):
        arquivos = self.get_selecionados()
        if not arquivos:
            messagebox.showinfo("Nada selecionado", "Selecione ao menos um arquivo.")
            return
        if messagebox.askyesno("Confirmar", f"Excluir {len(arquivos)} arquivo(s)?"):
            erros = excluir_arquivos(arquivos)
            if erros:
                messagebox.showwarning("Erros", f"Alguns arquivos não foram excluídos:\n{erros}")
            else:
                messagebox.showinfo("Sucesso", "Arquivos excluídos.")
            self.analisar()

    def mover(self):
        arquivos = self.get_selecionados()
        if not arquivos:
            messagebox.showinfo("Nada selecionado", "Selecione ao menos um arquivo.")
            return
        destino = filedialog.askdirectory()
        if not destino:
            return
        erros = mover_arquivos(arquivos, destino)
        if erros:
            messagebox.showwarning("Erros", f"Alguns arquivos não foram movidos:\n{erros}")
        else:
            messagebox.showinfo("Sucesso", "Arquivos movidos.")
        self.analisar()

    def selecionar_todos(self):
        for var, _ in self.checkboxes:
            var.set(True)
