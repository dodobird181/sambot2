import pickle


class StrategyFactory:
    """
    For creating and retrieving client bot objects from the database.
    """

    def create(self): ...

    def retrieve(self, id): ...


class ClientBot:
    """ """
