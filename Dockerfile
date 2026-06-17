ARG BASE_IMAGE=frappe/erpnext:v16.0.0
FROM ${BASE_IMAGE}

USER frappe
WORKDIR /home/frappe/frappe-bench

COPY --chown=frappe:frappe apps/erpnext_3pl apps/erpnext_3pl

RUN ./env/bin/pip install --no-cache-dir -e apps/erpnext_3pl
RUN mkdir -p sites/assets && ln -sfn /home/frappe/frappe-bench/apps/erpnext_3pl/erpnext_3pl/public sites/assets/erpnext_3pl
