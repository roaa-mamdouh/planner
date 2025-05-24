from __future__ import unicode_literals
import frappe
from frappe.utils.telemetry import capture

no_cache = 1


def get_context(context):
	csrf_token = frappe.sessions.get_csrf_token()
	frappe.db.commit()
	if frappe.session.user != "Guest":
		capture("active_site", "planner")
	context.csrf_token = csrf_token