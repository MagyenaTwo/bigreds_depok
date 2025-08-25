function handlePlay(gameKey, status) {
  if (status === "locked") {
    alert("Game ini belum dibuka!");
    return;
  }

  let content = "";
  switch (gameKey) {
    case "tebak-skor":
      content = `<iframe src="/games/tebak-skor" style="width:100%;height:100%;border:none;"></iframe>`;
      break;
    case "quiz":
      content = `<iframe src="/games/quiz" style="width:100%;height:100%;border:none;"></iframe>`;
      break;
    case "memory-game":
      content = `<iframe src="/api/memory" style="width:100%;height:100%;border:none;"></iframe>`;
  break;
    case "trivia":
      content = `<iframe src="/games/trivia" style="width:100%;height:100%;border:none;"></iframe>`;
      break;
    case "puzzle":
      content = `<iframe src="/games/puzzle" style="width:100%;height:100%;border:none;"></iframe>`;
      break;
     case "penalti_game":
      content = `<iframe src="/games/penalti" style="width:100%;height:100%;border:none;"></iframe>`;
      break;
    default:
      content = `<p>Game tidak ditemukan.</p>`;
  }

  document.getElementById("gameModalBody").innerHTML = content;
  document.getElementById("gameModal").style.display = "flex";
}

function closeModal() {
  document.getElementById("gameModal").style.display = "none";
  document.getElementById("gameModalBody").innerHTML = "";
}
