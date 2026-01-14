// Variável global para controlar o modal
let clientModalInstance = null;

let currentFileUrls = {
    'id_anexo_contrato': null,
    'id_manual_marca': null,
    'id_logo': null
};

let activeInputId = null;

document.addEventListener('DOMContentLoaded', function() {
    // 1. Configuração do Modal
    const modalElement = document.getElementById('clientModal');
    if (modalElement) {
        document.body.appendChild(modalElement);
        // Remove atributos que podem conflitar
        modalElement.removeAttribute('aria-modal');
        modalElement.removeAttribute('role');

        if (typeof bootstrap !== 'undefined') {
            clientModalInstance = new bootstrap.Modal(modalElement, {
                backdrop: 'static',
                keyboard: false
            });
        }
    }
    
    // 2. Inicializa Máscaras
    setupInputMasks();

    // 3. Garante que inputs de arquivo estejam ocultos
    document.querySelectorAll('input[type="file"]').forEach(input => {
        input.style.display = 'none';
        input.addEventListener('change', function() {
            updateFileName(this);
        });
    });
});

// =================================================================
// 1. FUNÇÕES DE MODAL (ABRIR / FECHAR)
// =================================================================

function openCreateModal() {
    const form = document.getElementById('clientForm');
    if(form) form.reset();
    
    // Reseta visual dos uploads (remove o verde e volta para cinza)
    resetUploadBoxes();

    // Limpa ID para garantir que é criação
    currentFileUrls = { 'id_anexo_contrato': null, 'id_manual_marca': null, 'id_logo': null };
    activeInputId = null;

    const idInput = document.getElementById('clientId');
    if(idInput) idInput.value = '';
    
    const title = document.getElementById('modalTitle');
    if(title) title.textContent = 'Cadastrar Novo Cliente';
    
    // Reseta checkboxes
    document.querySelectorAll('.social-toggle-list input[type="checkbox"]').forEach(el => el.checked = false);
    
    const activeCheck = document.getElementById('id_is_active');
    if(activeCheck) activeCheck.checked = true;

    clearErrors();

    if (clientModalInstance) clientModalInstance.show();
}

function closeClientModal() {
    if (clientModalInstance) {
        clientModalInstance.hide();
    } else {
        const modalEl = document.getElementById('clientModal');
        if(modalEl) {
            const modal = bootstrap.Modal.getInstance(modalEl);
            if(modal) modal.hide();
        }
    }
}

// =================================================================
// 2. FUNÇÕES DE UPLOAD (VISUAL)
// =================================================================

function triggerUpload(inputId) {
    activeInputId = inputId; // Guarda qual input foi clicado
    const url = currentFileUrls[inputId];

    // Se já tem URL salva (modo edição com arquivo existente), abre Preview
    if (url) {
        openPreviewModal(url, inputId);
    } else {
        // Se não tem arquivo, abre seletor nativo do sistema
        const input = document.getElementById(inputId);
        if(input) {
            input.click();
        } else {
            console.error("Input de arquivo não encontrado com ID: " + inputId);
        }
    }
}

function openPreviewModal(url, inputId) {
    const previewContent = document.getElementById('previewContent');
    const downloadBtn = document.getElementById('btnDownloadFile');
    const fileNameDisplay = document.getElementById('previewFileName');
    
    // Configura botão de download
    downloadBtn.href = url;
    
    // Tenta pegar nome do arquivo da URL
    const fileName = url.split('/').pop().split('?')[0];
    fileNameDisplay.innerText = decodeURIComponent(fileName);

    // Identifica se é Logo ou Documento baseado no ID ou extensão
    const isImage = inputId.includes('logo') || url.match(/\.(jpeg|jpg|gif|png|webp)$/i);

    if (isImage) {
        previewContent.innerHTML = `<img src="${url}" class="img-fluid rounded border" style="max-height: 200px; object-fit:contain;">`;
    } else {
        let iconClass = inputId.includes('contrato') ? 'fa-file-contract' : 'fa-book';
        previewContent.innerHTML = `
            <div style="font-size: 4rem; color: var(--c-primary); margin-bottom:10px;">
                <i class="fa-solid ${iconClass}"></i>
            </div>
        `;
    }

    // Abre o modal secundário
    const previewModal = new bootstrap.Modal(document.getElementById('filePreviewModal'));
    previewModal.show();
}

/**
 * [NOVO] Ação do botão "Substituir" dentro do modal de preview
 */
