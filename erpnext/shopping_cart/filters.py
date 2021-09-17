# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe


class ProductFiltersBuilder:
	def __init__(self, item_group=None):
		if not item_group or item_group == "Products Settings":
			self.doc = frappe.get_doc("Products Settings")
		else:
			self.doc = frappe.get_doc("Item Group", item_group)

		self.item_group = item_group

	def get_field_filters(self):
		filter_fields = [row.fieldname for row in self.doc.filter_fields]

		meta = frappe.get_meta('Item')
		fields = [df for df in meta.fields if df.fieldname in filter_fields]

		filter_data = []
		for df in fields:
			filters, or_filters = {}, []
			if df.fieldtype == "Link":
				if self.item_group:
					or_filters.extend([
						["item_group", "=", self.item_group],
						["Website Item Group", "item_group", "=", self.item_group]
					])

				values = frappe.get_all("Item", fields=[df.fieldname], filters=filters, or_filters=or_filters, distinct="True", pluck=df.fieldname)
			else:
				doctype = df.get_link_doctype()

				# apply enable/disable/show_in_website filter
				meta = frappe.get_meta(doctype)

				if meta.has_field('enabled'):
					filters['enabled'] = 1
				if meta.has_field('disabled'):
					filters['disabled'] = 0
				if meta.has_field('show_in_website'):
					filters['show_in_website'] = 1

				values = [d.name for d in frappe.get_all(doctype, filters)]

			# Remove None
			if None in values:
				values.remove(None)

			if values:
				filter_data.append([df, values])

		return filter_data

	def get_attribute_filters(self):
		attributes = [row.attribute for row in self.doc.filter_attributes]

		if not attributes:
			return []

		result = frappe.db.sql(
			"""
			select
				distinct attribute, attribute_value
			from
				`tabItem Variant Attribute`
			where
				attribute in %(attributes)s
				and attribute_value is not null
		""",
			{"attributes": attributes},
			as_dict=1,
		)

		attribute_value_map = {}
		for d in result:
			attribute_value_map.setdefault(d.attribute, []).append(d.attribute_value)

		out = []
		for name, values in attribute_value_map.items():
			out.append(frappe._dict(name=name, item_attribute_values=values))
		return out
