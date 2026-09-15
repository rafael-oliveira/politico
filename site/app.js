const DATA_URL = "data/candidatos.exemplo.json"; // trocar para candidatos.json quando o pipeline gerar dados reais

const el = {
  busca: document.getElementById("busca"),
  filtros: document.getElementById("filtros"),
  lista: document.getElementById("lista"),
  contagem: document.getElementById("contagem"),
  overlay: document.getElementById("overlay"),
  detalheConteudo: document.getElementById("detalhe-conteudo"),
  fechar: document.getElementById("fechar"),
  fonteInfo: document.getElementById("fonte-info"),
};

let TODOS = [];
let cargoAtivo = "TODOS";

function formatarMoeda(valor) {
  if (valor === null || valor === undefined) return "não informado";
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 });
}

function badgesDoCard(c) {
  const badges = [];
  if (c.concorrendo_reeleicao) {
    badges.push(`<span class="badge badge--reeleicao">🔁 Reeleição</span>`);
  } else if (c.candidaturas_anteriores > 0) {
    badges.push(`<span class="badge">🗳️ ${c.candidaturas_anteriores}ª candidatura</span>`);
  } else if (c.candidaturas_anteriores === 0) {
    badges.push(`<span class="badge">✨ Estreante</span>`);
  }
  if (c.ocupacao_declarada) {
    badges.push(`<span class="badge">💼 ${tituloCase(c.ocupacao_declarada)}</span>`);
  }
  if (c.processos && c.processos.length > 0) {
    badges.push(`<span class="badge badge--processo">⚠️ ${c.processos.length} processo${c.processos.length > 1 ? "s" : ""}</span>`);
  }
  return badges.join("");
}

function tituloCase(texto) {
  return texto
    .toLowerCase()
    .split(" ")
    .map((p) => (p.length > 2 ? p[0].toUpperCase() + p.slice(1) : p))
    .join(" ");
}

function cargoAbrev(cargo) {
  return cargo.toUpperCase().includes("FEDERAL") ? "Dep. Federal" : "Dep. Estadual";
}

function renderLista() {
  const termo = el.busca.value.trim().toLowerCase();

  const filtrados = TODOS.filter((c) => {
    const bateCargo = cargoAtivo === "TODOS" || c.cargo.toUpperCase() === cargoAtivo;
    if (!bateCargo) return false;
    if (!termo) return true;
    return (
      (c.nome_urna || "").toLowerCase().includes(termo) ||
      (c.numero_urna || "").includes(termo) ||
      (c.partido_sigla || "").toLowerCase().includes(termo) ||
      (c.municipio_ue || "").toLowerCase().includes(termo)
    );
  });

  el.contagem.textContent = `${filtrados.length} candidato${filtrados.length === 1 ? "" : "s"}`;

  if (filtrados.length === 0) {
    el.lista.innerHTML = `<div class="vazio">Nenhum candidato encontrado com esses termos.</div>`;
    return;
  }

  el.lista.innerHTML = filtrados
    .map(
      (c) => `
    <button class="card" data-id="${c.sq_candidato}">
      <div class="card__numero">${c.numero_urna || "—"}</div>
      <div class="card__corpo">
        <p class="card__nome">${c.nome_urna}</p>
        <p class="card__sub">${cargoAbrev(c.cargo)} · ${c.partido_sigla} · ${tituloCase(c.municipio_ue || "")}</p>
        <div class="badges">${badgesDoCard(c)}</div>
      </div>
    </button>
  `
    )
    .join("");

  el.lista.querySelectorAll(".card").forEach((cardEl) => {
    cardEl.addEventListener("click", () => abrirDetalhe(cardEl.dataset.id));
  });
}

function abrirDetalhe(id) {
  const c = TODOS.find((x) => x.sq_candidato === id);
  if (!c) return;

  const bensHtml = (c.bens || []).length
    ? c.bens.map((b) => `<div class="det-bem">${b.tipo} — ${formatarMoeda(parseFloat(b.valor))}</div>`).join("")
    : `<p class="det-vazio">Nenhum bem declarado.</p>`;

  const processosHtml = (c.processos || []).length
    ? c.processos.map((p) => `<div class="det-processo"><strong>${p.tipo}</strong> — ${p.descricao}</div>`).join("")
    : `<p class="det-vazio">Nenhum processo constando na base consultada.</p>`;

  el.detalheConteudo.innerHTML = `
    <p class="det-nome">${c.nome_urna}</p>
    <p class="det-sub">${c.nome_civil ? tituloCase(c.nome_civil) + " · " : ""}${cargoAbrev(c.cargo)} · Nº ${c.numero_urna} · ${c.partido_sigla}</p>

    <div class="det-secao">
      <h3>Perfil</h3>
      <div class="det-linha"><span class="det-linha__label">Município de candidatura</span><span>${tituloCase(c.municipio_ue || "—")}</span></div>
      <div class="det-linha"><span class="det-linha__label">Ocupação declarada</span><span>${c.ocupacao_declarada ? tituloCase(c.ocupacao_declarada) : "—"}</span></div>
      <div class="det-linha"><span class="det-linha__label">Escolaridade</span><span>${c.grau_instrucao ? tituloCase(c.grau_instrucao) : "—"}</span></div>
    </div>

    <div class="det-secao">
      <h3>Trajetória eleitoral</h3>
      <div class="det-linha"><span class="det-linha__label">Concorrendo à reeleição</span><span>${c.concorrendo_reeleicao ? "Sim" : "Não"}</span></div>
      <div class="det-linha"><span class="det-linha__label">Candidaturas anteriores (desde 2010)</span><span>${c.candidaturas_anteriores ?? "não calculado"}</span></div>
    </div>

    <div class="det-secao">
      <h3>Bens declarados — total ${formatarMoeda(c.bens_total_declarado)}</h3>
      ${bensHtml}
    </div>

    <div class="det-secao">
      <h3>Doações recebidas na campanha</h3>
      <p>${formatarMoeda(c.doacoes_total)}</p>
    </div>

    <div class="det-secao">
      <h3>Processos judiciais ligados à candidatura</h3>
      ${processosHtml}
      <p class="det-vazio" style="margin-top:0.5rem">Um processo em andamento não é uma condenação — todo candidato tem direito à presunção de inocência.</p>
    </div>

    <p class="det-fonte">Fonte: ${c.fonte}</p>
  `;

  el.overlay.hidden = false;
  document.body.style.overflow = "hidden";
}

function fecharDetalhe() {
  el.overlay.hidden = true;
  document.body.style.overflow = "";
}

el.fechar.addEventListener("click", fecharDetalhe);
el.overlay.addEventListener("click", (e) => {
  if (e.target === el.overlay) fecharDetalhe();
});
el.busca.addEventListener("input", renderLista);

el.filtros.addEventListener("click", (e) => {
  const btn = e.target.closest(".filtro");
  if (!btn) return;
  el.filtros.querySelectorAll(".filtro").forEach((b) => b.classList.remove("filtro--ativo"));
  btn.classList.add("filtro--ativo");
  cargoAtivo = btn.dataset.cargo;
  renderLista();
});

fetch(DATA_URL)
  .then((r) => r.json())
  .then((json) => {
    TODOS = json.candidatos;
    const avisoExemplo = json.aviso ? ` — ${json.aviso}` : "";
    el.fonteInfo.textContent = `Dados gerados em ${new Date(json.gerado_em).toLocaleString("pt-BR")}${avisoExemplo}`;
    renderLista();
  })
  .catch((err) => {
    el.lista.innerHTML = `<div class="vazio">Não foi possível carregar os dados (${err.message}).</div>`;
  });