function replaceFile() {
    // 1. Fecha modal de preview
    const modalEl = document.getElementById('filePreviewModal');
    const modalInstance = bootstrap.Modal.getInstance(modalEl);
    if(modalInstance) modalInstance.hide();

    // 2. Aciona o input file oculto para selecionar novo arquivo
    if(activeInputId) {
        const input = document.getElementById(activeInputId);
        if(input) input.click();
    }
}

function updateFileName(input) {
    if (input.files && input.files[0]) {
        let uploadBox = input.previousElementSibling; // Assume estrutura: Box -> Input
        if (!uploadBox) uploadBox = document.getElementById('box_' + input.id.replace('id_', '')); // Fallback

        if (uploadBox) {
            uploadBox.style.borderColor = "#ffc107"; // Amarelo (Alterado/Novo)
            uploadBox.style.backgroundColor = "#fff9db"; 
            
            let textElement = uploadBox.querySelector('.upload-text');
            let iconElement = uploadBox.querySelector('.upload-icon');
            
            if(iconElement) iconElement.className = "fa-solid fa-check upload-icon";
            if(iconElement) iconElement.style.color = "#b18605";

            if(textElement) {
                textElement.innerHTML = `<strong>${input.files[0].name}</strong>`;
                textElement.style.color = "#b18605";
            }
        }
    }
}

function resetUploadBoxes() {
    // IDs dos inputs que mapeamos
    ['id_anexo_contrato', 'id_manual_marca', 'id_logo'].forEach(id => {
        const input = document.getElementById(id);
        if(!input) return;
        
        let box = input.previousElementSibling;
        if(!box) box = document.getElementById('box_' + id.replace('id_', ''));

        if(box) {
            box.style.borderColor = "#ccc"; 
            box.style.backgroundColor = "#f9fafb";
            box.classList.remove('has-file'); // Remove classe se existir

            // Restaura ícones originais baseado no ID
            let iconClass = 'fa-file';
            if(id.includes('contrato')) iconClass = 'fa-file-contract';
            else if(id.includes('manual')) iconClass = 'fa-book';
            else if(id.includes('logo')) iconClass = 'fa-image';

            box.innerHTML = `
                <i class="fa-solid ${iconClass} upload-icon"></i>
                <div class="upload-text">Enviar</div>
            `;
        }
    });
}

function updateBoxToViewMode(inputId) {
    const input = document.getElementById(inputId);
    if(!input) return;
    
    let box = input.previousElementSibling;
    if(!box) box = document.getElementById('box_' + inputId.replace('id_', ''));

    if(box) {
        box.style.borderColor = "#28a745"; // Verde
        box.style.backgroundColor = "#f0fff4";
        box.innerHTML = `
            <i class="fa-solid fa-eye upload-icon" style="color: #28a745;"></i>
            <div class="upload-text" style="color: #28a745; font-weight:bold;">Ver Arquivo</div>
        `;
    }
}

// =================================================================
// 3. CRUD (SALVAR, EDITAR, EXCLUIR)
// =================================================================

function saveClient() {
    const form = document.getElementById('clientForm');
    const formData = new FormData(form); // Pega arquivos automaticamente
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const clientId = document.getElementById('clientId').value;
    
    // Define se é CREATE ou UPDATE baseado no ID
    let url;
    if (clientId) {
        url = `/api/clients/${clientId}/update/`; // Verifique se sua URL é essa mesma
    } else {
        url = "/api/clients/create/";
    }

    // Feedback visual no botão
    const btnSave = document.querySelector('.btn-save');
    const originalText = btnSave.innerHTML;
    btnSave.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Salvando...';
    btnSave.disabled = true;

    fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
        body: formData 
    })
    .then(response => {
        return response.text().then(text => {
            try {
                return JSON.parse(text);
            } catch (e) {
                console.error("Resposta não é JSON:", text);
                throw new Error("Erro no servidor (resposta inválida)");
            }
        });
    })
    .then(data => {
        if (data.success || data.status === 'success') {
            closeClientModal();
            // Se tiver SweetAlert usa ele, senão reload normal
            if (typeof Swal !== 'undefined') {
                Swal.fire({
                    title: "Sucesso!", text: data.message || "Salvo com sucesso!", icon: "success", timer: 1500, showConfirmButton: false
                }).then(() => window.location.reload());
            } else {
                window.location.reload();
            }
        } else {
            if (data.errors) {
                showErrors(data.errors);
            } else {
                alert("Erro: " + (data.message || "Erro desconhecido"));
            }
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert("Erro na conexão com o servidor.");
    })
    .finally(() => {
        btnSave.innerHTML = originalText;
        btnSave.disabled = false;
    });
}

