# # #
# # # Tokarev Vadim 20.05.2024
# # #
# # # Baggins Coffee
# # # 

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
from datetime import datetime, date, time
import pprint as pp

SCOPES = ['https://www.googleapis.com/auth/drive']
CLIENT_SECRET_FILE = 'client_secret.json'
TOKEN_PICKLE_FILE = '#token.pickle'


def authenticate():
    creds = None
    if os.path.exists(TOKEN_PICKLE_FILE):
        with open(TOKEN_PICKLE_FILE, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)
        with open(TOKEN_PICKLE_FILE, 'wb') as token:
            pickle.dump(creds, token)

    return creds


credentials = authenticate()
service = build('drive', 'v3', credentials=credentials)


def getFileName(FILE_ID):
    # Функция для получения name файла
    # Принимает на вход id файла
    try:
        result = service.files().get(fileId=FILE_ID).execute()['name']
        return result
    except Exception as e:
        print(e)


def getFileId(FILE_NAME):
    # Функция для получения id файла
    # Принимает на вход name файла
    try:
        result = ''
        file = service.files().list(
            q='name="'+FILE_NAME + '"',
             fields='files(id)'
             ).execute()

        for x in file.get('files'):
            result = x['id']

        if result is None:
            print(result)

        return result
    except Exception as e:
        print(e)

#
# ПЕРВОЕ ЗАДАНИЕ
#
def getArrayOfDocAndUsers():

    # Инициализация списка формата List[x][y]
    # Где x - элемент списка
    # y - значение элемента списка
    # элемент списка - [Название файла],[Идентификатор пользователя]
    listOfUsersAndDoc = []

    # Идентификатор корневой папки 'Baggins Coffee'
    FOLDER_ID = '1muM5T5BKseduTE1y6Z4VnviIbqdJQ6Hz'
    # Текущая дата для сравнения с датой создания
    CURRENT_DATE = datetime.today().date()
    # Токен следующей страницы для автоматического перехода между ними
    USERS_PAGE_TOKEN = None
    FILES_PAGE_TOKEN = None
    # Собственный идентификатор
    MY_ID = service.about().get(fields="user").execute()['user']['permissionId']

    # Цикл для прохода между всеми страницами
    while True:

        # Список всех пользователей
        # id - идентификатор пользователя
        listOfUsers = service.permissions().list(
            fileId=FOLDER_ID,
            fields='nextPageToken, permissions(id, type, displayName)',
            pageToken=USERS_PAGE_TOKEN
        ).execute()

        for user in listOfUsers.get('permissions'):
            # Проверка что в списке находится пользователь
            # А не разрешение
            # и что пользователь не является собственником
            if user['type'] != 'user' or user['id'] == MY_ID:
                continue

            # Запись идентификатора пользователя в фильтр-запрос
            USER_ID = user['id']
            # Имя пользователя для записи в список
            USER_NAME = user["displayName"]
            # Запрос для файлов где пользователь является владельцем
            QUERY = "'"+USER_ID+"' in owners"

            while True:

                # Список всех файлов
                # id - Идентификатор файла
                # modifiedTime - дата последнего изменения
                listOfFiles = service.files().list(
                    q=QUERY,
                    fields='files(id, name, createdTime)',
                    pageToken=FILES_PAGE_TOKEN
                ).execute()

                for file in listOfFiles.get('files'):

                    # Форматирование даты создание в [ГГГ:ММ:ДД]
                    CREATE_DATE = datetime.strptime(
                        file['createdTime'].split('T')[0], '%Y-%m-%d').date()
                    # Инициализация разницы между текущей датой и датой создания
                    DIFFERENT_DAYS = CURRENT_DATE - CREATE_DATE

                    # Проверка условия в разницы в 7 дней
                    if int(DIFFERENT_DAYS.days) > 7:
                        # Инициализация элемента списка и добавление в массив
                        stringResult = [str(file['name']), USER_NAME]
                        listOfUsersAndDoc.append(stringResult)

                # Установка токена следущей страницы файлов
                # Если нет - None
                FILES_PAGE_TOKEN = listOfFiles.get('nextPageToken', None)

                # Проверка токена, выход из цикла
                if FILES_PAGE_TOKEN is None:
                    break

        # Установка токена следущей страницы пользователей
        # Если нет - None
        USERS_PAGE_TOKEN = listOfUsers.get('nextPageToken', None)

        if USERS_PAGE_TOKEN is None:
            break

    # Возвращение списка
    return listOfUsersAndDoc

#
# ВТОРОЕ ЗАДАНИЕ
#
def createCopyOfFile(fileName, parentFolder, mimeType=None):
    # Функция для создания копии файла
    # принимает на вход следующие параметры
    # fileName - имя файла
    # parentFolder - родительская папка файла
    # mimeType - по умолчанию None - тип файла
    try:
        # Если mimeType не установлен
        # значит файл - папка
        if mimeType is None:
            mimeType = 'application/vnd.google-apps.folder'

        parentFolder = getFileId(parentFolder)
        newFileName = '[Copy] ' + fileName

        file_metadata = {
            "name": [newFileName],
            "mimeType": [mimeType],
            "parents": [parentFolder]
        }
        file = service.files().create(
            body=file_metadata,
            fields="id"
        ).execute()

    except Exception as e:
        print(e)


