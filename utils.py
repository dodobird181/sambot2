import uuid

import settings


class Factory:
    """
    Base factory class for database objects.
    """

    @staticmethod
    def path(obj_or_id) -> str:
        """
        Get the database path for a given object, or it's uuid if known.
        """
        id = obj_or_id if isinstance(obj_or_id, (str, uuid.UUID)) else obj_or_id.id
        return f"{settings.PICKLE_DB_PATH}{id}.pkl"
