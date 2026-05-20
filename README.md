# ERPNext 3PL Platform

Docker Swarm stack for a warehouse-first ERPNext v15 instance.

## Deploy

```bash
./deploy.sh
```

Default access:

- Public URL: `http://erptest.exemstsc.world`
- Local URL: `http://SERVER_IP:8080`
- User: `Administrator`
- Password: see `ADMIN_PASSWORD` in local `.env`

The `.env` file is intentionally not committed.

## Operational Notes

- Stack name: `erpnext3pl`
- ERPNext site: `erpnext-3pl.local`
- Public port: `8080`
- Nginx vhost: `/etc/nginx/sites-available/erptest.exemstsc.world`
- Data lives in Docker volumes created by the stack.
