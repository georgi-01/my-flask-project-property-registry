from app.repositories.events import EventRepository


class EventService:
    def __init__(self, repo=None):
        self.repo = repo or EventRepository()

    def latest(self, limit=100):
        return self.repo.latest(limit)
