import time
from collections import defaultdict

class IDPool:
    def __init__(self, max_id, ttl=3600):
        """
        Инициализация пула ID с максимальным числом ID и временем жизни ID (в секундах)
        :param max_id: Максимальное количество доступных ID
        :param ttl: Время жизни ID в секундах (по умолчанию 1 час)
        """
        self.free_ids = set(range(1, max_id + 1))  # Свободные ID
        self.issued_ids = {}  # Словарь для хранения выданных ID {ID: (IP, User-Agent, время_выдачи)}
        self.ttl = ttl  # Время жизни ID (в секундах)

    def get_id(self, ip, user_agent):
        """
        Выдача ID для заданной комбинации IP и User-Agent
        :param ip: IP пользователя
        :param user_agent: User-Agent пользователя
        :return: ID
        """
        # Проверяем, не выдан ли уже ID для этого IP и User-Agent
        for id_, (stored_ip, stored_ua, issue_time) in self.issued_ids.items():
            if stored_ip == ip and stored_ua == user_agent and not self.is_expired(id_):
                return id_

        # Если свободные ID доступны, выдаем новый
        if self.free_ids:
            new_id = self.free_ids.pop()
            self.issued_ids[new_id] = (ip, user_agent, time.time())
            return new_id
        else:
            raise Exception("No free IDs available")

    def release_id(self, id_):
        """
        Освобождает ID, возвращая его в пул
        :param id_: ID для освобождения
        """
        if id in self.issued_ids:
            del self.issued_ids[id]
        self.free_ids.add(id_)

    def is_expired(self, id_):
        """
        Проверка, истекло ли время жизни ID
        :param id_: ID для проверки
        :return: True, если ID истек, иначе False
        """
        if id_ in self.issued_ids:
            issue_time = self.issued_ids[id_][2]
            if time.time() - issue_time > self.ttl:
                # Если время жизни истекло, освобождаем ID
                self.release_id(id_)
                return True
        return False

    def cleanup(self):
        """
        Очистка истекших ID
        """
        for id_ in list(self.issued_ids.keys()):
            self.is_expired(id_)
