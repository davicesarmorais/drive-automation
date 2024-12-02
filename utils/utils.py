from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os, io, pickle
import subprocess
import platform
from tkinter.filedialog import askdirectory
from PIL import Image

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate():
    """Autentica o usuário e retorna o serviço da API do Google Drive."""
    creds = open_pickle('pickle/token.pickle', None)
    
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
        
        save_pickle('pickle/token.pickle', creds)
            
    return build('drive', 'v3', credentials=creds)


def download_file(service, file_id, file_name, output_folder, quality = 65):
    """Faz o download de um arquivo do Google Drive."""
    file_path = os.path.join(output_folder, file_name)
    request = service.files().get_media(fileId=file_id)
    with io.FileIO(file_path, 'wb') as file:
        print(f"Downloading {file_name}...")
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while not done:
            status,done = downloader.next_chunk()
            print(f"Downloading: {int(status.progress() * 100)}%")
    try:
        with Image.open(file_path) as img:
            # compressed_file_path = os.path.join(output_folder, f"compressed_{file_name}")
            img = img.convert("RGB") 
            img.save(file_path, "JPEG", quality=quality)
            print(f"{file_name} compactada e salva")
            
        # os.remove(file_path)
        
    except Exception as e:
        return


def choose_download_folder():
    """Permite ao usuário escolher o diretório de download."""
    folder_selected = askdirectory(title="Selecione a pasta para salvar os arquivos")
    return folder_selected if folder_selected != '' else None


def get_folder_name(service, folder_id):
    """Obtém o nome da pasta no Google Drive usando o ID da pasta."""
    file = service.files().get(fileId=folder_id, fields="name").execute()
    return file.get('name')    


def list_files_in_folder(service, folder_id):
    """Lista arquivos em uma pasta específica no Google Drive."""
    query = (
        f"'{folder_id}' in parents and "
        "(mimeType = 'application/vnd.google-apps.folder' or "
        "mimeType contains 'image/') and trashed = false"
    )
    files = []
    page_token = None

    while True:
        response = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token
        ).execute()

        files.extend(response.get('files', []))

        page_token = response.get('nextPageToken', None)
        if not page_token:
            break

    return files


def list_root_files(service):
    query = (
        "trashed = false and "
        "(mimeType = 'application/vnd.google-apps.folder' or "
        "mimeType contains 'image/')"
    )
    files = []
    page_token = None

    while True:
        response = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token
        ).execute()

        files.extend(response.get('files', []))

        page_token = response.get('nextPageToken', None)
        if not page_token:
            break

    return files


def sort_files_by_type(files):
    files_sorted = []
    for file in files:
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            files_sorted.append(file)
        else:
            files_sorted.insert(0, file)
        
    return files_sorted


def print_files(files):
    for idx, file in enumerate(files, start=1):
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            print(f"{idx:>3}. FOLDER: {file['name']}")
        else:
            print(f"{idx:>3}. IMG: {file['name']}")

            
def open_pickle(file_path, default = None):
    try:
        with open(file_path, 'rb') as file:
            return pickle.load(file)
    except FileNotFoundError:
        return default

    
def save_pickle(file_path, data):
    with open(file_path, 'wb') as file:
        pickle.dump(data, file)
        
        
def clear() -> None:
    """Limpa a tela do terminal."""
    if platform.system() == "Windows" and os.getenv("TERM") != "xterm":
        subprocess.run("cls", shell=True)
    else:
        subprocess.run("clear", shell=True)