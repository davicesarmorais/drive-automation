from utils import *
from stack import Stack
import time

    # TODO: Salvar a pasta que o usuário estava
    # TODO: Opção de voltar uma pasta????????? como OMG PILHA USAGE
    # TODO: Perguntar se quer baixar um arquivo ou todos
    # TODO: Opcao de entrar em uma pasta (e salva-la)
    # TODO: Se o id da pasta for None usar o list_root_files
    # TODO: Supressor de imagem


def menu():
    return "\n".join([
        "1. Listar itens da pasta atual",
        "2. Escolher caminho de download",
        "3. Tutorial",
        "4. Sair"
    ])

def main():
    # ID da pasta no Google Drive (substitua pelo ID real)
    # folder_id = '0dads3213adada'
    
    print("Seleciona a pasta que deseja salvar seus arquivos:")
    # output_folder = choose_download_folder()
    
    folder_stack = open_pickle('folders.pickle', Stack())
    service = authenticate()
    
    while True:
        folder_id = folder_stack.peek()
        clear()
        print(menu())
        choice = input("Escolha uma opção: ")

        if choice == '1':        
            while True:
                if folder_id is None:
                    files = list_root_files(service)
                else:
                    files = list_files_in_folder(service, folder_id)
                
                files_sorted = sort_files_by_type(files)
                
                clear()
                print("Listando arquivos no Drive...")
                print("[00] Voltar uma pasta")
                print_files(files_sorted)
                print("\n[Q] Voltar")
                print("[A] Baixar todos os arquivos")
                indice = input("> ").lower()
                
                if indice == 'q':
                    break
                elif indice == 'a':
                    for file in files_sorted:
                        download_file(service, file['id'], file['name'], output_folder)
                    break
                
                if indice == '0':
                    folder_stack.pop()
                    folder_id = folder_stack.peek()
                    save_pickle('folders.pickle', folder_stack)
                    continue
                
                try:
                    file = files_sorted[int(indice) - 1]
                except (IndexError, ValueError):
                    continue
                
                
                if file['mimeType'] == 'application/vnd.google-apps.folder':
                    folder_stack.push(file['id'])
                    folder_id = folder_stack.peek()
                    save_pickle('folders.pickle', folder_stack)
                    continue
                else:
                    download_file(service, file['id'], file['name'], output_folder)

            
        elif choice == '2':
            print("Seleciona a pasta que deseja salvar seus arquivos:")
            choose = choose_download_folder()
            if choose is not None:
                output_folder = choose
            
        elif choice == '3':
            clear()
            print("\n".join([
                "Tutorial:",
                "- Digite 'q' para cancelar ou voltar a qualquer momento.",
                "- Na opção 1 (Listar itens da pasta atual), você pode navegar entre as pastas.",
                "- Selecione o indice da pasta que deseja selecionar.",
                "- Para voltar uma pasta, escolha o indice 0.",
                "- Você pode baixar 1 ou todos os arquivos.",
                "- As pastas não serão baixadas, apenas os arquivos.",
                "- Escolha onde deseja salvar os arquivos."
            ]))
            input("\nAperte enter para continuar...")
            
        elif choice == '4':
            return
        
        
        # print("Listando arquivos no Drive...")
        # if folder_id is None:
        #     files = list_root_files(service)
        
        # if not files:
        #     return print("No files found.")
        
        
        
        # confirm = input("Deseja baixar os arquivos? (s/n): ")
        # if confirm.lower() == 's':
        #     print("Downloading files...")
        #     for file in files:
        #         # download_file(service, file['id'], file['name'], output_folder)
        #         break
    

if __name__ == '__main__':
    main()
