import os
import threading
import json
import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox
from controller import find_large_files, excluir_arquivos, mover_arquivos, validate_path
from utils import format_size

class LimpadorApp(ctk.CTk):
    def __init__(self):
        # Configurações persistentes
        self.config_file = "config.json"
        self.load_config()
        # Variáveis de controle
        self.is_analyzing = False
        self.cancel_analysis = False
        self.filter_widgets = {}
        self.show_filters = False
        super().__init__()
        self.title("Limpador de Arquivos ")
        self.geometry("950x800")
        ctk.set_appearance_mode("light")
        self.checkboxes = []

        self._build_interface()

    def _build_interface(self):
        # Header com título e botão de tema
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=20, pady=10)
        
        titulo = ctk.CTkLabel(header_frame, text="🔍 Otimizador de Espaço em Disco", 
                             font=("Arial", 20, "bold"))
        titulo.pack(side="left", pady=10)
        
        # Botões do header
        buttons_frame = ctk.CTkFrame(header_frame)
        buttons_frame.pack(side="right", padx=10, pady=10)
        
        self.filter_button = ctk.CTkButton(buttons_frame, text="🔧", width=40, 
                                          command=self.toggle_filters)
        self.filter_button.pack(side="left", padx=5)
        
        self.theme_button = ctk.CTkButton(buttons_frame, text="🌙", width=40, 
                                         command=self.toggle_theme)
        self.theme_button.pack(side="left", padx=5)

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

        # Frame de filtros (inicialmente oculto)
        self.filters_frame = ctk.CTkFrame(self)
        self._build_filters()

        # Barra de progresso
        progress_frame = ctk.CTkFrame(self)
        progress_frame.pack(fill="x", padx=20, pady=5)
        
        self.progress_label = ctk.CTkLabel(progress_frame, text="Pronto para análise")
        self.progress_label.pack(side="left", padx=10, pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=300)
        self.progress_bar.pack(side="right", padx=10, pady=5)
        self.progress_bar.set(0)

        # Lista de arquivos (scrollable)
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=800, height=400)
        self.scroll_frame.pack(padx=20, pady=10, fill='both', expand=True)

        # Label para status
        self.status_label = ctk.CTkLabel(self, text="Selecione uma pasta e clique em Analisar", text_color="gray")
        self.status_label.pack(pady=5)

        # Rodapé com botões (fixo na parte inferior)
        botoes = ctk.CTkFrame(self)
        botoes.pack(side="bottom", fill="x", padx=20, pady=10)

        # Container interno para centralizar os botões
        botoes_container = ctk.CTkFrame(botoes)
        botoes_container.pack(pady=10)

        ctk.CTkButton(botoes_container, text="✅ Selecionar Todos", command=self.selecionar_todos).grid(row=0, column=0, padx=5)
        ctk.CTkButton(botoes_container, text="❌ Desmarcar Todos", command=self.desmarcar_todos).grid(row=0, column=1, padx=5)
        ctk.CTkButton(botoes_container, text="🗑️ Excluir Selecionados", fg_color="red", command=self.excluir).grid(row=0, column=2, padx=5)
        ctk.CTkButton(botoes_container, text="📁 Mover Selecionados", command=self.mover).grid(row=0, column=3, padx=5)
        ctk.CTkButton(botoes_container, text="📊 Estatísticas", command=self.show_stats).grid(row=0, column=4, padx=5)


    def _build_filters(self):
        """Constrói a interface de filtros avançados"""
        # Título dos filtros
        title_frame = ctk.CTkFrame(self.filters_frame)
        title_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(title_frame, text="🔧 Filtros Avançados", 
                    font=("Arial", 14, "bold")).pack(side="left", padx=10, pady=5)
        
        # Frame principal dos filtros
        main_filter_frame = ctk.CTkFrame(self.filters_frame)
        main_filter_frame.pack(fill="x", padx=10, pady=5)
        
        # Linha 1: Tipos de arquivo
        ctk.CTkLabel(main_filter_frame, text="Tipos de arquivo:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        types_frame = ctk.CTkFrame(main_filter_frame)
        types_frame.grid(row=0, column=1, columnspan=3, sticky="w", padx=5, pady=5)
        
        self.filter_widgets["videos"] = ctk.CTkCheckBox(types_frame, text="🎬 Vídeos")
        self.filter_widgets["videos"].pack(side="left", padx=5)
        
        self.filter_widgets["images"] = ctk.CTkCheckBox(types_frame, text="🖼️ Imagens")
        self.filter_widgets["images"].pack(side="left", padx=5)
        
        self.filter_widgets["documents"] = ctk.CTkCheckBox(types_frame, text="📄 Documentos")
        self.filter_widgets["documents"].pack(side="left", padx=5)
        
        self.filter_widgets["archives"] = ctk.CTkCheckBox(types_frame, text="📦 Arquivos")
        self.filter_widgets["archives"].pack(side="left", padx=5)
        
        self.filter_widgets["others"] = ctk.CTkCheckBox(types_frame, text="📁 Outros")
        self.filter_widgets["others"].pack(side="left", padx=5)
        
        # Linha 2: Faixa de tamanho
        ctk.CTkLabel(main_filter_frame, text="Tamanho máximo (MB):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.filter_widgets["max_size"] = ctk.CTkEntry(main_filter_frame, width=100, placeholder_text="Ex: 1000")
        self.filter_widgets["max_size"].grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        # Linha 3: Idade do arquivo
        ctk.CTkLabel(main_filter_frame, text="Arquivos mais antigos que:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.filter_widgets["days_old"] = ctk.CTkEntry(main_filter_frame, width=100, placeholder_text="Ex: 30")
        self.filter_widgets["days_old"].grid(row=2, column=1, sticky="w", padx=5, pady=5)
        ctk.CTkLabel(main_filter_frame, text="dias").grid(row=2, column=2, sticky="w", padx=5, pady=5)
        
        # Linha 4: Arquivos ocultos
        self.filter_widgets["hidden"] = ctk.CTkCheckBox(main_filter_frame, text="Incluir arquivos ocultos")
        self.filter_widgets["hidden"].grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=5)
        
        # Botões de ação
        actions_frame = ctk.CTkFrame(self.filters_frame)
        actions_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(actions_frame, text="✅ Aplicar Filtros", 
                     command=self.apply_filters).pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(actions_frame, text="🔄 Limpar Filtros", 
                     command=self.clear_filters).pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(actions_frame, text="💾 Salvar Filtros", 
                     command=self.save_current_filters).pack(side="left", padx=5, pady=5)
        
        # Separador
        ctk.CTkLabel(actions_frame, text="|").pack(side="left", padx=10, pady=5)
        
        # Presets comuns
        ctk.CTkLabel(actions_frame, text="Presets:").pack(side="left", padx=5, pady=5)
        
        ctk.CTkButton(actions_frame, text="🎬 Vídeos Grandes", width=120,
                     command=lambda: self.apply_preset("videos_grandes")).pack(side="left", padx=2, pady=5)
        
        ctk.CTkButton(actions_frame, text="📁 Arquivos Antigos", width=120,
                     command=lambda: self.apply_preset("antigos")).pack(side="left", padx=2, pady=5)
        
        ctk.CTkButton(actions_frame, text="📦 Downloads", width=120,
                     command=lambda: self.apply_preset("downloads")).pack(side="left", padx=2, pady=5)

    def selecionar_pasta(self):
        initial_dir = self.config.get("last_folder", "")
        pasta = filedialog.askdirectory(initialdir=initial_dir)
        if pasta:
            # Validar o caminho selecionado
            is_valid, error_msg = validate_path(pasta)
            if not is_valid:
                messagebox.showerror("Erro de Validação", f"Pasta inválida: {error_msg}")
                return
            
            self.pasta_entry.delete(0, 'end')
            self.pasta_entry.insert(0, pasta)
            self.config["last_folder"] = pasta
            self.save_config()
            self.status_label.configure(text=f"Pasta selecionada: {os.path.basename(pasta)}")

    def analisar(self):
        pasta = self.pasta_entry.get()
        limite_str = self.limite_entry.get()

        # Validar entrada antes de prosseguir
        if not pasta.strip():
            messagebox.showerror("Erro", "Selecione uma pasta primeiro.")
            return

        try:
            # A validação agora é feita dentro de find_large_files
            self.status_label.configure(text="Analisando... Por favor, aguarde.", text_color="blue")
            self.update()  # Atualizar a interface
            
            arquivos = find_large_files(pasta, limite_str)
            
            # Limpar resultados anteriores
            for widget in self.scroll_frame.winfo_children():
                widget.destroy()
            self.checkboxes.clear()

            if not arquivos:
                ctk.CTkLabel(self.scroll_frame, text="Nenhum arquivo grande encontrado.").pack()
                self.status_label.configure(text="Análise concluída - Nenhum arquivo encontrado", text_color="green")
                return

            # Aplicar filtros se ativados
            if self.show_filters:
                arquivos = self.apply_file_filters(arquivos)
            
            # Mostrar resultados
            for path, size in arquivos:
                var = ctk.BooleanVar()
                texto = f"{path} ({format_size(size)})"
                check = ctk.CTkCheckBox(self.scroll_frame, text=texto, variable=var)
                check.pack(anchor="w", pady=2)
                self.checkboxes.append((var, path))

            total_size = sum(size for _, size in arquivos)
            filter_info = self.get_filter_info()
            status_text = f"Encontrados {len(arquivos)} arquivos - Total: {format_size(total_size)}"
            if filter_info:
                status_text += f" | Filtros: {filter_info}"
            
            self.status_label.configure(
                text=status_text, 
                text_color="green"
            )

        except ValueError as e:
            messagebox.showerror("Erro de Validação", str(e))
            self.status_label.configure(text="Erro na análise", text_color="red")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {str(e)}")
            self.status_label.configure(text="Erro na análise", text_color="red")


    def apply_file_filters(self, arquivos):
        """Aplica filtros aos arquivos encontrados"""
        if not arquivos:
            return arquivos
        
        filters = self.config.get("filters", {})
        filtered_files = []
        
        for path, size in arquivos:
            # Verificar se deve incluir o arquivo
            if self.should_include_file(path, size, filters):
                filtered_files.append((path, size))
        
        return filtered_files

    def should_include_file(self, path, size, filters):
        """Verifica se um arquivo deve ser incluído baseado nos filtros"""
        try:
            # Filtro de tamanho máximo
            max_size_mb = filters.get("max_size_mb", 0)
            if max_size_mb > 0:
                max_size_bytes = max_size_mb * 1024 * 1024
                if size > max_size_bytes:
                    return False
            
            # Filtro de tipos de arquivo
            file_types = filters.get("file_types", [])
            if file_types:
                file_category = self.get_file_category(path)
                if file_category not in file_types:
                    return False
            
            # Filtro de idade
            days_old = filters.get("days_old", 0)
            if days_old > 0:
                file_time = os.path.getmtime(path)
                file_date = datetime.datetime.fromtimestamp(file_time)
                cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_old)
                if file_date > cutoff_date:
                    return False
            
            # Filtro de arquivos ocultos
            include_hidden = filters.get("include_hidden", False)
            if not include_hidden:
                filename = os.path.basename(path)
                if filename.startswith("."):
                    return False
            
            return True
            
        except Exception:
            # Em caso de erro, incluir o arquivo
            return True

    def get_file_category(self, path):
        """Determina a categoria de um arquivo baseado na extensão"""
        ext = os.path.splitext(path)[1].lower()
        
        if ext in [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"]:
            return "video"
        elif ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg", ".webp"]:
            return "image"
        elif ext in [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx"]:
            return "document"
        elif ext in [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"]:
            return "archive"
        else:
            return "other"



    def get_filter_info(self):
        """Retorna informação resumida dos filtros ativos"""
        if not self.show_filters:
            return ""
        
        filters = self.config.get("filters", {})
        info_parts = []
        
        # Tipos de arquivo
        file_types = filters.get("file_types", [])
        if file_types:
            type_names = {
                "video": "Vídeos",
                "image": "Imagens", 
                "document": "Docs",
                "archive": "Arquivos",
                "other": "Outros"
            }
            types_str = ", ".join([type_names.get(t, t) for t in file_types])
            info_parts.append(f"Tipos: {types_str}")
        
        # Tamanho máximo
        max_size = filters.get("max_size_mb", 0)
        if max_size > 0:
            info_parts.append(f"Máx: {max_size}MB")
        
        # Idade
        days_old = filters.get("days_old", 0)
        if days_old > 0:
            info_parts.append(f">{days_old} dias")
        
        # Arquivos ocultos
        if filters.get("include_hidden", False):
            info_parts.append("+ Ocultos")
        
        return " | ".join(info_parts) if info_parts else "Nenhum filtro ativo"


    def get_selecionados(self):
        return [path for var, path in self.checkboxes if var.get()]

    def calcular_tamanho_selecionados(self):
        """Calcula o tamanho total dos arquivos selecionados"""
        arquivos = self.get_selecionados()
        total_size = 0
        for arquivo in arquivos:
            try:
                total_size += os.path.getsize(arquivo)
            except:
                pass
        return total_size

    def excluir(self):
        arquivos = self.get_selecionados()
        if not arquivos:
            messagebox.showinfo("Nada selecionado", "Selecione ao menos um arquivo.")
            return

        # Calcular tamanho total que será liberado
        tamanho_total = self.calcular_tamanho_selecionados()
        
        # PRIMEIRA CONFIRMAÇÃO - Mais detalhada
        msg_primeira = (
            f"⚠️ ATENÇÃO - EXCLUSÃO PERMANENTE ⚠️\n\n"
            f"Você está prestes a excluir {len(arquivos)} arquivo(s)\n"
            f"Espaço a ser liberado: {format_size(tamanho_total)}\n\n"
            f"Esta ação NÃO PODE ser desfeita!\n"
            f"Os arquivos serão excluídos permanentemente.\n\n"
            f"Deseja continuar?"
        )
        
        if not messagebox.askyesno("⚠️ Confirmar Exclusão", msg_primeira, icon="warning"):
            return

        # SEGUNDA CONFIRMAÇÃO - Mais específica
        if len(arquivos) > 5:
            # Para muitos arquivos, mostrar resumo
            msg_segunda = (
                f"🚨 CONFIRMAÇÃO FINAL 🚨\n\n"
                f"Excluir {len(arquivos)} arquivos permanentemente?\n"
                f"Primeiros arquivos:\n"
            )
            for i, arquivo in enumerate(arquivos[:3]):
                nome_arquivo = os.path.basename(arquivo)
                msg_segunda += f"• {nome_arquivo}\n"
            if len(arquivos) > 3:
                msg_segunda += f"... e mais {len(arquivos) - 3} arquivos\n"
        else:
            # Para poucos arquivos, mostrar todos
            msg_segunda = (
                f"🚨 CONFIRMAÇÃO FINAL 🚨\n\n"
                f"Excluir estes arquivos permanentemente?\n\n"
            )
            for arquivo in arquivos:
                nome_arquivo = os.path.basename(arquivo)
                msg_segunda += f"• {nome_arquivo}\n"
        
        msg_segunda += f"\nEsta é sua última chance de cancelar!"
        
        if not messagebox.askyesno("🚨 Confirmação Final", msg_segunda, icon="warning"):
            return

        # Executar exclusão
        self.status_label.configure(text="Excluindo arquivos...", text_color="red")
        self.update()
        
        try:
            erros = excluir_arquivos(arquivos)
            if erros:
                erro_msg = "Alguns arquivos não foram excluídos:\n\n"
                for arquivo, erro in erros[:5]:  # Mostrar apenas os primeiros 5 erros
                    erro_msg += f"• {os.path.basename(arquivo)}: {erro}\n"
                if len(erros) > 5:
                    erro_msg += f"\n... e mais {len(erros) - 5} erros."
                messagebox.showwarning("Erros na Exclusão", erro_msg)
                self.status_label.configure(text=f"Exclusão com erros - {len(erros)} falhas", text_color="orange")
            else:
                messagebox.showinfo("Sucesso", f"✅ {len(arquivos)} arquivo(s) excluído(s) com sucesso!\nEspaço liberado: {format_size(tamanho_total)}")
                self.status_label.configure(text=f"Exclusão concluída - {len(arquivos)} arquivos removidos", text_color="green")
            
            # Atualizar a lista
            self.analisar()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro durante a exclusão: {str(e)}")
            self.status_label.configure(text="Erro na exclusão", text_color="red")

    def mover(self):
        arquivos = self.get_selecionados()
        if not arquivos:
            messagebox.showinfo("Nada selecionado", "Selecione ao menos um arquivo.")
            return
        
        destino = filedialog.askdirectory(title="Selecione a pasta de destino")
        if not destino:
            return

        # Validar destino antes de prosseguir
        is_valid, error_msg = validate_path(destino)
        if not is_valid:
            messagebox.showerror("Erro de Validação", f"Pasta de destino inválida: {error_msg}")
            return

        # Confirmar movimentação
        tamanho_total = self.calcular_tamanho_selecionados()
        msg_confirmacao = (
            f"Mover {len(arquivos)} arquivo(s) para:\n"
            f"{destino}\n\n"
            f"Tamanho total: {format_size(tamanho_total)}\n\n"
            f"Confirmar movimentação?"
        )
        
        if not messagebox.askyesno("Confirmar Movimentação", msg_confirmacao):
            return

        self.status_label.configure(text="Movendo arquivos...", text_color="blue")
        self.update()
        
        try:
            erros = mover_arquivos(arquivos, destino)
            if erros:
                erro_msg = "Alguns arquivos não foram movidos:\n\n"
                for arquivo, erro in erros[:5]:
                    erro_msg += f"• {os.path.basename(arquivo)}: {erro}\n"
                if len(erros) > 5:
                    erro_msg += f"\n... e mais {len(erros) - 5} erros."
                messagebox.showwarning("Erros na Movimentação", erro_msg)
                self.status_label.configure(text=f"Movimentação com erros - {len(erros)} falhas", text_color="orange")
            else:
                messagebox.showinfo("Sucesso", f"✅ {len(arquivos)} arquivo(s) movido(s) com sucesso!")
                self.status_label.configure(text=f"Movimentação concluída - {len(arquivos)} arquivos", text_color="green")
            
            # Atualizar a lista
            self.analisar()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro durante a movimentação: {str(e)}")
            self.status_label.configure(text="Erro na movimentação", text_color="red")



    def toggle_filters(self):
        """Mostra/oculta o painel de filtros"""
        if self.show_filters:
            self.filters_frame.pack_forget()
            self.filter_button.configure(text="🔧")
            self.show_filters = False
        else:
            self.filters_frame.pack(fill="x", padx=20, pady=5, before=self.progress_bar.master)
            self.filter_button.configure(text="🔧✓")
            self.show_filters = True
            self.load_saved_filters()

    def apply_filters(self):
        """Aplica os filtros e reanalisa os arquivos"""
        if not self.pasta_entry.get().strip():
            messagebox.showwarning("Aviso", "Selecione uma pasta primeiro.")
            return
        
        # Salvar filtros atuais
        self.save_current_filters()
        # Executar nova análise
        self.analisar()

    def clear_filters(self):
        """Limpa todos os filtros"""
        # Desmarcar checkboxes
        for name in ["videos", "images", "documents", "archives", "others", "hidden"]:
            if name in self.filter_widgets:
                self.filter_widgets[name].deselect()
        
        # Limpar campos de entrada
        for name in ["max_size", "days_old"]:
            if name in self.filter_widgets:
                self.filter_widgets[name].delete(0, "end")
        
        # Limpar configuração
        self.config["filters"] = {
            "file_types": [],
            "min_size_mb": 0,
            "max_size_mb": 0,
            "days_old": 0,
            "include_hidden": False
        }
        self.save_config()

    def save_current_filters(self):
        """Salva os filtros atuais na configuração"""
        filters = {
            "file_types": [],
            "min_size_mb": int(self.limite_entry.get() or 0),
            "max_size_mb": 0,
            "days_old": 0,
            "include_hidden": False
        }
        
        # Tipos de arquivo selecionados
        type_mapping = {
            "videos": "video",
            "images": "image", 
            "documents": "document",
            "archives": "archive",
            "others": "other"
        }
        
        for name, file_type in type_mapping.items():
            if name in self.filter_widgets and self.filter_widgets[name].get():
                filters["file_types"].append(file_type)
        
        # Tamanho máximo
        if "max_size" in self.filter_widgets:
            try:
                max_size = self.filter_widgets["max_size"].get()
                if max_size.strip():
                    filters["max_size_mb"] = int(max_size)
            except ValueError:
                pass
        
        # Dias
        if "days_old" in self.filter_widgets:
            try:
                days = self.filter_widgets["days_old"].get()
                if days.strip():
                    filters["days_old"] = int(days)
            except ValueError:
                pass
        
        # Arquivos ocultos
        if "hidden" in self.filter_widgets:
            filters["include_hidden"] = self.filter_widgets["hidden"].get()
        
        self.config["filters"] = filters
        self.save_config()

    def load_saved_filters(self):
        """Carrega filtros salvos na interface"""
        filters = self.config.get("filters", {})
        
        # Restaurar tipos de arquivo
        type_mapping = {
            "video": "videos",
            "image": "images",
            "document": "documents", 
            "archive": "archives",
            "other": "others"
        }
        
        for file_type in filters.get("file_types", []):
            widget_name = type_mapping.get(file_type)
            if widget_name in self.filter_widgets:
                self.filter_widgets[widget_name].select()
        
        # Restaurar tamanho máximo
        if filters.get("max_size_mb", 0) > 0:
            self.filter_widgets["max_size"].insert(0, str(filters["max_size_mb"]))
        
        # Restaurar dias
        if filters.get("days_old", 0) > 0:
            self.filter_widgets["days_old"].insert(0, str(filters["days_old"]))
        
        # Restaurar arquivos ocultos
        if filters.get("include_hidden", False):
            self.filter_widgets["hidden"].select()



    def apply_preset(self, preset_name):
        """Aplica um preset de filtros predefinido"""
        # Primeiro limpar filtros
        self.clear_filters()
        
        if preset_name == "videos_grandes":
            # Vídeos maiores que 500MB
            self.filter_widgets["videos"].select()
            self.limite_entry.delete(0, "end")
            self.limite_entry.insert(0, "500")
            
        elif preset_name == "antigos":
            # Arquivos mais antigos que 90 dias
            self.filter_widgets["days_old"].insert(0, "90")
            
        elif preset_name == "downloads":
            # Arquivos e vídeos em Downloads
            self.filter_widgets["videos"].select()
            self.filter_widgets["archives"].select()
            self.filter_widgets["documents"].select()
            self.limite_entry.delete(0, "end")
            self.limite_entry.insert(0, "50")
        
        # Aplicar os filtros automaticamente
        self.apply_filters()


    def load_config(self):
        """Carrega configurações salvas"""
        default_config = {
            "theme": "light",
            "default_size_mb": 100,
            "last_folder": "",
            "filters": {
                "file_types": [],
                "min_size_mb": 0,
                "max_size_mb": 0,
                "days_old": 0,
                "include_hidden": False
            }
        }
        
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
            # Mesclar com configurações padrão para novos campos
            for key, value in default_config.items():
                if key not in self.config:
                    self.config[key] = value
        except:
            self.config = default_config

    def save_config(self):
        """Salva configurações"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except:
            pass

    def apply_theme(self):
        """Aplica o tema atual"""
        theme = self.config.get("theme", "light")
        ctk.set_appearance_mode(theme)
        if hasattr(self, 'theme_button'):
            self.theme_button.configure(text="☀️" if theme == "dark" else "🌙")
        if hasattr(self, 'filter_button'):
            if self.show_filters:
                self.filter_button.configure(text="🔧✓")
            else:
                self.filter_button.configure(text="🔧")

    def toggle_theme(self):
        """Alterna entre tema claro e escuro"""
        current_theme = self.config.get("theme", "light")
        new_theme = "dark" if current_theme == "light" else "light"
        self.config["theme"] = new_theme
        self.save_config()
        self.apply_theme()

    def desmarcar_todos(self):
        """Desmarca todos os checkboxes"""
        for var, _ in self.checkboxes:
            var.set(False)
        self.update_selection_status()

    def update_selection_status(self):
        """Atualiza status baseado na seleção"""
        if self.checkboxes:
            selected_count = sum(1 for var, _ in self.checkboxes if var.get())
            if selected_count > 0:
                tamanho_total = self.calcular_tamanho_selecionados()
                self.status_label.configure(
                    text=f"{selected_count} de {len(self.checkboxes)} arquivos selecionados - Total: {format_size(tamanho_total)}", 
                    text_color="blue"
                )
            else:
                self.status_label.configure(
                    text=f"{len(self.checkboxes)} arquivos disponíveis", 
                    text_color="gray"
                )

    def selecionar_todos(self):
        for var, _ in self.checkboxes:
            var.set(True)
        self.update_selection_status()
    def show_stats(self):
        """Mostra estatísticas dos arquivos"""
        if not self.checkboxes:
            messagebox.showinfo("Estatísticas", "Faça uma análise primeiro.")
            return

        # Calcular estatísticas
        total_files = len(self.checkboxes)
        total_size = 0
        stats_by_type = {}
        
        for var, path in self.checkboxes:
            try:
                size = os.path.getsize(path)
                total_size += size
                
                ext = os.path.splitext(path)[1].lower()
                if ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv']:
                    category = '🎬 Vídeos'
                elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    category = '🖼️ Imagens'
                elif ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf']:
                    category = '📄 Documentos'
                elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                    category = '📦 Arquivos'
                else:
                    category = '📁 Outros'
                
                if category not in stats_by_type:
                    stats_by_type[category] = {'count': 0, 'size': 0}
                stats_by_type[category]['count'] += 1
                stats_by_type[category]['size'] += size
            except:
                pass

        # Criar janela de estatísticas
        stats_window = ctk.CTkToplevel(self)
        stats_window.title("Estatísticas dos Arquivos")
        stats_window.geometry("500x400")
        stats_window.grab_set()

        ctk.CTkLabel(stats_window, text="📊 Estatísticas dos Arquivos", font=("Arial", 16, "bold")).pack(pady=10)

        # Estatísticas gerais
        general_frame = ctk.CTkFrame(stats_window)
        general_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(general_frame, text=f"Total de arquivos: {total_files}", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=2)
        ctk.CTkLabel(general_frame, text=f"Tamanho total: {format_size(total_size)}", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=2)

        # Estatísticas por tipo
        type_frame = ctk.CTkFrame(stats_window)
        type_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(type_frame, text="Por tipo de arquivo:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)

        for category, data in stats_by_type.items():
            percentage = (data['size'] / total_size * 100) if total_size > 0 else 0
            text = f"{category}: {data['count']} arquivos - {format_size(data['size'])} ({percentage:.1f}%)"
            ctk.CTkLabel(type_frame, text=text).pack(anchor="w", padx=20, pady=2)

        ctk.CTkButton(stats_window, text="Fechar", command=stats_window.destroy).pack(pady=20)
