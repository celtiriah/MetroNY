/**
 * Frontend JavaScript Vanilla para Metro NY (MTA NYCT)
 * Consume la API REST de Python Flask conectada a Oracle Database.
 */

// Estado global en memoria
let allStations = [];
let allQueriesCatalog = [];

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initTabs();
  checkConnectionStatus();
  loadDashboardData();
  loadLines();
  loadStations();
  initQueriesModule();
});

// -----------------------------------------------------------------------------
// 0. TEMA CLARO / OSCURO (PERSISTENCIA CON LOCALSTORAGE)
// -----------------------------------------------------------------------------
function initTheme() {
  const toggleBtn = document.getElementById("btn-theme-toggle");
  const themeIcon = document.getElementById("theme-icon");
  const themeText = document.getElementById("theme-text");

  // Leer tema guardado o usar 'light' por defecto
  const savedTheme = localStorage.getItem("mta-theme") || "light";
  applyTheme(savedTheme);

  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") || "light";
      const newTheme = current === "dark" ? "light" : "dark";
      applyTheme(newTheme);
      localStorage.setItem("mta-theme", newTheme);
    });
  }

  function applyTheme(theme) {
    if (theme === "dark") {
      document.documentElement.setAttribute("data-theme", "dark");
      if (themeIcon) themeIcon.textContent = "☀️";
      if (themeText) themeText.textContent = "Modo Claro";
    } else {
      document.documentElement.removeAttribute("data-theme");
      if (themeIcon) themeIcon.textContent = "🌙";
      if (themeText) themeText.textContent = "Modo Oscuro";
    }
  }
}


// -----------------------------------------------------------------------------
// 1. MANEJO DE PESTAÑAS (TABS)
// -----------------------------------------------------------------------------
function initTabs() {
  const buttons = document.querySelectorAll(".tab-btn");
  const contents = document.querySelectorAll(".tab-content");

  buttons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-tab");

      buttons.forEach(b => b.classList.remove("active"));
      contents.forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const target = document.getElementById(targetId);
      if (target) target.classList.add("active");
    });
  });
}


// -----------------------------------------------------------------------------
// 2. VERIFICAR CONEXIÓN CON ORACLE
// -----------------------------------------------------------------------------
async function checkConnectionStatus() {
  const badge = document.getElementById("connection-badge");
  const text = document.getElementById("connection-text");

  try {
    const res = await fetch("/api/status");
    const data = await res.json();

    if (data.connected) {
      badge.className = "connection-badge";
      text.textContent = `🟢 Oracle Activo (${data.pdb || "FREEPDB1"}) | Esquema: ${data.user}`;
    } else {
      badge.className = "connection-badge badge-error";
      text.textContent = "🔴 Error de conexión a Oracle";
    }
  } catch (err) {
    badge.className = "connection-badge badge-error";
    text.textContent = "🔴 Servidor desconectado";
  }
}


// -----------------------------------------------------------------------------
// 3. DASHBOARD: MÉTRICAS Y RESUMEN
// -----------------------------------------------------------------------------
async function loadDashboardData() {
  try {
    const res = await fetch("/api/resumen");
    const data = await res.json();

    document.getElementById("val-lineas").textContent = data.TOTAL_LINEAS ?? "-";
    document.getElementById("val-estaciones").textContent = data.TOTAL_ESTACIONES ?? "-";
    document.getElementById("val-trenes").textContent = data.TOTAL_TRENES ?? "-";
    document.getElementById("val-empleados").textContent = data.TOTAL_EMPLEADOS ?? "-";
    document.getElementById("val-tarjetas").textContent = data.TOTAL_TARJETAS ?? "-";
    document.getElementById("val-incidentes").textContent = data.INCIDENTES_ABIERTOS ?? "-";
  } catch (err) {
    console.error("Error al cargar resumen:", err);
  }
}


// -----------------------------------------------------------------------------
// 4. LÍNEAS DEL METRO
// -----------------------------------------------------------------------------
function getBulletColorClass(codigo) {
  const map = {
    "1": "bullet-red",
    "A": "bullet-blue",
    "C": "bullet-blue",
    "7": "bullet-purple",
    "L": "bullet-grey"
  };
  return map[codigo] || "bullet-blue";
}

async function loadLines() {
  const dashContainer = document.getElementById("dashboard-lines-grid");
  const fullContainer = document.getElementById("full-lines-grid");

  try {
    const res = await fetch("/api/lineas");
    const json = await res.json();
    const lines = json.rows || [];

    const html = lines.map(line => `
      <div class="line-card">
        <div class="line-header">
          <div class="line-title-wrap">
            <span class="mta-bullet ${getBulletColorClass(line.CODIGO)}">${line.CODIGO}</span>
            <span class="line-name">${line.NOMBRE}</span>
          </div>
          <span class="badge-tag">${line.ESTADO_OPERATIVO}</span>
        </div>
        <div class="line-details">
          <div class="detail-row">
            <span>Color Oficial:</span>
            <strong>${line.COLOR}</strong>
          </div>
          <div class="detail-row">
            <span>Servicio:</span>
            <span>${line.TIPO_SERVICIO}</span>
          </div>
          <div class="detail-row">
            <span>Estaciones Asignadas:</span>
            <strong>${line.TOTAL_ESTACIONES} paradas</strong>
          </div>
        </div>
      </div>
    `).join("");

    if (dashContainer) dashContainer.innerHTML = html;
    if (fullContainer) fullContainer.innerHTML = html;
  } catch (err) {
    console.error("Error al cargar líneas:", err);
  }
}


