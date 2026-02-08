const ROOMS_ENDPOINT = "/api/rooms";
const POLL_INTERVAL_MS = 5000;

const roomsList = document.getElementById("rooms-list");

function formatDuration(totalSeconds) {
  if (totalSeconds == null) {
    return "";
  }

  const seconds = Math.max(0, Number(totalSeconds));
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remaining = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${remaining}s`;
  }
  if (minutes > 0) {
    return `${minutes}m ${remaining}s`;
  }
  return `${remaining}s`;
}

function renderRooms(rooms) {
  roomsList.innerHTML = "";

  if (!rooms || rooms.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "Sem salas registadas.";
    roomsList.appendChild(empty);
    return;
  }

  rooms.forEach((room) => {
    const card = document.createElement("div");
    card.className = "room-card";

    const info = document.createElement("div");
    info.className = "room-info";

    const dot = document.createElement("span");
    dot.className = `status-dot ${room.state === 1 ? "status-busy" : "status-free"}`;

    const name = document.createElement("span");
    name.className = "room-name";
    name.textContent = room.room_name;

    info.appendChild(dot);
    info.appendChild(name);

    const meta = document.createElement("div");
    meta.className = "room-meta";
    if (room.state === 1) {
      const duration = formatDuration(room.occupied_seconds);
      meta.textContent = `Ocupada há ${duration}`;
    } else {
      meta.textContent = "Disponível";
    }

    card.appendChild(info);
    card.appendChild(meta);
    roomsList.appendChild(card);
  });
}

async function fetchRooms() {
  try {
    const response = await fetch(ROOMS_ENDPOINT);
    if (!response.ok) {
      throw new Error("Failed to load rooms");
    }
    const data = await response.json();
    renderRooms(data);
  } catch (error) {
    roomsList.innerHTML = "";
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "Erro ao carregar salas.";
    roomsList.appendChild(empty);
  }
}

fetchRooms();
setInterval(fetchRooms, POLL_INTERVAL_MS);
