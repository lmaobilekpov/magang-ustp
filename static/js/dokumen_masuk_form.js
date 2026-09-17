document.addEventListener('DOMContentLoaded', function () {
    const jenisPengirim = document.getElementById('id_jenis_pengirim');
    const ptPengirim = document.getElementById('id_pt_pengirim');
    const pengirim = document.getElementById('id_pengirim');

    if (!jenisPengirim) return;

    const getRow = (field) => field ? field.closest('.form-row') : null;
    const ptRow = getRow(ptPengirim);
    const pengirimRow = getRow(pengirim);

    function toggleSenderFields() {
        const isPT = jenisPengirim.value === 'PT';

        if (ptRow) ptRow.style.display = isPT ? '' : 'none';
        if (pengirimRow) pengirimRow.style.display = isPT ? 'none' : '';

        if (pengirim) {
            if (isPT) {
                pengirim.removeAttribute('required');
            } else {
                pengirim.setAttribute('required', 'required');
            }
        }
    }

    jenisPengirim.addEventListener('change', toggleSenderFields);
    toggleSenderFields();
});
