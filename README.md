### Configuração
1. Vá para [Google Cloud Console](https://console.cloud.google.com/).
2. Crie um projeto e ative a API Google Drive.
3. Baixe o arquivo `credentials.json` e coloque-o no diretório raiz.
4. Em _IDs do cliente OAuth_ 2.0 coloque em _URIs de redirecionamento autorizados_ essa url: `http://localhost:58273/`

5. Instale as dependências: `pip install -r requirements.txt`


- Windows: `python drive.py`
- Linux: `python3 drive.py`

*Dependendo do usuário, disponibilizo o arquivo*
