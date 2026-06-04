# ERPNext 3PL Platform

Docker Swarm stack for a warehouse-first ERPNext v16 instance.

## Deploy

Fresh server:

```bash
sudo scripts/bootstrap_docker_swarm.sh SERVER_IP
cp .env.example .env
# edit .env secrets
sudo ./scripts/deploy_first_instance.sh erpnext.SERVER_IP.sslip.io
```

Existing instance update:

```bash
./deploy.sh https://erpnext.77.237.244.169.sslip.io
./scripts/validate_instance.sh https://erpnext.77.237.244.169.sslip.io
```

Default access:

- Public URL: `https://erpnext.77.237.244.169.sslip.io`
- Local URL: `http://SERVER_IP:8080`
- User: `Administrator`
- Password: see `ADMIN_PASSWORD` in local `.env`

The `.env` file is intentionally not committed.

On a first deploy, use `deploy_first_instance.sh`. It starts the stack in a safe bootstrap phase, waits for site creation, starts runtime services, applies warehouse-only configuration, creates demo users, loads demo warehouse data, and validates the result.

On an existing instance, use `deploy.sh` or `scripts/deploy_existing_instance.sh`. The script creates a site backup before changing the ERPNext image, deploys the stack, runs `bench migrate`, reapplies project setup, and validates the public URL.

For a quick HTTPS endpoint without managing DNS first, use an `sslip.io` hostname such as `erpnext.77.237.244.169.sslip.io`. For a real domain, point its A record to the server first, then pass that domain to `configure_https.sh`.

## Demo Users

- Warehouse operator: `warehouse.demo@example.test` / `WarehouseDemo2026!`
- Warehouse manager: `warehouse.manager@example.test` / `WarehouseManager2026!`

## Warehouse Docs

- Deployment: `docs/deployment.md`
- Repository policy: `docs/repository-policy.md`
- Roadmap: `docs/roadmap.md`
- Warehouse mode overview: `docs/warehouse-mode.md`
- Demo access: `docs/manuals/00-demo-access.md`
- Client test guide: `docs/client-test-guide.md`
- Receiving: `docs/manuals/01-receiving.md`
- Putaway: `docs/manuals/02-putaway.md`
- Picking: `docs/manuals/03-picking.md`
- Packing and Dispatch: `docs/manuals/04-packing-dispatch.md`
- Open questions: `docs/manuals/05-open-questions.md`

## Operational Notes

- Stack name: `erpnext3pl`
- ERPNext site: `erpnext-3pl.local`
- Public port: `8080`
- Nginx vhost: `/etc/nginx/sites-available/DOMAIN`
- TLS certificate: `/etc/letsencrypt/live/DOMAIN/fullchain.pem`
- Data lives in Docker volumes created by the stack.
