# ERPNext 3PL Platform

Docker Swarm stack for a warehouse-first ERPNext v15 instance.

## Deploy

```bash
sudo scripts/bootstrap_docker_swarm.sh SERVER_IP
cp .env.example .env
# edit .env secrets
./deploy.sh
./scripts/run_post_deploy.sh
```

Default access:

- Public URL: `https://erptest.exemstsc.world`
- Local URL: `http://SERVER_IP:8080`
- User: `Administrator`
- Password: see `ADMIN_PASSWORD` in local `.env`

The `.env` file is intentionally not committed.

On a first deploy, run `run_post_deploy.sh` after the stack creates the ERPNext site. It applies the warehouse-only configuration, creates demo users, and loads demo warehouse data.

## Demo Users

- Warehouse operator: `warehouse.demo@example.test` / `WarehouseDemo2026!`
- Warehouse manager: `warehouse.manager@example.test` / `WarehouseManager2026!`

## Warehouse Docs

- Roadmap: `docs/roadmap.md`
- Warehouse mode overview: `docs/warehouse-mode.md`
- Demo access: `docs/manuals/00-demo-access.md`
- Receiving: `docs/manuals/01-receiving.md`
- Putaway: `docs/manuals/02-putaway.md`
- Picking: `docs/manuals/03-picking.md`
- Packing and Dispatch: `docs/manuals/04-packing-dispatch.md`
- Open questions: `docs/manuals/05-open-questions.md`

## Operational Notes

- Stack name: `erpnext3pl`
- ERPNext site: `erpnext-3pl.local`
- Public port: `8080`
- Nginx vhost: `/etc/nginx/sites-available/erptest.exemstsc.world`
- TLS certificate: `/etc/letsencrypt/live/erptest.exemstsc.world/fullchain.pem`
- Data lives in Docker volumes created by the stack.
