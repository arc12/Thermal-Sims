"""Routes for base Flask app"""
from flask import Blueprint, render_template

base_app = Blueprint("base_app", __name__)
top_menus = [
    {"path": "/ambient", "title": "Ambient"},
    {"path": "/cop_curves", "title": "COP Curves"},
    {"path": "/room_temp", "title": "Room Temp"},
    {"path": "/cycling", "title": "Cycling"},
    {"path": "/constant", "title": "Constant LWT"}
]


def get_top_menu_items(current_path: str = "/"):
    """Get html template for top menu items."""
    items = []

    for menu in top_menus:
        active = False

        if menu["path"] == current_path:
            active = True

        if menu["path"] != "/" and current_path.startswith(menu["path"]):
            active = True

        link_class_name = "nav-link px-2 " + (
            "link-secondary" if active else "link-dark"
        )

        items.append(
            f'<li><a href="{menu["path"]}" class="{link_class_name}">{menu["title"]}</a></li>'
        )

    return "\n".join(items)


@base_app.route("/")
def index():
    """Landing page."""
    return render_template("index.html", top_menu_items=get_top_menu_items("/"))
