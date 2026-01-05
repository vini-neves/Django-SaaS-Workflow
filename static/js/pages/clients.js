// Variável global para controlar o modal
let clientModalInstance = null;

document.addEventListener('DOMContentLoaded', function() {
  // 1. Move o modal para o corpo (Isso é essencial para o Bootstrap funcionar bem)
  const modalElement = document.getElementById('clientModal');
  if (modalElement) {
      document.body.appendChild(modalElement);
      
      // [CORREÇÃO]: Remove qualquer estilo manual que possa estar travando a tela
      modalElement.style.display = ''; 
      modalElement.removeAttribute('aria-modal');
      modalElement.removeAttribute('role');

      // 2. Inicializa o Bootstrap
      if (typeof bootstrap !== 'undefined') {
          clientModalInstance = new bootstrap.Modal(modalElement, {
              backdrop: 'static', // ou true, se preferir clicar fora pra fechar
              keyboard: false
          });
      }
  }
  
  // Inicializa máscaras e esconde inputs de arquivo
  setupInputMasks();
  const fileInputs = document.querySelectorAll('input[type="file"]');
  fileInputs.forEach(input => input.style.display = 'none');
});
// =================================================================
// 2. FUNÇÕES GLOBAIS (Acessíveis pelo HTML onclick="")
// =================================================================

function openCreateModal() {
    const form = document.getElementById('clientForm');
    if(form) form.reset();
    
    const idInput = document.getElementById('clientId');
    if(idInput) idInput.value = '';
    
    const title = document.getElementById('modalTitle');
    if(title) title.textContent = 'Cadastrar Novo Cliente';
    
    document.querySelectorAll('.social-toggle-list input[type="checkbox"]').forEach(el => el.checked = false);
    
    const activeCheck = document.getElementById('id_is_active');
    if(activeCheck) activeCheck.checked = true;

    clearErrors();

    if (clientModalInstance) {
        clientModalInstance.show();
    } else {
        console.error("Erro: Bootstrap Modal não foi inicializado.");
        alert("Erro ao carregar o modal. Recarregue a página.");
    }
}

function closeClientModal() {
    if (clientModalInstance) {
        clientModalInstance.hide();
    } else {
        const modalEl = document.getElementById('clientModal');
        if(modalEl) {
            modalEl.classList.remove('show');
            modalEl.style.display = 'none';
            document.body.classList.remove('modal-open');
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) backdrop.remove();
        }
    }
}

function editClient(buttonElement) {
  
    const button = buttonElement.closest('button');
    
    const url = button.dataset.url;

    console.log("Buscando dados em:", url);

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error("Erro na rede ou URL não encontrada (Status: " + response.status + ")");
            return response.json();
        })
        .then(data => {
            
            document.getElementById('clientId').value = data.id;
            
            const setVal = (id, val) => { const el = document.getElementById(id); if(el) el.value = val || ''; };
            const setCheck = (id, condition) => { const el = document.getElementById(id); if(el) el.checked = condition; };

            setVal('id_name', data.name);
            setVal('id_cnpj', data.cnpj);
            setVal('id_nome_representante', data.nome_representante);
            setVal('id_email_representante', data.email_representante);
            setVal('id_data_inicio_contrato', data.data_inicio_contrato);
            setVal('id_data_finalizacao_contrato', data.data_finalizacao_contrato);
            
            const activeCheck = document.getElementById('id_is_active');
            if(activeCheck) activeCheck.checked = data.is_active;

            const platforms = data.connected_platforms || [];
            setCheck('toggleInstagram', platforms.includes('instagram'));
            setCheck('toggleLinkedin', platforms.includes('linkedin-oauth2'));
            setCheck('toggleTiktok', platforms.includes('tiktok'));
            setCheck('toggleFacebook', platforms.includes('facebook'));

            const title = document.getElementById('modalTitle');
            if(title) title.textContent = 'Editar Cliente';
            
            if (typeof clearErrors === 'function') clearErrors();
            
            if (typeof clientModalInstance !== 'undefined') {
                clientModalInstance.show();
            } else {
                const modalEl = document.getElementById('clientModal');
                const modal = new bootstrap.Modal(modalEl);
                modal.show();
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert("Erro ao carregar dados: " + error.message);
        });
}

