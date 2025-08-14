
  function toggleMenu() {
    document.querySelector(".menu").classList.toggle("show");
  }
function toggleIDCard() {
  const status = document.getElementById("status").value;
  const idCardField = document.getElementById("idCardField");
  const idCardInput = document.getElementById("idCardInput");

  if (status === "member") {
    idCardField.style.display = "block";
    idCardInput.setAttribute("required", "required");
  } else {
    idCardField.style.display = "none";
    idCardInput.removeAttribute("required");
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const tombolQRIS = document.getElementById("tombolQRIS");
  const qrisContainer = document.getElementById("qrisContainer");

  if (tombolQRIS && qrisContainer) {
    tombolQRIS.addEventListener("click", function () {
      qrisContainer.style.display = qrisContainer.style.display === "none" ? "block" : "none";
    });
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("tiketForm");

  const statusSelect = form.querySelector('[name="status"]');
  const jumlahTiketInput = form.querySelector('[name="jumlah"]');
  const nominalInfo = document.getElementById("nominalInfo");
  const totalHargaInput = form.querySelector('[name="total_harga"]');

  function updateHarga() {
    const status = statusSelect.value;
    const jumlah = parseInt(jumlahTiketInput.value) || 0;

    let hargaPerTiket = 0;
    if (status === "member") {
      hargaPerTiket = 20000;
    } else if (status === "non member") {
      hargaPerTiket = 20000;
    }

    const total = hargaPerTiket * jumlah;
    if (status && jumlah > 0) {
      nominalInfo.style.display = "block";
      nominalInfo.textContent = `Total yang harus di Bayar: Rp ${total.toLocaleString("id-ID")}`;
    } else {
      nominalInfo.style.display = "none";
    }

    totalHargaInput.value = total;
  }

  statusSelect.addEventListener("change", updateHarga);
  jumlahTiketInput.addEventListener("input", updateHarga);
});

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('tiketForm');
  const popupLoading = document.getElementById('popupLoading');
  const popupOverlay = document.getElementById('popupOverlay');
  const lottieContainer = document.getElementById('lottieSuccess');
  const closeBtn = document.getElementById('closePopup');

  // 1. Pastikan semua elemen ada
  if (!form || !popupLoading || !popupOverlay || !lottieContainer || !closeBtn) {
    console.error("Elemen penting tidak ditemukan di DOM.");
    return;
  }

  // 2. Load Lottie animasi setelah DOM siap
  const successAnim = lottie.loadAnimation({
    container: lottieContainer,
    renderer: 'svg',
    loop: false,
    autoplay: false,
    path: '/static/img/success.json'
  });

  form.addEventListener('submit', async function (e) {
    e.preventDefault();
    const formData = new FormData(form);
    popupLoading.style.display = 'flex';

    try {
      const response = await fetch('/submit', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) throw new Error('Gagal submit form');

      // Opsional: Ambil result jika dibutuhkan
      const result = await response.json();

      // Matikan loading
      popupLoading.style.display = 'none';

      // Mainkan animasi jika sudah berhasil di-load
     if (successAnim && successAnim.goToAndPlay) {
  
  successAnim.goToAndPlay(0, true);

}


      // Tampilkan popup sukses
      popupOverlay.style.display = 'flex';

      // Reset form
      form.reset();

    } catch (err) {
      popupLoading.style.display = 'none';
      alert('Terjadi kesalahan: ' + err.message);
      console.error(err);
    }
  });

  closeBtn.addEventListener('click', () => {
    popupOverlay.style.display = 'none';
    window.location.href = '/';
  });
});

// TampilanQRIS
window.addEventListener("DOMContentLoaded", () => {
  const tombolQRIS = document.getElementById("tombolQRIS");
  const popupOverlay = document.getElementById("popupOverlay");
  const popupSuccess = document.getElementById("popupSuccess");
  const qrisSection = document.getElementById("qrisSection");
  const metodeSelect = document.getElementById("metode_pembayaran");
  const gopaySection = document.getElementById("gopaySection");
  const shopeeSection = document.getElementById("shopeeSection");
  const bankSection = document.getElementById("bankSection");

  // Tombol QRIS diklik
  tombolQRIS.addEventListener("click", () => {
    popupSuccess.classList.add("fade-in");

    popupSuccess.innerHTML = `
      <video autoplay muted loop playsinline style="width: 250px; height: auto; margin: 0 auto 15px; display: block; border-radius: 12px;">
        <source src="/static/img/maintenance.mp4" type="video/mp4">
        Your browser does not support the video tag.
      </video>
      <h2 style="margin-bottom: 10px; color: #d32f2f;">Coming Soon</h2>
      <p style="color: #444;">Payment QRIS under development.</p>
      <a href="/buy-ticket" class="submit" style="display: inline-block; margin-top: 20px; padding: 12px 25px;
        background-color: #d32f2f; color: white; border-radius: 8px; text-decoration: none;
        font-weight: bold; transition: background 0.3s;">
        Back
      </a>
    `;

    popupOverlay.style.display = "flex";

    setTimeout(() => {
      popupSuccess.classList.add("show");
    }, 100);
  });

  // Klik luar popup → tutup
  popupOverlay.addEventListener("click", (e) => {
    if (e.target === popupOverlay) {
      popupOverlay.style.display = "none";
      popupSuccess.classList.remove("show");
      popupSuccess.innerHTML = "";
    }
  });

  metodeSelect.addEventListener("change", () => {
  const selected = metodeSelect.value;

  qrisSection.style.display = selected === "qris" ? "block" : "none";
  gopaySection.style.display = selected === "gopay" ? "block" : "none";
  shopeeSection.style.display = selected === "shopeepay" ? "block" : "none";
  bankSection.style.display = selected === "bank_transfer" ? "block" : "none";

  });
});


