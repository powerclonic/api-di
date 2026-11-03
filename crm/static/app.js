const $ = (s) => document.querySelector(s);
let visao = "minhas";
let eu = null;

async function api(path, { method = "GET", body } = {}) {
  const res = await fetch(path, {
    method,
    credentials: "same-origin",
    headers: {
      "X-Requested-With": "fetch", // exigido pela proteção CSRF em métodos que alteram estado
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401) { mostrarLogin(); throw new Error("Sessão expirada"); }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const d = data.detail;
    throw new Error(Array.isArray(d) ? d.map((e) => e.msg).join("; ") : d || `Erro ${res.status}`);
  }
  return res.json();
}

function erro(msg) {
  const el = $("#erro");
  el.textContent = msg || "";
  el.hidden = !msg;
}

function mostrarLogin() {
  $("#login").hidden = false;
  $("#app").hidden = true;
  $("#user").hidden = true;
}

const PROXIMO = { aberta: ["em_andamento", "Iniciar"], em_andamento: ["concluida", "Concluir"], concluida: ["aberta", "Reabrir"] };
const ROTULO = { aberta: "Aberta", em_andamento: "Em andamento", concluida: "Concluída" };

function render(tarefas) {
  const ul = $("#lista");
  ul.replaceChildren();
  $("#vazio").hidden = tarefas.length > 0;
  for (const t of tarefas) {
    const li = document.createElement("li");
    li.className = t.status;

    const titulo = document.createElement("div");
    titulo.className = "titulo";
    titulo.textContent = t.titulo;

    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = [
      `Associado ${t.cpf_cnpj}`,
      t.prazo ? `prazo ${t.prazo.split("-").reverse().join("/")}` : "sem prazo",
      ROTULO[t.status],
      t.delegada ? `${t.solicitante_ldap} → ${t.responsavel_ldap}` : null,
    ].filter(Boolean).join(" · ");

    const acoes = document.createElement("div");
    acoes.className = "acoes";
    if (visao === "minhas") {
      const [prox, rotulo] = PROXIMO[t.status];
      const b = document.createElement("button");
      b.textContent = rotulo;
      b.onclick = () => agir(() => api(`/tarefas/${t.id}/status`, { method: "POST", body: { status: prox } }));
      const ld = document.createElement("input");
      ld.placeholder = "Delegar para (LDAP)";
      const bd = document.createElement("button");
      bd.textContent = "Delegar";
      bd.onclick = () => ld.value.trim() && agir(() => api(`/tarefas/${t.id}/delegar`, { method: "POST", body: { responsavel_ldap: ld.value.trim() } }));
      acoes.append(b, ld, bd);
    }
    li.append(titulo, meta, acoes);
    ul.append(li);
  }
}

async function agir(fn) {
  erro("");
  try { await fn(); await carregar(); } catch (e) { erro(e.message); }
}

async function carregar() {
  render(await api(`/tarefas?visao=${visao}`));
}

async function iniciar() {
  try {
    eu = await api("/auth/me");
  } catch { return mostrarLogin(); }
  $("#user-nome").textContent = eu.nome;
  $("#user").hidden = false;
  $("#login").hidden = true;
  $("#app").hidden = false;
  agir(() => Promise.resolve());
}

$("#form-nova").onsubmit = (e) => {
  e.preventDefault();
  const f = e.target;
  const body = Object.fromEntries(new FormData(f));
  for (const k of ["prazo", "responsavel_ldap"]) if (!body[k]) delete body[k];
  agir(async () => { await api("/tarefas", { method: "POST", body }); f.reset(); });
};

$("#abas").onclick = (e) => {
  const v = e.target.dataset.visao;
  if (!v) return;
  visao = v;
  document.querySelectorAll("#abas button").forEach((b) => b.classList.toggle("ativa", b === e.target));
  agir(() => Promise.resolve());
};

$("#btn-logout").onclick = async () => {
  try {
    const { logout_url } = await api("/auth/logout", { method: "POST" });
    location.href = logout_url;
  } catch (e) { erro(e.message); }
};

iniciar();
