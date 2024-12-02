from utils.utils import *
from utils.stack import Stack


def menu(service, folder_id, output_folder):
    if folder_id is None:
        folder_name = "Raiz"
    else:
        folder_name = get_folder_name(service, folder_id)
    
    print(f"Pasta onde serão salvos os arquivos: {output_folder}")
    print(f"Pasta atual do drive: {folder_name}\n")
    print(
        "1. Listar itens da pasta atual do drive",
        "2. Escolher caminho de download",
        "3. Tutorial",
        "4. Sair",
        sep='\n'
    )


def main():
    print("Seleciona a pasta que deseja salvar seus arquivos:")
    output_folder = open_pickle('pickle/out_path.pickle', None)
    if output_folder is None:
        output_folder = choose_download_folder()
        save_pickle('pickle/out_path.pickle', output_folder)
    
    folder_stack = open_pickle('pickle/folders.pickle', Stack())
    service = authenticate()
    
    while True:
        folder_id = folder_stack.peek()
        clear()
        menu(service, folder_id, output_folder)
        choice = input("Escolha uma opção: ")

        if choice == '1':        
            while True:
                if folder_id is None:
                    files = list_root_files(service)
                    folder_name = "Raiz"
                else:
                    files = list_files_in_folder(service, folder_id)
                    folder_name = get_folder_name(service, folder_id)
                
                files_sorted = sort_files_by_type(files)
                
                clear()
                print(f"Listando arquivos na pasta {folder_name} do Drive...\n")
                print_files(files_sorted)
                print("\n[0] Voltar uma pasta")
                print("[Q] Sair")
                print("[A] Baixar todos os arquivos")
                indice = input("> ").lower()
                
                if indice == 'q':
                    break
                
                elif indice == 'a':
                    if output_folder is None:
                        output_folder = choose_download_folder()
                        save_pickle('pickle/out_path.pickle', output_folder)
                    
                    if output_folder is None:
                        print("Nenhuma pasta selecionada para salvar os arquivos.")
                        input("Aperte enter para voltar...")
                        break
                    
                    for file in files_sorted:
                        if file['mimeType'] != 'application/vnd.google-apps.folder':
                            download_file(service, file['id'], file['name'], output_folder)
                    continue
                
                if indice == '0':
                    folder_stack.pop()
                    folder_id = folder_stack.peek()
                    save_pickle('pickle/folders.pickle', folder_stack)
                    continue
                
                try:
                    file = files_sorted[int(indice) - 1]
                except (IndexError, ValueError):
                    continue
                
                if file['mimeType'] == 'application/vnd.google-apps.folder':
                    folder_stack.push(file['id'])
                    folder_id = folder_stack.peek()
                    save_pickle('pickle/folders.pickle', folder_stack)
                    continue
                else:
                    if output_folder is None:
                        output_folder = choose_download_folder()
                        save_pickle('pickle/out_path.pickle', output_folder)
                    
                    if output_folder is None:
                        print("Nenhuma pasta selecionada para salvar os arquivos.")
                        input("Aperte enter para voltar...")
                        break
                    
                    download_file(service, file['id'], file['name'], output_folder)

            
        elif choice == '2':
            print("Seleciona a pasta que deseja salvar seus arquivos:")
            choose = choose_download_folder()
            if choose is not None:
                output_folder = choose
            
            
        elif choice == '3':
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

            
        elif choice == '4':
            return


if __name__ == '__main__':
    main()
