let currentPlayerName = "";
let currentGameType = "";

function openGame(gameName) {
  const modal = document.getElementById('gameModal');
  const frame = document.getElementById('gameFrame');
  frame.src = `/game/${gameName}`;
  modal.style.display = 'flex';
}

function closeGame() {
  const modal = document.getElementById('gameModal');
  const frame = document.getElementById('gameFrame');
  frame.src = '';
  modal.style.display = 'none';
}

async function loadLeaderboard() {
  const res = await fetch("/leaderboard");
  const data = await res.json();
  const list = document.getElementById("leaderboardList");
  list.innerHTML = "";
  data.forEach((player) => {
    const li = document.createElement("li");
    li.textContent = `${player.name} - ${player.score}`;
    list.appendChild(li);
  });
}

// Langkah 1: Minta nama, simpan, lalu buka game
function startGame(gameType) {
  const name = prompt("Masukkan Nama Lengkap:");
  if (!name) return;

  currentPlayerName = name;
  currentGameType = gameType;
  openGame(gameType);
}

// Langkah 2: Dipanggil setelah game selesai untuk submit skor
async function finishGame(score) {
  if (!currentPlayerName) return;

  await fetch(`/leaderboard?name=${encodeURIComponent(currentPlayerName)}&score=${score}`, {
    method: "POST"
  });

  alert(`Game ${currentGameType} selesai! Skor kamu: ${score}`);
  loadLeaderboard();
  closeGame();
}

loadLeaderboard();
