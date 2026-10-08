# Temperature Guru

Temperature Guru tracks cold-chain devices and temperature readings by company
branch in Odoo 18.

## Setup

- Install `chebu_inventory_movement` first; Temperature Guru uses its branch
  records.
- Add the company's remaining branch records before registering monitors for
  those locations.
- Add each monitor with its branch, physical location, serial number, and
  acceptable temperature range.
- The default range is 2-8 C and the device is considered offline after four
  hours without a reading. Adjust both values per device as required.

## Readings

Temperature readings can be logged from a device card or the Readings menu.
The dashboard reports out-of-range, stale, and missing readings and compares
24-hour averages by branch. The current module records readings entered in
Odoo; no external sensor or IoT feed is configured yet.

Temperature Guru users can view devices and create readings. Temperature Guru
managers can also create and configure devices. Access is limited to the user's
allowed companies.