// -----------------------------------------------------------------------------
// 5. ESTACIONES Y BUSCADOR
// -----------------------------------------------------------------------------
async function loadStations() {
  const tbody = document.getElementById("tbody-stations");
  const searchInput = document.getElementById("input-search-stations");

  try {
    const res = await fetch("/api/estaciones");
    const json = await res.json();
    allStations = json.rows || [];
    renderStationsTable(allStations);

    searchInput.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase().trim();
      const filtered = allStations.filter(s =>
        s.NOMBRE.toLowerCase().includes(q) ||
        s.DISTRITO.toLowerCase().includes(q) ||
        s.CODIGO.toLowerCase().includes(q)
      );
      renderStationsTable(filtered);
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="loading-cell">Error al conectar con Oracle: ${err.message}</td></tr>`;
  }
}

function renderStationsTable(stations) {
  const tbody = document.getElementById("tbody-stations");
  if (!stations.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No se encontraron estaciones coincidentes.</td></tr>`;
    return;
  }

  tbody.innerHTML = stations.map(st => `
    <tr>
      <td><code>${st.CODIGO}</code></td>
      <td><strong>${st.NOMBRE}</strong></td>
      <td>${st.DISTRITO}</td>
      <td>${st.TOTAL_PLATAFORMAS}</td>
      <td>${st.ACCESIBILIDAD === "S" ? "♿ Accesible (ADA)" : "No accesible"}</td>
      <td>${st.ELEVADORES_DISPONIBLES === "S" ? "✅ Sí" : "❌ No"}</td>
      <td><span class="badge-tag">${st.ESTADO_OPERATIVO}</span></td>
    </tr>
  `).join("");
}


// -----------------------------------------------------------------------------
// 6. MÓDULO DE 15 CONSULTAS MÍNIMAS
// -----------------------------------------------------------------------------
async function initQueriesModule() {
  const select = document.getElementById("select-query");
  const btnRun = document.getElementById("btn-run-query");

  try {
    const res = await fetch("/api/consultas");
    allQueriesCatalog = await res.json();

    select.innerHTML = `<option value="">-- Selecciona una consulta (1 al 15) --</option>` +
      allQueriesCatalog.map(q => `<option value="${q.id}">${q.titulo}</option>`).join("");

    select.addEventListener("change", () => {
      const qid = parseInt(select.value, 10);
      const query = allQueriesCatalog.find(q => q.id === qid);
      if (query) {
        showQueryMeta(query.titulo, query.descripcion, "Haz clic en 'Ejecutar Consulta' para ver el código SQL y la tabla de resultados.");
      } else {
        document.getElementById("query-meta-box").style.display = "none";
      }
    });

    btnRun.addEventListener("click", runSelectedQuery);
  } catch (err) {
    console.error("Error al inicializar consultas:", err);
  }
}

function showQueryMeta(title, desc, sql) {
  const box = document.getElementById("query-meta-box");
  document.getElementById("query-meta-title").textContent = title;
  document.getElementById("query-meta-desc").textContent = desc;
  document.getElementById("query-meta-sql").textContent = sql;
  box.style.display = "block";
}

async function runSelectedQuery() {
  const select = document.getElementById("select-query");
  const btnRun = document.getElementById("btn-run-query");
  const qid = select.value;

  if (!qid) {
    alert("Por favor selecciona una de las 15 consultas del listado.");
    return;
  }

  btnRun.disabled = true;
  btnRun.innerHTML = `<svg class="spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a10 10 0 0 1 10 10"/></svg> Ejecutando en Oracle...`;

  const countBadge = document.getElementById("results-count-badge");
  const pdbBadge = document.getElementById("results-pdb-badge");
  const thead = document.getElementById("thead-query-results");
  const tbody = document.getElementById("tbody-query-results");

  try {
    const res = await fetch(`/api/consultas/${qid}`);
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || "Error al ejecutar consulta");

    showQueryMeta(data.titulo, data.descripcion, data.sql);

    countBadge.textContent = `${data.total} filas recuperadas`;
    countBadge.style.display = "inline-block";

    pdbBadge.textContent = `PDB: ${data.pdb || "FREEPDB1"}`;
    pdbBadge.style.display = "inline-block";

    // Encabezados de tabla
    thead.innerHTML = `<tr>${data.columns.map(col => `<th>${col}</th>`).join("")}</tr>`;

    // Filas de tabla
    if (data.rows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="${data.columns.length}" class="empty-state">La consulta no arrojó resultados para los parámetros actuales.</td></tr>`;
    } else {
      tbody.innerHTML = data.rows.map(row => `
        <tr>
          ${data.columns.map(col => `<td>${row[col] ?? "-"}</td>`).join("")}
        </tr>
      `).join("");
    }
  } catch (err) {
    thead.innerHTML = `<tr><th>Error</th></tr>`;
    tbody.innerHTML = `<tr><td class="empty-state" style="color:#f87171;">Error de Oracle: ${err.message}</td></tr>`;
  } finally {
    btnRun.disabled = false;
    btnRun.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Ejecutar Consulta`;
  }
}

