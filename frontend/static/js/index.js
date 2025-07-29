
  function toggleMenu() {
    document.querySelector(".menu").classList.toggle("show");
  }

  // function toggleIDCard() {
  //   const status = document.getElementById("status").value;
  //   const idCard = document.getElementById("idCardField");
  //   if (status === "member") {
  //     idCard.classList.remove("hidden");
  //   } else {
  //     idCard.classList.add("hidden");
  //   }
  // }

document.addEventListener("DOMContentLoaded", function () {
  const tombolQRIS = document.getElementById("tombolQRIS");
  const qrisContainer = document.getElementById("qrisContainer");

  if (tombolQRIS && qrisContainer) {
    tombolQRIS.addEventListener("click", function () {
      qrisContainer.style.display = qrisContainer.style.display === "none" ? "block" : "none";
    });
  }
});
document.addEventListener("DOMContentLoaded", function () {
  const statusSelect = document.getElementById("status");
  const nominalInfo = document.getElementById("nominalInfo");

  statusSelect.addEventListener("change", function () {
    const selected = statusSelect.value;
    if (selected === "member") {
      nominalInfo.style.display = "block";
      nominalInfo.textContent = "Biaya untuk Member: Rp20.000 / Tiket";
    } else if (selected === "non member") {
      nominalInfo.style.display = "block";
      nominalInfo.textContent = "Biaya untuk Non Member: Rp25.000 / Tiket";
    } else {
      nominalInfo.style.display = "none";
    }
  });
});document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('tiketForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const form = e.target;
    const formData = new FormData(form);

    document.getElementById('popupLoading').style.display = 'flex';

    try {
      const response = await fetch('/submit', {
        method: 'POST',
        body: formData
      });
      if (!response.ok) throw new Error('Gagal submit form');

      const result = await response.json();
      document.getElementById('popupLoading').style.display = 'none';

      const downloadBtn = document.getElementById('downloadTiketBtn');
      downloadBtn.href = result.tiket_url;
      downloadBtn.download = result.tiket_url.split('/').pop();
      downloadBtn.addEventListener('click', async function (e) {
        e.preventDefault();
        const url = this.href;
        const fileName = this.download || url.split('/').pop();
        const res = await fetch(url);
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = fileName;
        a.click();
        URL.revokeObjectURL(a.href);
      });

      document.getElementById('popupOverlay').style.display = 'flex';
      successAnim.goToAndPlay(0, true); // restart animasi setiap submit

      form.reset();
    } catch (err) {
      document.getElementById('popupLoading').style.display = 'none';
      alert('Terjadi kesalahan: ' + err.message);
    }
  });

  const successAnim = lottie.loadAnimation({
    container: document.getElementById('lottieSuccess'),
    renderer: 'svg',
    loop: false,
    autoplay: false,
    path: '/static/img/success.json'
  });
document.getElementById('closePopup').addEventListener('click', () => {
  document.getElementById('popupOverlay').style.display = 'none';
  window.location.href = '/';
});

});

// window.addEventListener("DOMContentLoaded", () => {
//   const popupOverlay = document.getElementById("popupOverlay");
//   const popupSuccess = document.getElementById("popupSuccess");

//   // Tambahkan kelas awal fade-in
//   popupSuccess.classList.add("fade-in");
  
//   // Isi kontennya terlebih dahulu
//   popupSuccess.innerHTML = `
//     <video autoplay muted loop playsinline style="width: 250px; height: auto; margin: 0 auto 15px; display: block; border-radius: 12px;">
//       <source src="/static/img/maintenance.mp4" type="video/mp4">
//       Your browser does not support the video tag.
//     </video>
//     <h2 style="margin-bottom: 10px; color: #d32f2f;">Coming Soon</h2>
//     <p style="color: #444;">Ticket purchase is currently under development.</p>
//     <a href="/" class="submit" style="display: inline-block; margin-top: 20px; padding: 12px 25px;
//       background-color: #d32f2f; color: white; border-radius: 8px; text-decoration: none;
//       font-weight: bold; transition: background 0.3s;">
//       Back to Home
//     </a>
//   `;

//   popupOverlay.style.display = "flex";

//   // Tambahkan efek show setelah delay sedikit
//   setTimeout(() => {
//     popupSuccess.classList.add("show");
//   }, 100); // 100ms delay agar transisi terasa alami
// });


   

  async function showModal(el) {
  const title = el.dataset.title;
  const image = el.dataset.image;
  const date = el.dataset.date;
  const slug = el.dataset.slug;

  document.getElementById('modalTitle').innerText = title;
  document.getElementById('modalDate').innerText = date;
  document.getElementById('modalImage').src = image;

  // Tampilkan loading sementara
  document.getElementById('modalContent').innerHTML = "<em>Loading...</em>";
  document.getElementById('newsModal').style.display = 'flex';

  try {
    const res = await fetch(`https://backend.liverpoolfc.com/lfc-rest-api/id/news/${slug}`, {
      headers: {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
      }
    });
    const data = await res.json();

    // Cari block dengan type = formattedText
    const block = data.blocks.find(b => b.type === "formattedText");
    const html = block ? block.formattedText : "<em>Konten tidak tersedia.</em>";

    // Masukkan konten ke modal
    document.getElementById('modalContent').innerHTML = html;

  } catch (err) {
    document.getElementById('modalContent').innerHTML = "<em>Gagal memuat konten.</em>";
    console.error("❌ Error loading detail berita:", err);
  }
}

function closeModal() {
  document.getElementById('newsModal').style.display = 'none';
}