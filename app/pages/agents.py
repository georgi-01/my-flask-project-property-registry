from flask import abort, flash, redirect, render_template, request, url_for

from app.errors import ValidationError
from app.pages import bp
from app.pages.forms import agent_from_form, namespace, show_errors
from app.services.agents import AgentService
from app.services.listings import ListingService

agents = AgentService()
listings = ListingService()


def load_agent(agent_id):
    agent = agents.get(agent_id)
    if agent is None:
        abort(404)
    return agent


@bp.route("/agents")
def agent_index():
    text = request.args.get("q", "")
    return render_template("agents.html", agents=agents.search(text), q=text)


@bp.route("/agents/new", methods=["GET", "POST"])
def new_agent():
    form = namespace({"name": "", "phone": "", "email": "", "office": ""})
    if request.method == "POST":
        data = agent_from_form(request.form)
        form = namespace(data)
        try:
            added = agents.create(data)
        except ValidationError as error:
            show_errors(error)
        else:
            flash(f"Брокерът {added.name} е добавен.", "success")
            return redirect(url_for("pages.agent_detail", agent_id=added.id))
    return render_template("agent_form.html", title="Нов брокер", agent=form)


@bp.route("/agents/<int:agent_id>")
def agent_detail(agent_id):
    agent = load_agent(agent_id)
    own = listings.search({"agent_id": agent_id})
    return render_template("agent.html", agent=agent, listings=own)


@bp.route("/agents/<int:agent_id>/edit", methods=["GET", "POST"])
def edit_agent(agent_id):
    agent = load_agent(agent_id)
    if request.method == "POST":
        data = agent_from_form(request.form)
        try:
            agents.update(agent_id, data)
        except ValidationError as error:
            show_errors(error)
            agent = namespace(data)
            agent.id = agent_id
        else:
            flash("Промените са запазени.", "success")
            return redirect(url_for("pages.agent_detail", agent_id=agent_id))
    return render_template("agent_form.html", title="Редакция на брокер", agent=agent)


@bp.route("/agents/<int:agent_id>/delete", methods=["POST"])
def delete_agent(agent_id):
    agent = load_agent(agent_id)
    try:
        agents.delete(agent_id)
    except ValidationError as error:
        show_errors(error)
        return redirect(url_for("pages.agent_detail", agent_id=agent_id))
    flash(f"Брокерът {agent.name} е изтрит.", "success")
    return redirect(url_for("pages.agent_index"))
