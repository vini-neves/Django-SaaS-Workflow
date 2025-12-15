// static/js/client.js

document.addEventListener("DOMContentLoaded", () => {
  // --- 1. Inicializações ---
  if (typeof feather !== "undefined") feather.replace();

  const table = $("#client-table").DataTable({
    language: { url: "//cdn.datatables.net/plug-ins/1.13.6/i18n/pt-BR.json" },
    order: [[0, "asc"]],
  });

  // --- 2. Controle do Modal ---
  const modal = document.getElementById("client-modal");
  const openBtn = document.getElementById("btn-open-modal");
  // Busca o botão de fechar DENTRO do modal para garantir que é o certo
  const closeBtn = modal ? modal.querySelector(".close-button") : null;

  const form = document.getElementById("client-form");
  const modalTitle = document.getElementById("modal-title");
  const hiddenIdInput = document.getElementById("client_id_hidden");

  function clearSocialHighlights() {
    document.querySelectorAll(".social-connect-item").forEach((item) => {
      item.classList.remove("is-connected");
      item.title = item.title.replace(" (Conectado)", ""); // Limpa tooltip
    });
  }

  if (modal && openBtn && closeBtn) {
    // Abrir Modal (Cadastro Limpo)
    openBtn.addEventListener("click", () => {
      form.reset();
      hiddenIdInput.value = "";
      modalTitle.innerText = "Cadastrar Novo Cliente";

      clearSocialHighlights();

      // Reseta o checkbox de ativo
      const activeCheck = document.getElementById("id_is_active");
      if (activeCheck) activeCheck.checked = true;

      modal.style.display = "flex";
    });

    // Fechar Modal (Botão X)
    closeBtn.addEventListener("click", () => {
      modal.style.display = "none";
    });

    // Fechar Modal (Clicar no fundo escuro)
    window.addEventListener("click", (e) => {
      if (e.target === modal) {
        modal.style.display = "none";
      }
    });
  } else {
    console.error("Erro Crítico: Elementos do modal não encontrados no DOM.");
    console.log(
      "Modal:",
      modal,
      "Btn Abrir:",
      openBtn,
      "Btn Fechar:",
      closeBtn
    );
  }

  // --- 3. Lógica de Edição ---
  // Usamos delegação de eventos pois os botões estão dentro do DataTable
  document
    .querySelector("#client-table")
    .addEventListener("click", async (e) => {
      if (e.target.closest(".edit-client-btn")) {
        const btn = e.target.closest(".edit-client-btn");
        const clientId = btn.dataset.id;

        // Busca dados do cliente
        try {
          const response = await fetch(
            `${GET_CLIENT_DATA_URL_BASE}${clientId}/get/`
          );
          const data = await response.json();

          // Preenche o formulário
          hiddenIdInput.value = data.id;
          document.getElementById("id_name").value = data.name;
          document.getElementById("id_cnpj").value = data.cnpj || "";
          document.getElementById("id_nome_representante").value =
            data.nome_representante || "";
          document.getElementById("id_celular_representante").value =
            data.celular_representante || "";
          document.getElementById("id_email_representante").value =
            data.email_representante || "";
          document.getElementById("id_data_inicio_contrato").value =
            data.data_inicio_contrato || "";
          document.getElementById("id_data_finalizacao_contrato").value =
            data.data_finalizacao_contrato || "";
          document.getElementById("id_is_active").checked = data.is_active;

          clearSocialHighlights(); // Limpa primeiro

          if (data.connected_platforms && data.connected_platforms.length > 0) {
            data.connected_platforms.forEach((platform) => {
              // Procura o elemento pela classe .sc-nome_da_rede
              // Ex: .sc-facebook, .sc-instagram
              const icon = document.querySelector(
                `.social-connect-item.sc-${platform}`
              );
              if (icon) {
                icon.classList.add("is-connected");
                icon.title += " (Conectado)"; // Dica visual ao passar o mouse
              }
            });
          }

          modalTitle.innerText = "Editar Cliente";
          modal.style.display = "flex";
        } catch (error) {
          console.error(error);
          Swal.fire("Erro", "Não foi possível carregar os dados.", "error");
        }
      }
    });

  // --- 4. Submissão do Formulário (AJAX) ---
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(form);

    try {
      const response = await fetch(SAVE_CLIENT_URL, {
        method: "POST",
        headers: { "X-CSRFToken": CSRF_TOKEN },
        body: formData,
      });
      const result = await response.json();

      if (response.ok) {
        Swal.fire("Sucesso!", result.message, "success").then(() => {
          location.reload(); // Recarrega para atualizar a tabela
        });
      } else {
        Swal.fire("Erro", "Verifique os campos.", "error");
        console.error(result.errors);
      }
    } catch (error) {
      Swal.fire("Erro", "Erro de conexão.", "error");
    }
  });

  // --- 5. Máscaras de Input (CNPJ e Telefone) ---

  // Máscara CNPJ (00.000.000/0000-00)
  const cnpjInput = document.getElementById("id_cnpj");
  if (cnpjInput) {
    cnpjInput.addEventListener("input", function (e) {
      let x = e.target.value
        .replace(/\D/g, "")
        .match(/(\d{0,2})(\d{0,3})(\d{0,3})(\d{0,4})(\d{0,2})/);
      e.target.value = !x[2]
        ? x[1]
        : x[1] +
          "." +
          x[2] +
          "." +
          x[3] +
          "/" +
          x[4] +
          (x[5] ? "-" + x[5] : "");
    });
  }

  // Máscara Celular ( (00) 00000-0000 )
  const phoneInput = document.getElementById("id_celular_representante");
  if (phoneInput) {
    phoneInput.addEventListener("input", function (e) {
      let x = e.target.value
        .replace(/\D/g, "")
        .match(/(\d{0,2})(\d{0,5})(\d{0,4})/);
      e.target.value = !x[2]
        ? x[1]
        : "(" + x[1] + ") " + x[2] + (x[3] ? "-" + x[3] : "");
    });
  }

  // --- 6. Conectar Social (Mockup) ---
  window.connectSocial = function (platform) {
    const clientId = document.getElementById("client_id_hidden").value;

    if (!clientId) {
      Swal.fire(
        "Atenção",
        "Salve o cliente primeiro antes de conectar redes.",
        "warning"
      );
      return;
    }

    if (platform === "facebook" || platform === "instagram") {
      window.location.href = `/meta/connect/${clientId}/`;
    } else if (platform === "linkedin") {
      // NOVA ROTA
      window.location.href = `/linkedin/connect/${clientId}/`;
    } else {
      Swal.fire("Em breve", "Integração em desenvolvimento.", "info");
    }
  };
});
