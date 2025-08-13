function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('active');
 
}

async function kirimTiket(tiketId) {
    const btn = event.target;
    const originalText = btn.innerText;

    btn.innerHTML = "Mengirim...";
    btn.style.opacity = "0.6";
    btn.disabled = true;

    try {
        const res = await fetch(`/kirim-tiket/${tiketId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });

        const data = await res.json();

        if (data.success) {
            // Tidak ubah tampilan di sini
            location.reload(); // Reload biar HTML Jinja render ulang status ✅
        } else {
            throw new Error(data.message || "Gagal mengirim");
        }
    } catch (err) {
        alert("❌ Gagal mengirim tiket. Coba lagi.");
        btn.innerText = originalText;
        btn.style.opacity = "1";
        btn.disabled = false;
    }
}


let selectedDeleteId = null;

function showDeleteConfirm(id) {
  selectedDeleteId = id;
  document.getElementById('deleteModal').style.display = 'flex';
}

function closeDeleteModal() {
  selectedDeleteId = null;
  document.getElementById('deleteModal').style.display = 'none';
}

document.getElementById('confirmDeleteBtn').addEventListener('click', function() {
  if (selectedDeleteId) {
    // Buat form POST secara dinamis
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = `/cms/delete/${selectedDeleteId}`;
    document.body.appendChild(form);
    form.submit();
  }
});