from fabric import task
from pathlib import Path

SERVER_USER = "yyy"
SITENAME = "149.248.0.76"
REPO_URL = "https://github.com/PotatoBoy-MMY/mywebsite.git"
BRANCH = "master"


def render_template(template_name, **context):
    template_path = Path("deploy_tools") / template_name
    text = template_path.read_text()
    for key, value in context.items():
        text = text.replace(key, value)
    return text


@task
def deploy(c):
    site_folder = f"/home/{SERVER_USER}/sites/{SITENAME}"
    source_folder = f"{site_folder}/source"
    venv_folder = f"{site_folder}/virtualenv"
    database_folder = f"{site_folder}/database"
    static_folder = f"{site_folder}/static"
    env_file = f"{site_folder}/environment"

    print("== 1. Create directory structure ==")
    c.run(f"mkdir -p {database_folder}")
    c.run(f"mkdir -p {static_folder}")
    c.run(f"mkdir -p {venv_folder}")
    c.run(f"mkdir -p {source_folder}")

    print("== 2. Get latest source code ==")
    c.run(
        f"""
        if [ -d {source_folder}/.git ]; then
            cd {source_folder} && git fetch
        else
            git clone {REPO_URL} {source_folder}
        fi
        """
    )
    c.run(f"cd {source_folder} && git reset --hard origin/{BRANCH}")

    print("== 3. Create secret key if needed ==")
    c.run(
        f"""
        if [ ! -f {site_folder}/secret_key ]; then
            python3 -c "import secrets; print(secrets.token_hex(50))" > {site_folder}/secret_key
        fi
        """
    )
    secret_key = c.run(f"cat {site_folder}/secret_key", hide=True).stdout.strip()

    print("== 4. Write environment file ==")
    c.run(
        f"""
        cat > {env_file} <<EOF
ALLOWED_HOSTS={SITENAME}
DEBUG=False
DJANGO_SECRET_KEY={secret_key}
EOF
        """
    )

    print("== 5. Create or update virtualenv ==")
    c.run(f"python3 -m venv {venv_folder}")
    c.run(f"{venv_folder}/bin/pip install --upgrade pip")
    c.run(f"{venv_folder}/bin/pip install -r {source_folder}/requirements.txt")

    print("== 6. Run migrations ==")
    c.run(f"cd {source_folder} && {venv_folder}/bin/python manage.py migrate --noinput")

    print("== 7. Collect static files ==")
    c.run(f"cd {source_folder} && {venv_folder}/bin/python manage.py collectstatic --noinput")

    print("== 8. Upload nginx config ==")
    nginx_conf = render_template(
        "nginx.template.conf",
        SITENAME=SITENAME,
        USER=SERVER_USER,
    )
    Path("nginx.generated.conf").write_text(nginx_conf)
    c.put("nginx.generated.conf", "/tmp/nginx.generated.conf")
    c.sudo(f"mv /tmp/nginx.generated.conf /etc/nginx/sites-available/{SITENAME}")
    c.sudo(f"ln -sfn /etc/nginx/sites-available/{SITENAME} /etc/nginx/sites-enabled/{SITENAME}")
    c.sudo("rm -f /etc/nginx/sites-enabled/default")
    c.sudo("nginx -t")

    print("== 9. Upload systemd service ==")
    systemd_conf = render_template(
        "gunicorn-systemd.template.service",
        SITENAME=SITENAME,
        USER=SERVER_USER,
    )
    Path("gunicorn.generated.service").write_text(systemd_conf)
    c.put("gunicorn.generated.service", "/tmp/gunicorn.service")
    c.sudo("mv /tmp/gunicorn.service /etc/systemd/system/gunicorn.service")

    print("== 10. Fix permissions ==")
    c.sudo(f"chmod o+x /home/{SERVER_USER}")

    print("== 11. Restart services ==")
    c.sudo("systemctl daemon-reload")
    c.sudo("systemctl reload nginx")
    c.sudo("systemctl enable gunicorn")
    c.sudo("systemctl restart gunicorn")

    print("== Deploy finished ==")
