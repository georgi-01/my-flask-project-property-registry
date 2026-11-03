from sqlalchemy import func, or_, select

from app.models import Agent
from app.repositories.base import Repository


class AgentRepository(Repository):
    def get(self, agent_id):
        return self.session.get(Agent, agent_id)

    def search(self, text=""):
        stmt = select(Agent).order_by(Agent.name)
        if text:
            pattern = f"%{text}%"
            stmt = stmt.where(or_(Agent.name.ilike(pattern), Agent.office.ilike(pattern), Agent.email.ilike(pattern)))
        return list(self.session.scalars(stmt))

    def add(self, agent):
        self.session.add(agent)
        self.session.commit()
        self.session.refresh(agent)
        return agent

    def commit(self):
        self.session.commit()

    def delete(self, agent):
        self.session.delete(agent)
        self.session.commit()

    def count(self):
        return self.session.scalar(select(func.count()).select_from(Agent)) or 0
