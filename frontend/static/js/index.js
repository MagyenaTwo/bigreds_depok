
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