// --- FUNÇÃO EDITAR (RESTAURADA) ---
function editClient(buttonElement) {
    const button = buttonElement.closest('button');
    const url = button.dataset.url; // URL vem do data-url no HTML

    // Limpa o form antes de preencher
    resetUploadBoxes();
    clearErrors();

    currentFileUrls = { 'id_anexo_contrato': null, 'id_manual_marca': null, 'id_logo': null };

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error("Erro ao buscar dados do cliente");
            return response.json();
        })
        .then(data => {
            // Preenche ID
            const idInput = document.getElementById('clientId');
            if(idInput) idInput.value = data.id;
            
            // Preenche Campos de Texto
            setVal('id_name', data.name);
            setVal('id_cnpj', data.cnpj);
            setVal('id_nome_representante', data.nome_representante);
            setVal('id_email_representante', data.email_representante);
            setVal('id_celular_representante', data.celular_representante);
            setVal('id_data_inicio_contrato', data.data_inicio_contrato);
            setVal('id_data_finalizacao_contrato', data.data_finalizacao_contrato);
            
            // Preenche Checkbox Ativo
            const activeCheck = document.getElementById('id_is_active');
            if(activeCheck) activeCheck.checked = data.is_active;

            // Preenche Redes Sociais
            const platforms = data.connected_platforms || [];
            setCheck('toggleInstagram', platforms.includes('instagram'));
            setCheck('toggleLinkedin', platforms.includes('linkedin-oauth2'));
            setCheck('toggleTiktok', platforms.includes('tiktok'));
            setCheck('toggleFacebook', platforms.includes('facebook'));
            
            if(data.anexo_contrato_url) {
                currentFileUrls['id_anexo_contrato'] = data.anexo_contrato_url;
                updateBoxToViewMode('id_anexo_contrato');
            }
            if(data.manual_marca_url) {
                currentFileUrls['id_manual_marca'] = data.manual_marca_url;
                updateBoxToViewMode('id_manual_marca');
            }
            if(data.logo_url) {
                currentFileUrls['id_logo'] = data.logo_url;
                updateBoxToViewMode('id_logo');
            }

            // Muda título do Modal
            const title = document.getElementById('modalTitle');
            if(title) title.textContent = 'Editar Cliente';
            
            // Abre o Modal
            if (clientModalInstance) {
                clientModalInstance.show();
            } else {
                // Tenta recriar se não existir
                const modalEl = document.getElementById('clientModal');
                clientModalInstance = new bootstrap.Modal(modalEl);
                clientModalInstance.show();
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert("Erro ao carregar dados: " + error.message);
        });
}

// --- FUNÇÕES DELETAR (RESTAURADAS) ---

function deleteClient(clientId) {
    if (!confirm("Tem certeza que deseja excluir este cliente?")) return;

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const url = `/projects/api/clients/${clientId}/delete/`; // Ajuste conforme sua rota

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

// Mantendo a performDelete caso você use em outro lugar
function performDelete(clientId) {
   deleteClient(clientId);
}


// =================================================================
// 4. HELPERS (MÁSCARAS, ERROS, ETC)
// =================================================================

function setVal(id, val) {
    const el = document.getElementById(id);
    if(el) el.value = val || '';
}

function setCheck(id, isChecked) {
    const el = document.getElementById(id);
    if(el) el.checked = !!isChecked;
}

function clearErrors() {
    document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    document.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
}

function showErrors(errors) {
    clearErrors();
    for (const fieldName in errors) {
        // Django usa prefixo id_ no HTML, mas retorna erro com nome simples
        const input = document.getElementById(`id_${fieldName}`);
        if (input) {
            input.classList.add('is-invalid');
            
            let errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback';
            errorDiv.style.display = 'block';
            errorDiv.textContent = errors[fieldName][0];
            
            // Se for input de arquivo, coloca o erro depois da caixa visual
            if(input.type === 'file') {
                // input.previousElementSibling é a .upload-box
                if(input.previousElementSibling) {
                    input.previousElementSibling.after(errorDiv);
                } else {
                    input.parentNode.appendChild(errorDiv);
                }
            } else {
                input.parentNode.appendChild(errorDiv);
            }
        }
    }
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