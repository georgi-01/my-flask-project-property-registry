from sqlalchemy.exc import IntegrityError

from app.errors import ValidationError
from app.models import Agent
from app.parsing import clean_text
from app.repositories.agents import AgentRepository
from app.repositories.listings import ListingRepository


class AgentService:
    def __init__(self, repo=None, listings=None):
        self.repo = repo or AgentRepository()
        self.listings = listings or ListingRepository()

    def get(self, agent_id):
        return self.repo.get(agent_id)

    def search(self, text=""):
        return self.repo.search(clean_text(text))

    def create(self, data):
        cleaned = self.validate(data)
        agent = Agent(**cleaned)
        try:
            return self.repo.add(agent)
        except IntegrityError:
            self.repo.session.rollback()
            raise ValidationError("Този имейл вече се използва.") from None

    def update(self, agent_id, data):
        agent = self.repo.get(agent_id)
        if agent is None:
            return None
        cleaned = self.validate(data)
        agent.name = cleaned["name"]
        agent.phone = cleaned["phone"]
        agent.email = cleaned["email"]
        agent.office = cleaned["office"]
        try:
            self.repo.commit()
        except IntegrityError:
            self.repo.session.rollback()
            raise ValidationError("Този имейл вече се използва.") from None
        return agent

    def delete(self, agent_id):
        agent = self.repo.get(agent_id)
        if agent is None:
            return None
        if self.listings.count_for_agent(agent_id):
            raise ValidationError(f"Брокерът {agent.name} не може да бъде изтрит, защото има обяви.")
        self.repo.delete(agent)
        return agent

    def validate(self, data):
        name = clean_text(data.get("name"))
        phone = clean_text(data.get("phone"))
        email = clean_text(data.get("email")).lower()
        office = clean_text(data.get("office"))
        errors = []
        if not name:
            errors.append("Въведете име.")
        elif len(name) > 120:
            errors.append("Името трябва да е до 120 знака.")
        elif not _person_name(name):
            errors.append("Името може да съдържа само букви, интервали, тирета и апострофи.")
        if len(phone) < 6 or len(phone) > 40:
            errors.append("Въведете телефон.")
        elif not _phone(phone):
            errors.append("Телефонът може да съдържа цифри, интервали, +, - и скоби.")
        if "@" not in email or "." not in email.split("@")[-1] or " " in email or len(email) > 160:
            errors.append("Въведете валиден имейл.")
        if not office:
            errors.append("Въведете офис.")
        elif len(office) > 80:
            errors.append("Офисът трябва да е до 80 знака.")
        if errors:
            raise ValidationError(*errors)
        return {"name": name, "phone": phone, "email": email, "office": office}


def _person_name(value):
    return all(char.isalpha() or char in " -'" for char in value)


def _phone(value):
    return all(char.isdigit() or char in " +-()" for char in value)