function copyRekening() {
  const rekeningText = document.getElementById("rekeningText").textContent;

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(rekeningText)
      .then(() => {
        alert("✅ Nomor rekening berhasil disalin ke clipboard!");
      })
      .catch(err => {
        console.error("Gagal menyalin:", err);
        alert("Gagal menyalin nomor rekening.");
      });
  } else {
    // Fallback: gunakan textarea
    const tempInput = document.createElement("textarea");
    tempInput.value = rekeningText;
    document.body.appendChild(tempInput);
    tempInput.select();
    try {
      document.execCommand("copy");
      alert("✅ Nomor rekening berhasil disalin!");
    } catch (err) {
      alert("Gagal menyalin nomor rekening.");
    }
    document.body.removeChild(tempInput);
  }
}

  
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
    // GUNAKAN ROUTE PROXY BACKENDMU
    const res = await fetch(`/proxy/news/${slug}`);
    const data = await res.json();

    const block = data.blocks.find(b => b.type === "formattedText");
    const html = block ? block.formattedText : "<em>Konten tidak tersedia.</em>";

    document.getElementById('modalContent').innerHTML = html;

  } catch (err) {
    document.getElementById('modalContent').innerHTML = "<em>Gagal memuat konten.</em>";
    console.error("❌ Error loading detail berita:", err);
  }
}

function closeModal() {
  document.getElementById('newsModal').style.display = 'none';
}

const rawGallery = document.getElementById("gallery-data").dataset.gallery;
const galleryImages = JSON.parse(rawGallery);

const img1 = document.getElementById("bg1");
const img2 = document.getElementById("bg2");

let index = 0;
let currentImg = img1;
let nextImg = img2;

function changeBackground() {
  if (!galleryImages.length) return;

  const nextImage = galleryImages[index].image_url;
  const img = new Image();

  img.onload = () => {
    nextImg.src = nextImage;
    nextImg.classList.add("visible");
    currentImg.classList.remove("visible");
    [currentImg, nextImg] = [nextImg, currentImg];
    index = (index + 1) % galleryImages.length;
  };

  img.src = nextImage;
}

// Set gambar pertama saat load
window.addEventListener("DOMContentLoaded", () => {
  if (galleryImages.length > 0) {
    img1.src = galleryImages[0].image_url;
    img1.classList.add("visible");
  }

  setInterval(changeBackground, 7000);
});


  document.addEventListener("DOMContentLoaded", () => {
  const giftsContainer = document.querySelector(".falling-gifts");
  const giftEmojis = ["🎁", "🏆", "🎉", "⚽"];
  
  function createGift() {
    const gift = document.createElement("div");
    gift.classList.add("gift");
    gift.textContent = giftEmojis[Math.floor(Math.random() * giftEmojis.length)];
    gift.style.left = Math.random() * 100 + "vw";
    gift.style.animationDuration = (Math.random() * 3 + 3) + "s";
    giftsContainer.appendChild(gift);

    setTimeout(() => gift.remove(), 6000);
  }

  setInterval(createGift, 500);
});

// Tampilkan modal saat klik tombol
document.getElementById('maintenanceBtn').addEventListener('click', function(e){
  e.preventDefault();
  document.getElementById('maintenanceModal').style.display = 'block';
});

// Tutup modal saat klik tombol close
document.getElementById('closeModal').addEventListener('click', function(){
  document.getElementById('maintenanceModal').style.display = 'none';
});

// Tutup modal saat klik di luar modal
window.addEventListener('click', function(e){
  const modal = document.getElementById('maintenanceModal');
  if(e.target === modal) modal.style.display = 'none';
});
