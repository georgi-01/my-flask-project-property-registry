from flask import abort, flash, redirect, render_template, request, url_for

from app.errors import ValidationError
from app.pages import bp
from app.pages.forms import inquiry_from_form, namespace, show_errors
from app.services.inquiries import InquiryService
from app.services.listings import ListingService

inquiries = InquiryService()
listings = ListingService()


def load_inquiry(inquiry_id):
    inquiry = inquiries.get(inquiry_id)
    if inquiry is None:
        abort(404)
    return inquiry


@bp.post("/listings/<int:listing_id>/inquiries")
def create_inquiry(listing_id):
    if listings.get(listing_id) is None:
        abort(404)
    data = inquiry_from_form(request.form)
    try:
        added = inquiries.create(listing_id, data)
    except ValidationError as error:
        show_errors(error)
        return redirect(url_for("pages.listing_detail", listing_id=listing_id))
    flash(f"Запитването от {added.author_name} е записано.", "success")
    return redirect(url_for("pages.listing_detail", listing_id=listing_id))


@bp.route("/inquiries")
def inquiry_index():
    return render_template("inquiries.html", inquiries=inquiries.all())


@bp.route("/inquiries/<int:inquiry_id>/edit", methods=["GET", "POST"])
def edit_inquiry(inquiry_id):
    inquiry = load_inquiry(inquiry_id)
    if request.method == "POST":
        data = inquiry_from_form(request.form)
        try:
            inquiries.update(inquiry_id, data)
        except ValidationError as error:
            show_errors(error)
            form = namespace(data)
            form.id = inquiry_id
            form.listing = inquiry.listing
            inquiry = form
        else:
            flash("Запитването е обновено.", "success")
            return redirect(url_for("pages.inquiry_index"))
    return render_template("inquiry_form.html", inquiry=inquiry)


@bp.post("/inquiries/<int:inquiry_id>/delete")
def delete_inquiry(inquiry_id):
    inquiry = load_inquiry(inquiry_id)
    listing_id = inquiry.listing_id
    inquiries.delete(inquiry_id)
    flash("Запитването е изтрито.", "success")
    target = request.form.get("next") or url_for("pages.inquiry_index")
    if target == "listing":
        return redirect(url_for("pages.listing_detail", listing_id=listing_id))
    return redirect(url_for("pages.inquiry_index"))
