const $ = (s) => document.querySelector(s);
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
const dataBR = (d) => d.split("-").reverse().join("/");

function item(classe, titulo, meta, acoes = []) {
  const li = document.createElement("li");
  if (classe) li.className = classe;
  const t = document.createElement("div");
  t.className = "titulo";
  t.textContent = titulo;
  const m = document.createElement("div");
  m.className = "meta";
  m.textContent = meta;
  li.append(t, m);
  if (acoes.length) {
    const a = document.createElement("div");
    a.className = "acoes";
    a.append(...acoes);
    li.append(a);
  }
  return li;
}

function botao(texto, fn) {
  const b = document.createElement("button");
  b.textContent = texto;
  b.onclick = fn;
  return b;
}

function preencher(painel, itens) {
  const ul = $(`${painel} .lista`);
  ul.replaceChildren(...itens);
  $(`${painel} .vazio`).hidden = itens.length > 0;
}

function metaTarefa(t, delegacao) {
  return [
    `Associado ${t.cpf_cnpj}`,
    t.prazo ? `prazo ${dataBR(t.prazo)}` : "sem prazo",
    ROTULO[t.status],
    delegacao ? `${t.solicitante_ldap} → ${t.responsavel_ldap}` : null,
  ].filter(Boolean).join(" · ");
}

function renderMinhas(tarefas) {
  preencher("#p-minhas", tarefas.map((t) => {
    const [prox, rotulo] = PROXIMO[t.status];
    const ld = document.createElement("input");
    ld.placeholder = "Delegar (LDAP)";
    return item(t.status, t.titulo, metaTarefa(t, t.delegada), [
      botao(rotulo, () => agir(() => api(`/tarefas/${t.id}/status`, { method: "POST", body: { status: prox } }))),
      ld,
      botao("Delegar", () => ld.value.trim() && agir(() => api(`/tarefas/${t.id}/delegar`, { method: "POST", body: { responsavel_ldap: ld.value.trim() } }))),
    ]);
  }));
}

function renderAcompanhando(tarefas) {
  preencher("#p-acomp", tarefas.map((t) => item(t.status, t.titulo, metaTarefa(t, true))));
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
  const ul = $("#p-visitas .lista");
  ul.replaceChildren();
  $("#p-visitas .vazio").hidden = visitas.length > 0;
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

async function agir(fn) {
  erro("");
  try { await fn(); await carregar(); } catch (e) { erro(e.message); }
}

async function carregar() {
  const [minhas, acomp, visitas] = await Promise.all([
    api("/tarefas?visao=minhas"), api("/tarefas?visao=acompanhando"), api("/visitas"),
  ]);
  renderMinhas(minhas);
  renderAcompanhando(acomp);
  renderVisitas(visitas);
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

$("#form-visita").onsubmit = (e) => {
  e.preventDefault();
  const f = e.target;
  agir(async () => { await api("/visitas", { method: "POST", body: Object.fromEntries(new FormData(f)) }); f.reset(); });
};

$("#form-visita").onsubmit = (e) => {
  e.preventDefault();
  const f = e.target;
  agir(async () => { await api("/visitas", { method: "POST", body: Object.fromEntries(new FormData(f)) }); f.reset(); });
};

$("#btn-logout").onclick = async () => {
  try {
    const { logout_url } = await api("/auth/logout", { method: "POST" });
    location.href = logout_url;
  } catch (e) { erro(e.message); }
};

iniciar();