function saveClient() {
    const form = document.getElementById('clientForm');
    const formData = new FormData(form);
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const clientId = document.getElementById('clientId').value;
    
    let url;
    
    // VERIFICAÇÃO IMPORTANTE DA URL
    if (clientId) {
        // Se certifique que esta URL bate com o urls.py
        url = `/api/clients/${clientId}/update/`
    } else {
        url = "/api/clients/create/";
    }

    console.log(`Enviando para: ${url}`); // Ajuda a debugar

    fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
        body: formData
    })
    .then(response => {
        // Lemos como texto primeiro para ver o que veio (JSON ou HTML de erro)
        return response.text().then(text => {
            try {
                // Tenta converter para JSON
                const data = JSON.parse(text);
                
                if (!response.ok) {
                    // Se o status for 400 ou 500, tratamos como erro
                    const error = new Error(data.message || "Erro no servidor");
                    error.data = data;
                    throw error;
                }
                return data;
            } catch (e) {
                // SE CAIR AQUI, O ERRO É HTML
                console.error("O servidor não retornou JSON. Resposta recebida:", text);
                throw new Error(`Erro Fatal (Status ${response.status}): Verifique o console para ver o HTML retornado.`);
            }
        });
    })
    .then(data => {
        if (data.status === 'success') {
            closeClientModal();
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: "Sucesso!", text: data.message, icon: "success", timer: 1500, showConfirmButton: false
                }).then(() => window.location.reload());
            } else {
                window.location.reload();
            }
        }
    })
    .catch(error => {
        console.error('Erro detalhado:', error);
        if (error.data && error.data.errors) {
            showErrors(error.data.errors); // Mostra campos vermelhos
        } else {
            alert(error.message);
        }
    });
}

function deleteClient(clientId) {
    if (!confirm("Tem certeza que deseja excluir?")) return;

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const url = `/projects/api/clients/${clientId}/delete/`;

    fetch(url, { 
        method: 'POST', 
        headers: { 'X-CSRFToken': csrfToken }
    })
    .then(response => {
        if(response.ok) {
            window.location.reload();
        } else {
            alert("Erro ao excluir cliente.");
        }
    });
}

function performDelete(clientId) {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    fetch(`/projects/client/${clientId}/delete/`, { 
        method: 'POST', 
        headers: { 'X-CSRFToken': csrfToken }
    })
    .then(response => {
        if(response.ok) {
            window.location.reload();
        } else {
            alert("Erro ao excluir.");
        }
    });
}

// --- Helpers ---

function triggerUpload(inputId) {
    const el = document.getElementById(inputId);
    if(el) el.click();
}

function setVal(id, val) {
    const el = document.getElementById(id);
    if(el) el.value = val || '';
}

function setCheck(id, isChecked) {
    const el = document.getElementById(id);
    if(el) el.checked = isChecked;
}

function showErrors(errors) {
    clearErrors();
    for (const fieldName in errors) {
        const input = document.getElementById(`id_${fieldName}`);
        if (input) {
            input.classList.add('is-invalid'); // Classe do Bootstrap para borda vermelha
            // Tenta achar ou criar div de erro
            let errorDiv = input.nextElementSibling;
            if (!errorDiv || !errorDiv.classList.contains('invalid-feedback')) {
                errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback'; // Classe do Bootstrap para texto vermelho
                errorDiv.style.display = 'block'; // Força exibição
                input.parentNode.appendChild(errorDiv);
            }
            errorDiv.textContent = errors[fieldName][0];
        }
    }
}

function clearErrors() {
    document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    document.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
}

function setupInputMasks() {
    const cnpjInput = document.getElementById("id_cnpj");
    if (cnpjInput) {
        cnpjInput.addEventListener("input", function (e) {
            let x = e.target.value.replace(/\D/g, "").match(/(\d{0,2})(\d{0,3})(\d{0,3})(\d{0,4})(\d{0,2})/);
            e.target.value = !x[2] ? x[1] : x[1] + "." + x[2] + "." + x[3] + "/" + x[4] + (x[5] ? "-" + x[5] : "");
        });
    }
    const phoneInput = document.getElementById("id_celular_representante");
    if (phoneInput) {
        phoneInput.addEventListener("input", function (e) {
            let x = e.target.value.replace(/\D/g, "").match(/(\d{0,2})(\d{0,5})(\d{0,4})/);
            e.target.value = !x[2] ? x[1] : "(" + x[1] + ") " + x[2] + (x[3] ? "-" + x[3] : "");
        });
    }
}