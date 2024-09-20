import time
import os
import copy
import json


class ChatMessage:
    def __init__(self, sender, message="", unixTime=None):
        self.sender = sender
        self.message = message
        self.unixTime = unixTime if unixTime is not None else time.time()

    def getStr(self):
        result = time.strftime("%H:%M:%S", time.localtime(self.unixTime)) + " " + self.sender + ": " + self.message + "\n"
        return result

    def to_dict(self):
        """Сериализация объекта в словарь."""
        return {
            'sender': self.sender,
            'message': self.message,
            'unixTime': self.unixTime
        }

    @staticmethod
    def from_dict(data):
        """Десериализация из словаря в объект ChatMessage."""
        return ChatMessage(data['sender'], data['message'], data['unixTime'])


class ChatHistory:
    def __init__(self, existanceTime=3600/2):
        self.ChatMessages = []
        self.creationTimeUnix = time.time()
        self.expirationTimeUnix = self.creationTimeUnix + existanceTime
        self._iter_index = 0

    def add(self, sender, message):
        self.ChatMessages.append(ChatMessage(sender, message))

    def last(self):
        return self.ChatMessages[-1].getStr() if self.ChatMessages else None

    def save(self, filePath, fileName):
        with open(filePath + fileName, "w") as file:
            json.dump(self.to_dict(), file)  # Сохраняем историю в JSON

    @staticmethod
    def load(filePath, fileName):
        with open(filePath + fileName, "r") as file:
            data = json.load(file)
            chat_history = ChatHistory()
            chat_history.from_dict(data)  # Заполняем историю данными из файла
            return chat_history

    def to_dict(self):
        """Сериализация объекта в словарь."""
        return {
            'ChatMessages': [msg.to_dict() for msg in self.ChatMessages],
            'creationTimeUnix': self.creationTimeUnix,
            'expirationTimeUnix': self.expirationTimeUnix
        }

    def from_dict(self, data):
        """Десериализация из словаря в объект ChatHistory."""
        self.creationTimeUnix = data['creationTimeUnix']
        self.expirationTimeUnix = data['expirationTimeUnix']
        self.ChatMessages = [ChatMessage.from_dict(msg) for msg in data['ChatMessages']]

    def __getitem__(self, index):
        return self.ChatMessages[index]

    def __iter__(self):
        self._iter_index = 0
        return self

    def __next__(self):
        if self._iter_index < len(self.ChatMessages):
            result = self.ChatMessages[self._iter_index]
            self._iter_index += 1
            return result
        else:
            raise StopIteration

    def get_history(self):
        # Преобразуем сообщения в формат, ожидаемый в importHistory
        return [{'role': msg.sender, 'content': msg.message} for msg in self.ChatMessages]



class Api:
    def __init__(self, host, url="/", token="", method="POST", name=""):
        # Инициализация всех параметров API
        self.url = url
        self.host = host
        self.token = token
        self.method = method
        self.name = name

    def setUrl(self, url):
        self.url = url

    def setHost(self, host):
        self.host = host

    def setToken(self, token):
        self.token = token

    def setMethod(self, method):
        self.method = method

    def setName(self, name):
        self.name = name


class SuperVisor:
    def __init__(self, path, days=30):
        # Инициализация с заданием пути и времени обратного отсчёта
        self.path = path
        self.__countdownStart = days * 24 * 60 * 60
        self.countdown = copy.copy(self.__countdownStart)

    def setPath(self, path):
        # Установка пути
        self.path = path
        return self.path

    def setCountdown(self, days=0, hours=0, minutes=0, seconds=0):
        # Установка обратного отсчёта в секундах
        self.__countdownStart = days * 24 * 60 * 60 + hours * 60 + minutes * 60 + seconds
        self.countdown = copy.copy(self.__countdownStart)
        return self.__countdownStart

    def getCountdown(self):
        # Возвращаем текущее значение обратного отсчёта
        return self.countdown

    def watch(self):
        # Функция проверки и удаления старых файлов
        deleteCounter = 0
        if self.countdown > 0 or self.__countdownStart <= 0:
            return 0
        for path in self.path:
            files = [entry.path for entry in os.scandir(path) if entry.is_file()]
            for file in files:
                modificationTime = os.path.getmtime(file)
                # Проверяем, если файл старше чем значение отсчёта, то удаляем его
                if modificationTime < time.time() - self.countdown:
                    os.remove(file)
                    deleteCounter += 1
                    print(f"Deleted file: {file}")
        self.countdown = self.__countdownStart
        return deleteCounter

    def reset(self):
        # Сброс всех параметров
        self.countdown = 0
        self.__countdownStart = -1
        self.path = []

