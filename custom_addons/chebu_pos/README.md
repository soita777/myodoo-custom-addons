# Chebu POS

Chebu POS adds a lightweight register lifecycle and a cleaner POS login flow to Odoo 18 Point of Sale without replacing the standard Odoo POS engine.

## What it does

- Adds four lightweight POS registers: Cashier 01, Cashier 02, Sales 01, and Sales 02.
- Tracks register availability, user assignment, session linkage, and lock state.
- Prevents two users from occupying the same register at the same time.
- Displays a modern register-selection experience before the standard POS login proceeds.
- Keeps Odoo's native POS products, customers, payments, sessions, stock, and accounting flow intact.

## Installation

1. Place the module in your custom addons directory.
2. Update the Odoo addons path if needed.
3. Install the module in the target database, then refresh the POS app.

## Register management

The register model stores:

- name
- code
- register type (Cashier or Sales)
- active flag
- status (Available, Active, Locked)
- current user
- active POS session
- associated POS configuration, where assigned

## Occupancy rules

- A register can only have one assigned user at a time.
- Backend validation blocks any second user from claiming an already active register.
- A locked register cannot be opened until it is reset by an administrator.
- Release logic clears the user and session when the session ends cleanly.

## POS workflow

Users select an available register at the POS login screen and then continue with the built-in Odoo POS login flow. The register is claimed server-side before the POS app continues.

## Security notes

The backend is the source of truth for register occupancy. Frontend validation is only a UX aid; it does not replace the server-side rules.

## Upgrade

When changing the register model or logic, update the module version and install the module again in the target database.

## Known limitations

- This module is designed as a register-management layer and does not replace standard Odoo POS features.
- The register list is intentionally lightweight; it is meant to be extended with Chebu-specific POS enhancements later.
