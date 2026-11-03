from app.db import get_session


class Repository:
    def __init__(self, session_provider=None):
        self._session_provider = session_provider or get_session

    @property
    def session(self):
        return self._session_provider()
