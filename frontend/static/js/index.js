
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
      nominalInfo.textContent = "Biaya untuk Member: Rp20.000";
    } else if (selected === "non_member") {
      nominalInfo.style.display = "block";
      nominalInfo.textContent = "Biaya untuk Non Member: Rp25.000";
    } else {
      nominalInfo.style.display = "none";
    }
  });
});

document.getElementById("tiketForm").addEventListener("submit", async function (e) {
  e.preventDefault();

  const form = e.target;
  const formData = new FormData(form);

  // Tampilkan loading popup
  const loadingPopup = document.getElementById("popupLoading");
  loadingPopup.style.display = "flex";

  try {
    const response = await fetch("/submit", {
      method: "POST",
      body: formData
    });

    loadingPopup.style.display = "none"; // Sembunyikan loading popup

    if (response.redirected || response.ok) {
      // Tampilkan popup sukses
      const popupOverlay = document.getElementById("popupOverlay");
      popupOverlay.style.display = "flex";

      // Cegah animasi double-load
      if (!popupOverlay.dataset.loaded) {
        lottie.loadAnimation({
          container: document.getElementById("lottieSuccess"),
          renderer: "svg",
          loop: false,
          autoplay: true,
          path: "/static/img/success.json"
        });
        popupOverlay.dataset.loaded = "true";
      }
    } else {
      alert("Terjadi kesalahan. Silakan coba lagi.");
    }
  } catch (error) {
    loadingPopup.style.display = "none";
    alert("Terjadi kesalahan jaringan.");
  }
});



document.getElementById("downloadTiketBtn").addEventListener("click", function () {
  setTimeout(() => {
    window.location.href = "/";
  }, 3000); 
});

function validasiJumlahTiket(input) {
  const val = input.value;
  // Hapus karakter non-angka
  input.value = val.replace(/[^0-9]/g, '');

  // Jika lebih dari 4, batasi ke 4
  if (parseInt(input.value) > 4) {
    input.value = 4;
  }

  // Jika kurang dari 1 tapi tidak kosong, set ke 1
  if (input.value !== '' && parseInt(input.value) < 1) {
    input.value = 1;
  }
}
//JS MAINTENANCE TIKET
  window.addEventListener("DOMContentLoaded", () => {
    
    document.getElementById("popupOverlay").style.display = "flex";
    document.getElementById("popupSuccess").innerHTML = `
      <div id="lottieSuccess" style="width: 180px; height: 180px; margin: 0 auto 15px;"></div>
      <h2 style="margin-bottom: 10px; color: #d32f2f;">Coming Soon</h2>
      <p style="color: #444;">Ticket purchase is currently under development.</p>
      <a href="/" class="submit" style="display: inline-block; margin-top: 20px; padding: 12px 25px;
        background-color: #d32f2f; color: white; border-radius: 8px; text-decoration: none;
        font-weight: bold; transition: background 0.3s;">
        Back to Home
      </a>
    `;

    // Tambah animasi Lottie sukses
    lottie.loadAnimation({
      container: document.getElementById('lottieSuccess'),
      renderer: 'svg',
      loop: false,
      autoplay: true,
      path: 'https://assets6.lottiefiles.com/packages/lf20_jbrw3hcz.json' // animasi coming soon
    });
  });

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