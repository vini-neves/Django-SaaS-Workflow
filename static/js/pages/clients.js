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
    // Limpa o formulário
    const form = document.getElementById('clientForm');
    if(form) form.reset();
    
    // Reseta campos ocultos e títulos
    const idInput = document.getElementById('clientId');
    if(idInput) idInput.value = '';
    
    const title = document.getElementById('modalTitle');
    if(title) title.textContent = 'Cadastrar Novo Cliente';
    
    // Reseta os toggles visuais
    document.querySelectorAll('.social-toggle-list input[type="checkbox"]').forEach(el => el.checked = false);
    
    // Padrão Ativo
    const activeCheck = document.getElementById('id_is_active');
    if(activeCheck) activeCheck.checked = true;

    // Remove erros visuais anteriores
    clearErrors();

    // Abre o modal
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
        // Fallback de emergência: remove classes manualmente se o Bootstrap falhar
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

function editClient(clientId) {
    const url = `/projects/api/clients/${clientId}/`; 

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error("Erro na rede ou URL não encontrada");
            return response.json();
        })
        .then(data => {
            // Preenche ID
            document.getElementById('clientId').value = data.id;
            
            // Preenche inputs (Função auxiliar setVal)
            setVal('id_name', data.name);
            setVal('id_cnpj', data.cnpj);
            setVal('id_nome_representante', data.nome_representante);
            setVal('id_email_representante', data.email_representante);
            setVal('id_data_inicio_contrato', data.data_inicio_contrato);
            setVal('id_data_finalizacao_contrato', data.data_finalizacao_contrato);
            
            // Checkbox Status
            const activeCheck = document.getElementById('id_is_active');
            if(activeCheck) activeCheck.checked = data.is_active;

            // Toggles Sociais
            const platforms = data.connected_platforms || [];
            setCheck('toggleInstagram', platforms.includes('instagram'));
            setCheck('toggleLinkedin', platforms.includes('linkedin'));
            setCheck('toggleTiktok', platforms.includes('tiktok'));
            setCheck('toggleFacebook', platforms.includes('facebook'));

            // Muda título e abre
            const title = document.getElementById('modalTitle');
            if(title) title.textContent = 'Editar Cliente';
            
            clearErrors();
            
            if (clientModalInstance) clientModalInstance.show();
        })
        .catch(error => {
            console.error('Erro:', error);
            // Fallback: Se não tiver SweetAlert, usa alert normal
            if (typeof Swal !== 'undefined') {
                Swal.fire("Erro", "Não foi possível carregar os dados.", "error");
            } else {
                alert("Erro ao carregar dados do cliente.");
            }
        });
}

function saveClient() {
    const form = document.getElementById('clientForm');
    const formData = new FormData(form);
    
    // Tenta pegar o token de várias formas
    let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    const url = "/projects/api/clients/save/"; 

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            closeClientModal();
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: "Sucesso!",
                    text: data.message,
                    icon: "success",
                    timer: 1500,
                    showConfirmButton: false
                }).then(() => window.location.reload());
            } else {
                window.location.reload();
            }
        } else {
            if (typeof Swal !== 'undefined') {
                Swal.fire("Atenção", "Verifique os campos em vermelho.", "warning");
            } else {
                alert("Verifique os campos.");
            }
            showErrors(data.errors);
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert("Erro de conexão ao salvar.");
    });
}

function deleteClient(clientId) {
    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Tem certeza?',
            text: "Não será possível reverter!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#ef4444',
            cancelButtonColor: '#6b7280',
            confirmButtonText: 'Sim, excluir!',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                performDelete(clientId);
            }
        });
    } else {
        if(confirm("Tem certeza que deseja excluir?")) {
            performDelete(clientId);
        }
    }
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