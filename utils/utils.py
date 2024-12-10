import sys
import time
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
import os, io, pickle
import subprocess
import platform
from tkinter.filedialog import askdirectory
from PIL import Image
from multiprocessing import Pool
if platform.system() == 'Windows':
    import msvcrt
else:
    import termios
    import tty


SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def authenticate():
    """Autentica o usuário e retorna o serviço da API do Google Drive."""
    creds = open_pickle('pickle/token.pickle', None)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                save_pickle('pickle/token.pickle', None)
                return authenticate()
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                SCOPES,
                redirect_uri='http://localhost:58273/' 
            )
            creds = flow.run_local_server(port=58273)
            
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
            print(f"Downloading {file_name}: {int(status.progress() * 100)}%")
        print(f"Download de {file_name} concluido")

    try:
        with Image.open(file_path) as img:
            img = img.convert("RGB") 
            img.save(file_path, "JPEG", quality=quality)
            print(f"{file_name} compactada e salva")
        
    except Exception:
        return

def tecla_pressionada():
    if platform.system() == 'Windows':
        # Windows version using msvcrt
        return msvcrt.getch().decode()  # msvcrt.getch() returns a byte, so we decode it to string
    else:
        # Unix-like systems (Linux/macOS) version using termios and tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def download_files(service, files_sorted, output_folder):
    with Pool(4) as pool:
        for file in files_sorted:
            if not is_folder(file):
                pool.apply_async(download_file, (service, file['id'], file['name'], output_folder))
           
        while True:
            # if keyboard.is_pressed('q'):
            if tecla_pressionada() == 'q':
                pool.terminate()    
                return
            time.sleep(0.05)

def output_folder_exists(output_folder):
    return os.path.exists(output_folder)

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
        if is_folder(file):
            files_sorted.append(file)
        else:
            files_sorted.insert(0, file)
        
    return files_sorted


def print_files(files):
    for idx, file in enumerate(files, start=1):
        if is_folder(file):
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
        

def verify_output_folder(output_folder):
    if output_folder is None or not output_folder_exists(output_folder):
        print("Seleciona a pasta que deseja salvar seus arquivos:")
        output_folder = choose_download_folder()
        save_pickle('pickle/out_path.pickle', output_folder)
    
    return output_folder

def is_folder(file) -> bool:
    return file['mimeType'] == 'application/vnd.google-apps.folder'