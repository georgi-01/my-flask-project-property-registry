from flask import jsonify, request, url_for

from app.api import bp, errors
from app.errors import ValidationError
from app.services.agents import AgentService

service = AgentService()


def read_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def not_found(agent_id):
    return errors(404, f"Няма брокер с номер {agent_id}.")


@bp.get("/agents")
def list_agents():
    text = request.args.get("q", "")
    return jsonify([agent.to_dict() for agent in service.search(text)])


@bp.get("/agents/<int:agent_id>")
def get_agent(agent_id):
    agent = service.get(agent_id)
    if agent is None:
        return not_found(agent_id)
    return jsonify(agent.to_dict())


@bp.post("/agents")
def create_agent():
    try:
        agent = service.create(read_body())
    except ValidationError as error:
        return errors(400, *error.args)
    return jsonify(agent.to_dict()), 201, {"Location": url_for("api.get_agent", agent_id=agent.id)}


@bp.put("/agents/<int:agent_id>")
def update_agent(agent_id):
    try:
        agent = service.update(agent_id, read_body())
    except ValidationError as error:
        return errors(400, *error.args)
    if agent is None:
        return not_found(agent_id)
    return jsonify(agent.to_dict())


@bp.delete("/agents/<int:agent_id>")
def delete_agent(agent_id):
    try:
        agent = service.delete(agent_id)
    except ValidationError as error:
        return errors(409, *error.args)
    if agent is None:
        return not_found(agent_id)
    return "", 204
