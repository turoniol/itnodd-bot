class GameState:
    STOP = 0
    START = 1
    VOTING = 2

    def __init__(self):
        self.state = GameState.STOP

    def stop(self):
        return self.state == GameState.STOP

    def start(self):
        return self.state == GameState.START

    def voting(self):
        return self.state == GameState.VOTING
