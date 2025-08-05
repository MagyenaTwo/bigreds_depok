
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
      hargaPerTiket = 30000;
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

window.addEventListener("DOMContentLoaded", () => {
  const popupOverlay = document.getElementById("popupOverlay");
  const popupSuccess = document.getElementById("popupSuccess");

  // Tambahkan kelas awal fade-in
  popupSuccess.classList.add("fade-in");
  
  // Isi kontennya terlebih dahulu
  popupSuccess.innerHTML = `
    <video autoplay muted loop playsinline style="width: 250px; height: auto; margin: 0 auto 15px; display: block; border-radius: 12px;">
      <source src="/static/img/maintenance.mp4" type="video/mp4">
      Your browser does not support the video tag.
    </video>
    <h2 style="margin-bottom: 10px; color: #d32f2f;">Coming Soon</h2>
    <p style="color: #444;">Ticket purchase is currently under development.</p>
    <a href="/" class="submit" style="display: inline-block; margin-top: 20px; padding: 12px 25px;
      background-color: #d32f2f; color: white; border-radius: 8px; text-decoration: none;
      font-weight: bold; transition: background 0.3s;">
      Back to Home
    </a>
  `;

  popupOverlay.style.display = "flex";

  // Tambahkan efek show setelah delay sedikit
  setTimeout(() => {
    popupSuccess.classList.add("show");
  }, 100); // 100ms delay agar transisi terasa alami
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

