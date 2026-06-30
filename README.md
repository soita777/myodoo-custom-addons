# Chebu Odoo 18 Custom Addons

This repository tracks custom Odoo 18 addons for the local Chebu Odoo instance.

## Addons

- `my_arena`: a private notebook app for Odoo users.

## Local Odoo Setup

The custom addons path should be included in `/etc/odoo/odoo.conf`:

```ini
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/mnt/c/Users/PeterSoita/Desktop/chebu-odoo18-enterprise/custom_addons
```

After adding or updating modules, restart Odoo and update/install the target module.
