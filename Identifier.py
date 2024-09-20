

class IDPool:
    def __init__(self, max_id):
        """
        Инициализация пула ID с максимальным числом ID.
        :param max_id: Максимальное количество доступных ID.
        """
        self.free_ids = set(range(1, max_id + 1))  # Свободные ID
        self.issued_ids = {}  # Словарь для хранения выданных ID {ID: (IP, User-Agent)}

    def getId(self, ip, user_agent):
        """
        Выдача ID для заданной комбинации IP и User-Agent.
        :param ip: IP пользователя.
        :param user_agent: User-Agent пользователя.
        :return: ID.
        """
        # Проверяем, не выдан ли уже ID для этого IP и User-Agent
        for id_, (stored_ip, stored_ua) in self.issued_ids.items():
            if stored_ip == ip and stored_ua == user_agent:
                return str(id_)

        # Если свободные ID доступны, выдаем новый
        if self.free_ids:
            new_id = self.free_ids.pop()
            self.issued_ids[new_id] = (ip, user_agent)
            return str(new_id)
        else:
            raise Exception("No free IDs available")

    def releaseId(self, id_):
        """
        Освобождает ID, возвращая его в пул.
        :param id_: ID для освобождения.
        """
        id_=int(id_)
        if id_ in self.issued_ids:
            del self.issued_ids[id_]
        self.free_ids.add(id_)

    def getInfo(self, id_):
        """
        Получение информации об IP и User-Agent для заданного ID.
        :param id_: ID для поиска.
        :return: Кортеж (IP, User-Agent), если ID существует, иначе None.
        """
        return self.issued_ids.get(id_)

    def takeId(self, id_, ip, user_agent):
        """
        Запрашивает конкретный ID, если он свободен, и выдает его для заданного IP и User-Agent.
        :param id_: Запрашиваемый ID.
        :param ip: IP пользователя.
        :param user_agent: User-Agent пользователя.
        :return: Запрашиваемый ID, если он свободен, иначе исключение.
        """
        if id_ in self.free_ids:
            self.free_ids.remove(id_)
            self.issued_ids[id_] = (ip, user_agent)
            return str(id_)
        elif id_ in self.issued_ids:
            raise Exception(f"ID {id_} уже выдан")
        else:
            raise Exception(f"ID {id_} вне допустимого диапазона")