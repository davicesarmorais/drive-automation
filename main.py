from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
import io
from tkinter import Tk
from tkinter.filedialog import askdirectory
from PIL import Image
import time

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate():
    """Autentica o usuário e retorna o serviço da API do Google Drive."""
    try:
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    except FileNotFoundError:
        creds = None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                SCOPES,
                redirect_uri='http://localhost:8080/' 
            )
            creds = flow.run_local_server(port=8080)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
            
    return build('drive', 'v3', credentials=creds)

def list_files_in_folder(service, folder_id):
    """Lista arquivos em uma pasta específica no Google Drive."""
    query = f"'{folder_id}' in parents and mimeType contains 'image/'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    return results.get('files', [])

def download_file(service, file_id, file_name, output_folder, quality = 80):
    """Faz o download de um arquivo do Google Drive."""
    file_path = os.path.join(output_folder, file_name)
    request = service.files().get_media(fileId=file_id)
    with io.FileIO(file_path, 'wb') as file:
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Downloading {file_name}: {int(status.progress() * 100)}%")
    print(f"{file_name} downloaded to {file_path}")
    try:
        with Image.open(file_path) as img:
            compressed_file_path = os.path.join(output_folder, f"compressed_{file_name}")
            
            img = img.convert("RGB") 
            img.save(compressed_file_path, "JPEG", quality=quality)
            print(f"{file_name} compactada e salva em {compressed_file_path}")
    except Exception as e:
        print(f"Erro ao compactar {file_name}: {e}")


def choose_download_folder():
    """Permite ao usuário escolher o diretório de download."""
    root = Tk()
    root.withdraw()  
    folder_selected = askdirectory(title="Selecione a pasta para salvar os arquivos")
    if not folder_selected:
        print("Nenhuma pasta selecionada. Usando o diretório atual como padrão.")
        return os.getcwd() 
    
    return folder_selected

def list_root_files(service):
    query = "trashed = false"  
    results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()
    files = results.get('files', [])
    return files

def filter_by_type(file):
    lista = ['application/vnd.google-apps.folder',
                'application/x-compressed',
                'application/x-zip-compressed',
                'image/png', 'image/jpeg', 'image/jpg']
    
    if file['mimeType'] in lista:
        return True
    return False


def main():
    # TODO: Salvar a pasta que o usuário estava
    # TODO: Opção de voltar uma pasta????????? como OMG PILHA USAGE
    # TODO: Perguntar se quer baixar um arquivo ou todos
    # TODO: Opcao de entrar em uma pasta (e salva-la)
    # TODO: Se o id da pasta for None usar o list_root_files
    # TODO: Supressor de imagem
    
    # ID da pasta no Google Drive (substitua pelo ID real)
    # folder_id = '0dads3213adada'
    folder_id = None
    
    print("Seleciona a pasta que quer salvar seus arquivos:")
    time.sleep(1)
    output_folder = choose_download_folder()

    service = authenticate()

    print("Listando arquivos no Drive...")
    if folder_id is None:
        files = list_root_files(service)
    
    if not files:
        print("No files found.")
        return
    
    files_filtered = filter(filter_by_type, files)
    files_sorted = []
    for file in files_filtered:
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            files_sorted.insert(0, file)
        
        elif file['mimeType'] in ['application/x-compressed', 'application/x-zip-compressed']:
            files_sorted.insert(0, file)
        
        elif file['mimeType'] in ['image/png', 'image/jpeg', 'image/jpg']:
            files_sorted.append(file)
            
    for idx, file in enumerate(files_sorted, start=1):
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            print(f"[{str(idx).zfill(2)}] FOLDER: {file['name']}")
        elif file['mimeType'] in ['application/x-compressed', 'application/x-zip-compressed']:
            print(f"[{str(idx).zfill(2)}] ZIP: {file['name']}")
        else:
            print(f"[{str(idx).zfill(2)}] {file['mimeType'].split('/')[1].upper()}: {file['name']}")
    
    confirm = input("Deseja baixar os arquivos? (s/n): ")
    if confirm.lower() == 's':
        print("Downloading files...")
        for file in files:
            # download_file(service, file['id'], file['name'], output_folder)
            break
    

if __name__ == '__main__':
    main()
