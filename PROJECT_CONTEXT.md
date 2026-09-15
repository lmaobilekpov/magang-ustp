# Project Context

## Project
Internal office document/package tracking system for receptionist and employees.
Repository: `lmaobilekpov/magang-ustp`

## Stack
- Django / Python
- SQLite for the current application database
- Django Admin for receptionist-side management
- Employee tracking portal at `/`
- GitHub `main` is the current source of truth

## Working preferences
- Discuss requirements before adding business features.
- Prefer one logical code change at a time.
- Keep the MVP simple and avoid overengineering.
- Keep automated tests passing after changes.

## Master data
### Karyawan
The source Excel contains employee records imported into the local database.
Fields currently include employee code, full name, position, and date of birth.

Requirements:
- Resigned employees should automatically become inactive based on a date/mechanism; exact implementation is still open.
- All receptionists have the same access level.
- Store who last updated a record if needed, but a full audit log is not required.

### Supplier
The source Excel contains supplier records imported into the local database.
Source columns include supplier code and supplier name; address is not needed for transactions.

Requirements:
- Store/use both supplier code and supplier name.
- Supplier code is the stable identifier when names are duplicated.
- Supplier data comes from an external/main database/API.
- The application must keep a local copy so it can continue operating when the main database/API is down.
- New supplier data should originate from the main API/database.
- With 1,000+ suppliers, a searchable supplier selection UI is preferable to a long normal dropdown.

## Dokumen Masuk
Categories: `Surat Resmi`, `Paket Pribadi`.
Statuses: `Di Resepsionis`, `Sudah Diambil`.

Sender:
- PT/Instansi -> select from supplier master.
- Non-PT/Perseorangan -> manually enter sender name.

Recipient:
- Must match an employee registered in Data Karyawan.
- Normally one specific employee.
- If needed, use the person who normally handles incoming packages for that division.
- Another person may physically pick up a package if they know the owner's date of birth; the system does not need a separate representative entity.

Pickup:
- Pickup time is automatically recorded when status changes to `Sudah Diambil`.
- Existing pickup time is preserved if status remains `Sudah Diambil`.
- Packages unpicked for more than 3 days should be identifiable by the receptionist.
- Receptionist is normally always available; security handover is not part of the normal process.

## Dokumen Keluar
Statuses:
- `Menunggu Kurir`
- `Sudah Diserahkan ke JNE`
- `Paket Kembali`

Sender:
- Must match an employee registered in Data Karyawan.

Internal number:
- Auto-generated as `OUT-YYYYMMDD-001`.
- Unique per transaction.
- Sequence resets to `001` on a new date.

JNE:
- Store a clickable JNE tracking URL.
- No JNE API/scraping integration for the MVP.
- Usually around 10-15 documents are handed to JNE in one pickup, generally once per day.
- No management report is required; the system is mainly for receptionist use.

Returned documents:
- If a shipment handed to JNE returns to the office, mark the old transaction `Paket Kembali`.
- If it will be sent again, create a new outgoing transaction/process instead of overwriting the old transaction.

## Portal
- Employee tracking portal currently uses date of birth verification.
- If a date of birth matches more than one employee, verification is rejected and the user is asked to contact the receptionist.

## Photos and scope
- `foto_barang` and `foto_dokumen` remain optional unless office SOP requires them.
- No Inventaris IT category.
- No notification system unless a real need is confirmed.
- No phone number unless required by the actual process.

## Testing status
`dokumen/tests.py` contains automated tests covering incoming validation, pickup timestamps, outgoing validation, JNE URL validation, internal number generation/sequence, employee-name validation, and portal date-of-birth verification.

## Open decisions
- Exact inactive mechanism/date for resigned employees.
- Exact API contract and synchronization schedule for supplier data.
- Exact office meaning of "penerimaan baru"; current interpretation is old outgoing transaction becomes `Paket Kembali`, then a new outgoing transaction is created for re-shipment.
- Whether incoming receipt time needs hour/minute precision.
- Whether first receiver should be recorded; allowed with Lily as default, but not core yet.
