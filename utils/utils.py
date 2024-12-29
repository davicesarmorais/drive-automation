from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
import os, time
import io, pickle
import subprocess
import platform
from tkinter.filedialog import askdirectory
from PIL import Image
from multiprocessing import Pool
import threading
from pynput import keyboard


SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


def count_down(timeout, stop_event):
    for i in range(timeout, -1, -1):
        if stop_event.is_set():
            print()
            clear()
            break
        time.sleep(1)
        print(f"Tempo restante: {i:2d}", end='\r')

        
def authenticate(change_account=False):
    """Autentica o usuário e retorna o serviço da API do Google Drive."""
    creds = open_pickle('token.pickle', None)
    if change_account:
        creds = None    
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                save_pickle('token.pickle', None)
                return authenticate()
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                SCOPES,
                redirect_uri='http://localhost:58273/' 
            )

            try:
                timout = 60
                stop_event = threading.Event()
                thread = threading.Thread(target=count_down, args=(timout, stop_event))
                thread.start()
                
                creds = flow.run_local_server(
                    port=58273,
                    timeout_seconds=timout,
                    access_type='offline'
                )
            except Exception:
                return None
            finally:
                stop_event.set()
                thread.join()
        
        save_pickle('token.pickle', creds)
            
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


stop_loop = False

def on_press(key):
    global stop_loop
    try:
        if key.char == 'q':
            stop_loop = True
    except AttributeError:
        pass  # Ignora outras teclas que não são caracteres


def remove_empty_files(output_folder):
    for filename in os.listdir(output_folder):
        file_path = os.path.join(output_folder, filename)
        if os.path.isfile(file_path) and os.path.getsize(file_path) == 0:
            os.remove(file_path)


def download_files(service, files, output_folder):
    global stop_loop
    with Pool(4) as pool:
        files_to_download = [(service, file['id'], file['name'], output_folder) for file in files if not is_folder(file)]
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        results = pool.starmap_async(download_file, files_to_download)
        
        while not results.ready():
            if stop_loop:
                listener.stop()
                print("Cancelando downloads aguarde.")
                pool.terminate()
                pool.join()
                stop_loop = False
                break
            time.sleep(0.1)  # Pequena pausa para evitar consumo excessivo de CPU

        if results.ready():
            print("Todos os downloads foram concluídos.")
            pool.close()
            pool.join()
            listener.stop()

        remove_empty_files(output_folder)

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
            orderBy="viewedByMeTime asc, name",
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
        "mimeType = 'application/vnd.google-apps.folder'"
    )
    files = []
    page_token = None

    while True:
        response = service.files().list(
            q=query,
            orderBy="viewedByMeTime asc, name",
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

            
def open_pickle(file_name, default = None):
    DIRETORIO_PROJETO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if not os.path.exists(os.path.join(DIRETORIO_PROJETO, 'pickle')):
        os.mkdir(os.path.join(DIRETORIO_PROJETO, 'pickle'))
    path = os.path.join(DIRETORIO_PROJETO, 'pickle', file_name)
    try:
        with open(path, 'rb') as file:
            return pickle.load(file)
    except FileNotFoundError:
        return default

    
def save_pickle(file_name, data):
    DIRETORIO_PROJETO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if not os.path.exists(os.path.join(DIRETORIO_PROJETO, 'pickle')):
        os.mkdir(os.path.join(DIRETORIO_PROJETO, 'pickle'))
    path = os.path.join(DIRETORIO_PROJETO, 'pickle', file_name)
    with open(path, 'wb') as file:
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
        save_pickle('out_path.pickle', output_folder)
    
    return output_folder

def is_folder(file) -> bool:
    return file['mimeType'] == 'application/vnd.google-apps.folder'
