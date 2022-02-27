from enum import Enum


class Role(Enum):
    LEADER = 1
    GAMER = 2


class Answer:
    def __init__(self, aid=0, text=str()):
        self.authorID = aid
        self.text = text
        self.votes = set()

    def is_right(self):
        return self.authorID == -1

    def set_right(self):
        self.authorID = -1

    def votes_count(self):
        return len(self.votes)

    def empty(self) -> bool:
        return len(self.text) == 0


class Gamer:
    def __init__(self, uid=0, user=None, role=Role.GAMER):
        self.id = uid
        self.user = user
        self.answer = Answer()
        self.role = role

    def is_leader(self):
        return self.role == Role.LEADER

    def username(self):
        return self.user["name"]
