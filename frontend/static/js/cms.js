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
