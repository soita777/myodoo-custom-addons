# My Odoo Custom Addons

Custom Odoo 18 addons for a locally hosted Odoo instance.

This repository is meant to track custom module code only. It should not contain
database dumps, Odoo logs, server passwords, local config files, or generated
Python cache files.

## Available Modules

### `my_arena`

`My Arena` is a private notebook app for Odoo users.

Main features:

- Personal notes for each internal Odoo user.
- Notes are owned by the logged-in user.
- Users can only access their own notes and tags.
- Kanban, list, form, and search views.
- Support for tags, pinned notes, archived notes, colors, and priority.
- Odoo app icon included.

## Repository Structure

```text
custom_addons/
├── my_arena/
│   ├── models/
│   ├── security/
│   ├── static/description/
│   ├── views/
│   ├── __init__.py
│   └── __manifest__.py
├── .gitignore
└── README.md
```

## Odoo Configuration

The custom addons directory must be included in `/etc/odoo/odoo.conf`.

Example:

```ini
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/mnt/c/Users/PeterSoita/Desktop/chebu-odoo18-enterprise/custom_addons
```

After changing `addons_path`, restart Odoo:

```bash
sudo systemctl restart odoo
```

## Install A Module

Install `my_arena` into the local database:

```bash
sudo -u odoo /usr/bin/odoo \
  -c /etc/odoo/odoo.conf \
  -d odoo18_db \
  -i my_arena \
  --stop-after-init \
  --no-http
```

Then restart Odoo:

```bash
sudo systemctl restart odoo
```

## Update A Module

After code changes, update the module:

```bash
sudo -u odoo /usr/bin/odoo \
  -c /etc/odoo/odoo.conf \
  -d odoo18_db \
  -u my_arena \
  --stop-after-init \
  --no-http
```

Then restart Odoo:

```bash
sudo systemctl restart odoo
```

## Git Workflow

Check current changes:

```bash
git status
```

Stage changes:

```bash
git add .
```

Commit changes:

```bash
git commit -m "Describe the change"
```

Push changes:

```bash
git push
```

Local commit identity used for this repository:

```text
soita888 <peterspectre99@gmail.com>
```

For GitHub contribution attribution, the email address above must be added and
verified in the GitHub account settings.

## Notes

- Keep custom modules in this repository.
- Keep Odoo system configuration in `/etc/odoo/odoo.conf`, not in Git.
- Keep database backups outside this repository.
- Do not commit tokens, passwords, logs, or generated cache files.
