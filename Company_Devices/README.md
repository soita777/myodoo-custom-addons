# myodoo-custom-addons
This is for my test.


Custom Addons

This repository tracks custom Odoo 18 addons for the local Chebu Odoo instance.
Custom Odoo 18 addons for a locally hosted Odoo instance.

## Addons
This repository is meant to track custom module code only. It should not contain
database dumps, Odoo logs, server passwords, local config files, or generated
Python cache files.

## Available Modules

- `my_arena`: a private notebook app for Odoo users.
- `company_devices`: a module to record and track company-owned devices.

### `my_arena`

## Local Odoo Setup
`My Arena` is a private notebook app for Odoo users.

The custom addons path should be included in `/etc/odoo/odoo.conf`:
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
├── Company resources/
│   └── company_devices/
│       ├── models/
│       ├── security/
│       ├── views/
│       ├── __init__.py
│       └── __manifest__.py
├── .gitignore
└── README.md
```

## Odoo Configuration

The custom addons directory must be included in `/etc/odoo/odoo.conf`.

Example:

```ini
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/mnt/c/Users/PeterSoita/Desktop/chebu-odoo18-enterprise/custom_addons
```

After adding or updating modules, restart Odoo and update/install the target module.
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

## Company Devices (module)

Module to record and track company-owned devices and assign them to employees or users. Includes fields for remote management and tracking method.

Quick install
-------------
- Copy the `company_devices` folder into your Odoo `addons` path (for example, `custom_addons/Company resources/company_devices`).
- Update the Apps list and install the `Company Devices` module.

GitHub
------
This repository contains a single Odoo module `company_devices`. To publish to GitHub, initialize a git repo, add a remote, and push. Example commands:

```powershell
cd "c:\Users\PeterSoita\Desktop\chebu-odoo18-enterprise\custom_addons\Company resources\company_devices"
git init
git add .
git commit -m "Initial commit: company_devices module"
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

Notes
-----
- The module restricts model access to admin by default. If you want HR or managers to have access, ask and I will add groups and record rules.
- If you want me to push to GitHub, provide the repository URL or let me know if you want instructions for creating the repository.

