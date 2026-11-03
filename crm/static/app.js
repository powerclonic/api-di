const $ = (s) => document.querySelector(s);
let visao = "minhas";
let modulo = "tarefas";
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
  if (modulo === "visitas") renderVisitas(await api("/visitas"));
  else render(await api(`/tarefas?visao=${visao}`));
}

const ROTULO_VISITA = { rascunho: "Rascunho", revisao: "Em revisão", confirmada: "Confirmada" };
const linhas = (s) => s.split("\n").map((l) => l.trim()).filter(Boolean);

function campo(rotulo, el) {
  const l = document.createElement("label");
  l.append(rotulo, el);
  return l;
}

function area(valor, rows) {
  const t = document.createElement("textarea");
  t.rows = rows;
  t.value = valor;
  return t;
}

function secaoLida(rotulo, itens) {
  const div = document.createDocumentFragment();
  if (!itens.length) return div;
  const h = document.createElement("h3");
  h.textContent = rotulo;
  const ul = document.createElement("ul");
  for (const i of itens) {
    const li = document.createElement("li");
    li.textContent = i;
    ul.append(li);
  }
  div.append(h, ul);
  return div;
}

function renderVisitas(visitas) {
  const ul = $("#lista-visitas");
  ul.replaceChildren();
  $("#vazio-visitas").hidden = visitas.length > 0;
  for (const v of visitas) {
    const li = document.createElement("li");

    const titulo = document.createElement("div");
    titulo.className = "titulo";
    titulo.textContent = `Associado ${v.cpf_cnpj} · ${v.data.split("-").reverse().join("/")}`;

    const st = document.createElement("span");
    st.className = `status ${v.status}`;
    st.textContent = ROTULO_VISITA[v.status];

    li.append(titulo, st);

    if (v.status === "confirmada") {
      const lido = document.createElement("div");
      lido.className = "lido";
      const p = document.createElement("p");
      p.textContent = v.relato.resumo;
      lido.append(p, secaoLida("Pontos de atenção", v.relato.pontos_de_atencao), secaoLida("Próximos passos", v.relato.proximos_passos));
      li.append(lido);
    } else {
      const bruto = document.createElement("div");
      bruto.className = "relato-bruto";
      bruto.textContent = v.relato_bruto;

      const r = v.relato;
      const resumo = area(r ? r.resumo : "", 3);
      const pontos = area(r ? r.pontos_de_atencao.join("\n") : "", 3);
      const passos = area(r ? r.proximos_passos.join("\n") : "", 3);
      const editor = document.createElement("div");
      editor.className = "editor";
      editor.append(
        campo("Resumo", resumo),
        campo("Pontos de atenção (um por linha)", pontos),
        campo("Próximos passos (um por linha)", passos),
      );

      const acoes = document.createElement("div");
      acoes.className = "acoes";
      const salvar = document.createElement("button");
      salvar.textContent = "Salvar relato";
      const salvarRelato = () => api(`/visitas/${v.id}/relato`, {
        method: "PUT",
        body: { resumo: resumo.value.trim(), pontos_de_atencao: linhas(pontos.value), proximos_passos: linhas(passos.value) },
      });
      salvar.onclick = () => resumo.value.trim() ? agir(salvarRelato) : erro("Preencha o resumo");
      acoes.append(salvar);
      if (v.status === "revisao") {
        const conf = document.createElement("button");
        conf.textContent = "Confirmar";
        conf.onclick = () => {
          if (!resumo.value.trim()) return erro("Preencha o resumo");
          agir(async () => { await salvarRelato(); await api(`/visitas/${v.id}/confirmar`, { method: "POST" }); });
        };
        acoes.append(conf);
      }
      li.append(bruto, editor, acoes);
    }
    ul.append(li);
  }
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

$("#form-visita").onsubmit = (e) => {
  e.preventDefault();
  const f = e.target;
  agir(async () => { await api("/visitas", { method: "POST", body: Object.fromEntries(new FormData(f)) }); f.reset(); });
};

$("#modulos").onclick = (e) => {
  const m = e.target.dataset.modulo;
  if (!m) return;
  modulo = m;
  document.querySelectorAll("#modulos button").forEach((b) => b.classList.toggle("ativa", b === e.target));
  $("#view-tarefas").hidden = m !== "tarefas";
  $("#view-visitas").hidden = m !== "visitas";
  agir(() => Promise.resolve());
};

$("#btn-logout").onclick = async () => {
  try {
    const { logout_url } = await api("/auth/logout", { method: "POST" });
    location.href = logout_url;
  } catch (e) { erro(e.message); }
};

iniciar();
