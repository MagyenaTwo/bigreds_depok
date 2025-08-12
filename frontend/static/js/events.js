async function showEventDetails(card) {
    const title = card.getAttribute('data-title');
    if (!title) return;

    try {
      const response = await fetch(`/event-details?title=${encodeURIComponent(title)}`);
      if (!response.ok) throw new Error('Gagal memuat detail event');
      const data = await response.json();

      document.getElementById('modal-title').textContent = data.title;
      document.getElementById('modal-description').textContent = data.deskripsi || 'Tidak ada deskripsi.';

      const gallery = document.getElementById('modal-gallery');
      gallery.innerHTML = '';
      data.images.forEach(img => {
        const imageElem = document.createElement('img');
        imageElem.src = img.image_url;
        imageElem.alt = data.title;
        gallery.appendChild(imageElem);
      });

      document.getElementById('eventDetailModal').style.display = 'block';
    } catch (error) {
      alert(error.message);
    }
  }

  function closeModal() {
    document.getElementById('eventDetailModal').style.display = 'none';
  }

  // Tutup modal saat klik di luar modal-content
  window.onclick = function(event) {
    const modal = document.getElementById('eventDetailModal');
    if (event.target === modal) {
      closeModal();
    }
  }