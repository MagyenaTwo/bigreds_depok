let currentPlayerName = "";
let currentGameType = "";
let currentGameKey = null;

function handlePlay(gameKey, status) {
  if (status === "locked") return;
  currentGameKey = gameKey;
  document.getElementById('nameModal').style.display = 'flex';
}


function startGame(gameType) {
  const name = prompt("Masukkan Nama Lengkap:");
  if (!name) return;
  currentPlayerName = name;
  currentGameType = gameType;
  openGame(gameType);
}

async function finishGame(score) {
  if (!currentPlayerName) return;
  await fetch(`/leaderboard?name=${encodeURIComponent(currentPlayerName)}&score=${score}`, { method: "POST" });
  alert(`Game ${currentGameType} selesai! Skor kamu: ${score}`);
  loadLeaderboard();
  closeGame();
}

function toggleGameStatus(gameKey) {
  fetch(`/cms/games/${gameKey}/toggle`, { method: "POST" })
    .then(res => res.json())
    .then(data => {
      if (data.status === 'success') {
        const gameCard = document.querySelector(`[data-key="${gameKey}"]`);
        const button = gameCard.querySelector('button');
        gameCard.classList.remove('disabled');
        button.disabled = false;
      }
    })
    .catch(err => {
      alert("Error: " + err.message);
    });
}

function closeNameModal() {
  document.getElementById('nameModal').style.display = 'none';
}

function submitName() {
  const name = document.getElementById('playerName').value.trim();
  if (!name) {
    alert("Nama tidak boleh kosong");
    return;
  }
  localStorage.setItem(`name_${currentGameKey}`, name);
  checkOrSaveName(name);
}
function checkOrSaveName(name) {
  fetch("/fans-corner/check-or-save-name", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: `game_key=${encodeURIComponent(currentGameKey)}&name=${encodeURIComponent(name)}`
  })
    .then(res => res.json())
    .then(() => {
      closeNameModal();
      setTimeout(() => {
        openGame(currentGameKey);
      }, 300); // jeda 0.3 detik biar transisi mulus
    })
    .catch(err => {
      alert("Terjadi kesalahan: " + err.message);
    });
}

function openGame(gameKey) {
  const gameModal = document.getElementById("gameModal");
  const gameFrame = document.getElementById("gameFrame");
  gameFrame.src = `/games/${gameKey}`;
  gameModal.style.display = "flex";
}



function closeGame() {
  const gameModal = document.getElementById("gameModal");
  const gameFrame = document.getElementById("gameFrame");
  gameFrame.src = "";
  gameModal.style.display = "none";
}

loadLeaderboard();
