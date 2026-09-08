# POS Register Pool

This addon makes every selected POS configuration an exclusive register.

## Daily workflow

1. Each salesperson signs in using their own Odoo user account.
2. They choose an available POS register from the POS dashboard.
3. The first person to open it owns that register until its POS session is closed.
4. Anyone else who selects the occupied register receives a message naming the
   salesperson who has it and must choose another register.

Create seven POS configurations (for example, `Register 1` through `Register
7`) for a seven-register pool. Leave **Exclusive Register** enabled on each
configuration.

The occupant name and status are shown in the POS configuration list and on the
configuration form.