def createCopyOfFoldersAndFiles(OWNER_NAME, START_FOLDER):
    # OWNER_NAME - имя владельца
    # START_FOLDER - папка, с которой начинается поиск

    TOP_LEVEL = START_FOLDER
    # Под TOP_LEVEL понимается самая верхняя в функции папка, что бы не создавать ее копию

    # функция-рекурсия
    # создана специально для того, что бы TOP_LEVEL был статичным и
    # не изменялся при рекурсии последующего кода
    def recursionOfFolders(OWNER_NAME, START_FOLDER):
        # Проверка исходной папки на явление корневой
        if (START_FOLDER == TOP_LEVEL):
            # В случае если папка корневая, копией папки являются текущая папка
            FOLDER_COPY = START_FOLDER
        else:
            # В противном случае добавляется метка [COPY]
            FOLDER_COPY = '[COPY] ' + START_FOLDER

        # Получение id текущей папки
        PARENT_FOLDER_ID = getFileId(START_FOLDER)
        # Токен для перехода между страницами результата поиска
        PAGE_TOKEN = None

        # mimeType папки
        MIME_TYPE_FOLDER = 'application/vnd.google-apps.folder'

        # Получение списка файлов в папке startFolder где владелец - ownerName
        while True:

            # Получение списка файлов в папке startFolder
            # По фильтру:
            # родительская папка - PARENT_FOLDER_ID
            # имя владельца - OWNER_NAME
            # находится в корзине - false
            query = "parents='"+PARENT_FOLDER_ID+"' and '" + OWNER_NAME + "' in owners and trashed = false"
            listOfFiles = service.files().list(
                q=query,
                fields='files(name, id, parents, owners(displayName,permissionId),mimeType)',
                pageToken=PAGE_TOKEN
            ).execute()

            # Проходим 1 раз через все файлы для создания копий папок
            for file in listOfFiles.get('files'):
                # Если файл - папка, то создаем копию папки в копии родительской папки
                if file['mimeType'] == MIME_TYPE_FOLDER:
                    createCopyOfFile(file['name'], FOLDER_COPY)
                    print(file['name'] + ' - копия папки создана в папке ' + FOLDER_COPY)
                    # Запускаем рекурсию для папки
                    recursionOfFolders(OWNER_NAME, file['name'])

            # Проходим второй раз через все файлы для создания копий файлов
            for file in listOfFiles.get('files'):
                if file['mimeType'] != MIME_TYPE_FOLDER:
                    createCopyOfFile(
                        file['name'], FOLDER_COPY, file['mimeType'])
                    print(file['name'] + ' - копия файла создана в папке ' + FOLDER_COPY)

            PAGE_TOKEN = listOfFiles.get('nextPageToken', None)
            if PAGE_TOKEN is None:
                break

    recursionOfFolders(OWNER_NAME, START_FOLDER)

#
# ТРЕТЬЕ ЗАДАНИЕ
#
def changeOwner(FILE_ID, MY_PERMISSION_ID):
    # Почта текущего аккаунта
    MY_EMAIL = service.about().get(fields="user").execute()['user']['emailAddress']

    # Создание нового разрешения для файла
    # тип - пользователь
    # изначальная роль - редактор
    # почта - почта
    # transferOwnership - передать владение файлом пользователю - false
    # поскольку пользователь - редактор
    NEW_PERMISSION = {
        'type': 'user',
        'role': 'writer',  
        'emailAddress': MY_EMAIL
    }
    service.permissions().create(
        fileId=FILE_ID,
        body=NEW_PERMISSION,
        transferOwnership=False
    ).execute()

    # Обновление разрешение до владельца
    # transferOwnership - true, поскольку роль пользователя - владелец
    service.permissions().update(
        fileId=FILE_ID,
        permissionId=MY_PERMISSION_ID,
        transferOwnership=True,
        body={'role': 'owner'}
    ).execute()
    print('Установлен статус - "владелец" для файла "' + getFileName(FILE_ID) + '"')


def acceptAllOwnershipRequests():
    # Получение идентификатора Permission владельца аккаунта
    MY_PERMISSION_ID = service.about().get(fields="user").execute()['user']['permissionId']
    # Инициализация списка всех файлов
    listOfFiles = service.files().list(fields='files(id,name)').execute()
    for file in listOfFiles.get('files'):
        try:
            # Получение значение pendingOwner файла
            isPendingOwner = service.permissions().get(
                permissionId=MY_PERMISSION_ID,
                fileId=file['id'],
                fields='pendingOwner'
            ).execute()['pendingOwner']

            # pendingOwner - булевое поле файла, которое определяет
            # является ли пользователь ожидающим владельцем

            # Если пользователь является ожидающим владельцем
            # Вызов функции changeOwner
            if isPendingOwner is True:
                changeOwner(file['id'], MY_PERMISSION_ID)
                print(file['name'] + ' - разрешено для изменения')
            else:
                print(file['name'] + ' - запрещено для изменения')
        except Exception as e:
            print(file['id'] + ' - ошибка получения значения')

# Первое задание
Array = getArrayOfDocAndUsers()
pp.pprint(Array)
# Второе задание
createCopyOfFoldersAndFiles('kikorikisuai@gmail.com', 'Baggins Coffee')
# Третье задание
acceptAllOwnershipRequests()