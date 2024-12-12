from utils.utils import *
from utils.stack import Stack


class App:
    def __init__(self, service):
        self.service = service
        
        output_folder = open_pickle('out_path.pickle', None)
        verify_output_folder(output_folder)
        self.output_folder = output_folder
        
        self.folder_stack = open_pickle('folders.pickle', Stack())
        
        self.folder_id = None
        self.folder_name = None
        
        
    def run(self):
        while True:
            self.folder_id = self.folder_stack.peek()
            if self.folder_id is None:
                self.folder_name = "Raiz"
            else:
                self.folder_name = get_folder_name(self.service, self.folder_id)
            clear()
            self._menu_principal()
            choice = input("Escolha uma opcao: ").strip()
            if choice == '1':
                self._list_files()
            elif choice == '2':
                self._list_files_by_id()
            elif choice == '3':
                self._choose_download_folder()
            elif choice == '4':
                self._change_account()
            elif choice == '5':
                self._tutorial()
            elif choice == '6':
                break
                
                
    def _menu_principal(self):
        print(f"Pasta onde os arquivos serão salvos: {self.output_folder}")
        print(f"Pasta atual do drive: {self.folder_name}\n")
        print(
            "1. Listar itens da pasta atual do drive",
            "2. Listar itens por id da pasta",
            "3. Escolher caminho de download",
            "4. Trocar contas",
            "5. Tutorial",
            "6. Sair",
            sep='\n'
        )
        
        
    def _tutorial(self):
        clear()
        print(
            "Tutorial:",
            "- Digite 'q' para cancelar ou voltar a qualquer momento.",
            "- Na opção 1 (Listar itens da pasta atual), você pode navegar entre as pastas.",
            "- Selecione o indice da pasta que deseja selecionar.",
            "- Para voltar uma pasta, escolha o indice 0.",
            "- Você pode baixar 1 ou todos os arquivos.",
            "- As pastas não serão baixadas, apenas os arquivos.",
            "- Escolha onde deseja salvar os arquivos.",
            sep='\n'
        )
        input("\nAperte enter para continuar...")
        
        
    def _filter_by_name(self, name, files):
        files = [file for file in files if name.lower() in file['name'].lower() and is_folder(file)]
        return files
        
    def _list_files(self):
        while True:
            if self.folder_id is None:
                files = list_root_files(self.service)
            else:
                files = list_files_in_folder(self.service, self.folder_id)
            
            files = sort_files_by_type(files)
            
            clear()
            print(f"Listando arquivos na pasta {self.folder_name} do Drive...\n")
            print_files(files)
            print("\n[0] Voltar uma pasta")
            print("[Q] Sair")
            print("[A] Baixar todos os arquivos (aperte 'q' para cancelar os downloads em andamento)")
            indice = input("> ").lower().strip().split()
            
            if len(indice) == 1:
                indice = indice[0]
            elif len(indice) >= 2:
                try:
                    indice = list(dict.fromkeys(indice))
                    if indice[0] == '!' and len(indice) == 3:
                        indice = [int(i) if i != '!' else i for i in indice]
                    else:
                        indice = list(map(int, indice))
                except ValueError:
                    continue
                
                try:
                    if indice[0] == '!':
                        indice.pop(0)
                        files_to_download = [files[i - 1] for i in range(min(indice), max(indice) + 1) if not is_folder(files[i - 1])]
                    else:
                        files_to_download = [files[i - 1] for i in indice if not is_folder(files[i - 1])]
                except IndexError:
                    continue
                
                if len(files_to_download) > 0:        
                    self.__download_all_files(files_to_download)
                continue
                
            
            if indice == 'q':
                break
            
            elif indice == '0':
                self.__back_folder()
                
            elif indice == 'a':
                if not self.__download_all_files(files):
                    break
            elif indice.isdecimal():
                try:
                    file_selected = files[int(indice) - 1]
                except (IndexError, ValueError):
                    continue
                
                if is_folder(file_selected):
                    self.__select_folder(file_selected)
                else:
                    if not self.__download_selected_file(file_selected):
                        break
            else:
                files_filtered = self._filter_by_name(indice, files)
                if len(files_filtered) == 0:
                    print("Nenhuma pasta encontrado com esse nome.")
                    input("Aperte enter para voltar...")
                    continue
                
                clear()
                print_files(files_filtered)
                print("\n[Q] Sair")
                print("Selecione uma pasta")
                indice = input("> ").lower().strip()
                if indice == 'q':
                    continue
                    
                try:
                    file_selected = files_filtered[int(indice) - 1]
                except (IndexError, ValueError):
                    continue
                
                self.__select_folder(file_selected)
                break
    
    
    def _list_files_by_id(self):
        folder_id = input("Digite o id da pasta (ou 'q' para sair): ").strip()
        index = folder_id.find("?")
        if index != -1:
            folder_id = folder_id[:index]
        
        if folder_id == 'q':
            return
         
        while True:
            files = list_files_in_folder(self.service, folder_id)
            if len(files) == 0:
                print("Nenhum arquivo encontrado na pasta escolhida.")
                input("Aperte enter para voltar...")
                continue
            
            files = sort_files_by_type(files)
            folder_name = get_folder_name(self.service, folder_id)
            clear()
            print(f"Listando arquivos na pasta {folder_name} do Drive...\n")
            print_files(files)
            print(
                "\n[Q] Sair",
                "[A] Baixar todos os arquivos (aperte 'q' para cancelar os downloads em andamento)",
                sep="\n"
            )
            indice = input("> ").lower().strip()
            
            if indice == 'q':
                break
            
            elif indice == 'a':
                if not self.__download_all_files(files):
                    break
            else:
                try:
                    file_selected = files[int(indice) - 1]
                except (IndexError, ValueError):
                    continue
                
                if is_folder(file_selected):
                    self.__select_folder(file_selected)
                else:
                    if not self.__download_selected_file(file_selected):
                        break
            
    
    def _choose_download_folder(self):
        print("Seleciona a pasta que deseja salvar seus arquivos:")
        output_folder = choose_download_folder()
        if output_folder is not None:
            self.output_folder = output_folder
            save_pickle('out_path.pickle', output_folder)
            
          
    def _change_account(self):
        service = authenticate(change_account=True)
        if service is not None:
            self.service = service
        
            
    def __back_folder(self):
        self.folder_stack.pop()
        self.folder_id = self.folder_stack.peek()
        save_pickle('folders.pickle', self.folder_stack)
    
    def __download_selected_file(self, file_selected) -> bool:
        verify_output_folder(self.output_folder)
        if self.output_folder is None:
            print("Nenhuma pasta selecionada para salvar os arquivos.")
            input("Aperte enter para voltar...")
            return False
        
        download_file(self.service, file_selected['id'], file_selected['name'], self.output_folder)
        return True
    
    def __select_folder(self, file_selected) -> None:
        self.folder_stack.push(file_selected['id'])
        self.folder_id = self.folder_stack.peek()
        save_pickle('folders.pickle', self.folder_stack)
    
    def __download_all_files(self, files) -> bool:
        verify_output_folder(self.output_folder)
        if self.output_folder is None:
            print("Nenhuma pasta selecionada para salvar os arquivos.")
            input("Aperte enter para voltar...")
            return False
    
        download_files(self.service, files, self.output_folder)
        return True