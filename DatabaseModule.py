import json
import time
import os
from Utility import ChatHistory

class Person:
    def __init__(self,Name=""):
        self.fields=dict()
        self.fields['Name']=Name

    def to_dict(self):
        return self.fields


class UserDatabase:
    user_counter=0
    base_dir="Database"

    def __init__(self,assigned_ID):
        assigned_ID=str(assigned_ID)
        os.makedirs(UserDatabase.base_dir, exist_ok=True)
        self.user_id = assigned_ID
        self.user_info = Person(assigned_ID)
        self.chat_log = ChatHistory()
        self.last_seen = time.time()
        self.db_file_name = self.user_id+".json"
        self.db_full_path = os.path.join(UserDatabase.base_dir, self.db_file_name)
        self.additional_info = dict()
        UserDatabase.user_counter += 1

    def toDict(self):
        return {
            'user_id': self.user_id,
            'user_info': self.user_info.to_dict(),
            'chat_log': self.chat_log.to_dict(),
            'last_seen': self.last_seen,
            'additional_info': self.additional_info
        }

    @classmethod
    def fromDict(cls, data):
        obj = cls(data['user_id'])
        obj.user_info = Person( data['user_info']['Name'])
        obj.chat_log = ChatHistory()
        obj.last_seen = data['last_seen']
        obj.additional_info = data['additional_info']
        return obj

    def save(self):
        with open(self.db_full_path,"w+") as file:
            fields__=self.toDict()
            json.dump(fields__,file)



    @staticmethod
    def load(FilePath):
        try:
            with open(FilePath, "r") as file:
                fields__ = json.load(file)
                return UserDatabase.fromDict(fields__)
        except FileNotFoundError:
            print(f"Файл {FilePath} не найден.")
            return None


def load_objects_from_folder(folder_path="Database"):
    objects_dict = dict()
    counter=0
    # Проходим по всем файлам в указанной папке
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            # Формируем полный путь к файлу
            file_path = os.path.join(folder_path, filename)
            try:
                obj = UserDatabase.load(file_path)
                # Добавляем объект в словарь по его user_id
                objects_dict[obj.user_id] = obj
                counter+=1
            except Exception as e:
                print(f"Ошибка при загрузке {file_path}: {e}")

    # Возвращаем словарь с загруженными объектами
    print(f"Найдено {counter} файлов с данными пользователей")
    return objects_dict

Users=load_objects_from_folder()

if __name__=="__main_!_":
    #db=UserDatabase.load("Database/1.json")
    users=load_objects_from_folder()
    for user in users.values():
        print(user.user_id)
