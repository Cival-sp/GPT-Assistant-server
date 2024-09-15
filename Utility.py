import time
import os
import copy

class ChatMessage:
    def __init__(self, sender, message="", unixTime=None):
        # Если unixTime не передан, используется текущее время
        self.sender = sender
        self.message = message
        self.unixTime = unixTime if unixTime is not None else time.time()

    def getStr(self):
        # Преобразуем unixTime в читаемый формат
        result = time.strftime("%H:%M:%S", time.localtime(self.unixTime)) + " " + self.sender + ": " + self.message + "\n"
        return result


class ChatHistory:
    def __init__(self):
        # Теперь ChatMessages - атрибут экземпляра, уникальный для каждого объекта
        self.ChatMessages = []


    def add(self, sender, message):
        # Добавляем новое сообщение в историю
        self.ChatMessages.append(ChatMessage(sender, message))

    def last(self):
        # Возвращаем последнее сообщение, если оно есть
        return self.ChatMessages[-1].getStr() if self.ChatMessages else None

    def save(self, filePath, fileName):
        # Сохраняем все сообщения в указанный файл
        with open(filePath + fileName, "w") as file:
            for msg in self.ChatMessages:
                file.write(msg.getStr())

    @staticmethod
    def load( filePath, fileName):
        # Читаем все строки из файла (это пример; тут можно добавить разбор строки для восстановления объектов)
        with open(filePath + fileName, "r") as file:
            return file.readlines()


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
