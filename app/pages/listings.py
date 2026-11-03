from flask import abort, flash, redirect, render_template, request, url_for

from app.errors import ValidationError
from app.pages import bp
from app.pages.forms import blank_listing, listing_from_form, namespace, show_errors
from app.services.agents import AgentService
from app.services.inquiries import InquiryService
from app.services.listings import ListingService

listings = ListingService()
agents = AgentService()
inquiries = InquiryService()


def load_listing(listing_id):
    listing = listings.get(listing_id)
    if listing is None:
        abort(404)
    return listing


@bp.route("/")
def home():
    found = listings.search({"status": "active"})
    return render_template("home.html", counts=listings.counts(), listings=found[:6])


@bp.route("/listings")
def listing_index():
    raw = request.args.to_dict()
    return render_template("listings.html", listings=listings.search(raw), filters=raw)


@bp.route("/listings/new", methods=["GET", "POST"])
def new_listing():
    form = blank_listing()
    if request.method == "POST":
        data = listing_from_form(request.form)
        form = namespace(data)
        try:
            added = listings.create(data)
        except ValidationError as error:
            show_errors(error)
        else:
            flash(f"Обявата „{added.title}“ е добавена.", "success")
            return redirect(url_for("pages.listing_detail", listing_id=added.id))
    return render_template("listing_form.html", title="Нова обява", listing=form, agents=agents.search(), locked_kind=False)


@bp.route("/listings/<int:listing_id>")
def listing_detail(listing_id):
    listing = load_listing(listing_id)
    return render_template(
        "listing.html",
        listing=listing,
        inquiries=inquiries.for_listing(listing_id),
    )


@bp.route("/listings/<int:listing_id>/edit", methods=["GET", "POST"])
def edit_listing(listing_id):
    listing = load_listing(listing_id)
    if request.method == "POST":
        data = listing_from_form(request.form)
        data["kind"] = listing.kind
        try:
            listings.update(listing_id, data)
        except ValidationError as error:
            show_errors(error)
            listing = namespace(data)
            listing.kind = data["kind"]
            listing.id = listing_id
        else:
            flash("Промените са запазени.", "success")
            return redirect(url_for("pages.listing_detail", listing_id=listing_id))
    return render_template(
        "listing_form.html",
        title="Редакция на обява",
        listing=listing,
        agents=agents.search(),
        locked_kind=True,
    )


@bp.route("/listings/<int:listing_id>/delete", methods=["POST"])
def delete_listing(listing_id):
    listing = load_listing(listing_id)
    listings.delete(listing_id)
    flash(f"Обявата „{listing.title}“ е изтрита.", "success")
    return redirect(url_for("pages.listing_index"))
