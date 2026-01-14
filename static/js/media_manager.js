/* static/js/media_manager.js */

document.addEventListener("DOMContentLoaded", function () {
    console.log("--> Media Manager JS carregado!"); // Debug para confirmar carregamento

    // 1. Inicializa ícones Feather
    if (typeof feather !== 'undefined') {
        feather.replace();
    }

    // 2. Funções para abrir/fechar modais
    window.openModal = function (modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'flex';
    }

    window.closeModal = function (element) {
        const modal = element.closest('.modal');
        if (modal) modal.style.display = 'none';
    }

    // Fechar ao clicar fora do modal
    window.onclick = function (event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = "none";
        }
    }

    // 3. VALIDAÇÃO DO DOWNLOAD EM LOTE
    // Verifica se o formulário existe na página antes de adicionar o evento
    const batchForm = document.getElementById('batchForm');
    const tokenInput = document.getElementById('downloadToken'); // Referência ao input

    if (batchForm) {
        batchForm.addEventListener('submit', function(event) {
            const checked = document.querySelectorAll('.file-select-checkbox:checked');
            
            if (checked.length === 0) {
                event.preventDefault();
                if (typeof Swal !== 'undefined') {
                    Swal.fire('Atenção', 'Selecione pelo menos um arquivo.', 'warning');
                } else {
                    alert('Selecione pelo menos um arquivo.');
                }
                return;
            }

            // --- INÍCIO DA LÓGICA DE PROGRESSO ---
            
            // 1. Gera um Token Único (Data atual em milissegundos)
            const token = new Date().getTime();
            if(tokenInput) tokenInput.value = token;

            // 2. Mostra o SweetAlert com Barra de Progresso
            let progress = 0;
            Swal.fire({
                title: 'Gerando Arquivo ZIP...',
                html: `
                    <div style="text-align: left; margin-bottom: 5px; color: #555;">Compactando ${checked.length} arquivos</div>
                    <div style="width: 100%; background-color: #e9ecef; border-radius: 4px; height: 15px; overflow: hidden;">
                        <div id="zip-progress-bar" style="width: 0%; height: 100%; background-color: var(--primary-color, #2563eb); transition: width 0.2s;"></div>
                    </div>
                    <div style="font-size: 0.8rem; margin-top: 5px; color: #888;">Aguarde, o download iniciará automaticamente.</div>
                `,
                allowOutsideClick: false,
                allowEscapeKey: false,
                showConfirmButton: false,
                didOpen: () => {
                    Swal.showLoading();
                }
            });

            // 3. Timer para Simular Progresso e Checar Cookie
            const progressBar = document.getElementById('zip-progress-bar');
            
            const downloadTimer = setInterval(() => {
                // A. Simula progresso (vai rápido até 30%, depois devagar até 90%)
                if (progress < 30) progress += 2;
                else if (progress < 90) progress += 0.5;
                
                if (progressBar) progressBar.style.width = progress + '%';

                // B. Verifica se o Cookie chegou
                // O servidor cria um cookie "download_token=123456"
                if (document.cookie.includes('download_token=' + token)) {
                    
                    // SUCESSO! O servidor respondeu.
                    clearInterval(downloadTimer);
                    
                    if (progressBar) progressBar.style.width = '100%';

                    // Limpa o cookie para não atrapalhar o próximo
                    document.cookie = 'download_token=; Max-Age=-99999999;';

                    // Fecha o alerta após um breve delay visual
                    setTimeout(() => {
                        Swal.close();
                        
                        // Opcional: Toast de sucesso
                        const Toast = Swal.mixin({
                            toast: true, position: 'top-end', showConfirmButton: false, timer: 3000
                        });
                        Toast.fire({ icon: 'success', title: 'Download iniciado!' });
                    }, 500);
                }
            }, 100); // Roda a cada 100ms

        });
    }
});

// ==============================================================
// FUNÇÕES GLOBAIS (UPLOAD, DELETE, SELEÇÃO)
// Elas precisam estar fora do DOMContentLoaded para o HTML acessá-las
// ==============================================================

// Função de Delete com SweetAlert
function confirmDelete(event, title, text, element) {
    event.stopPropagation();
    event.preventDefault(); // Impede o link de abrir ou o form de enviar imediatamente

    Swal.fire({
        title: title,
        text: text,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#3085d6',
        confirmButtonText: 'Sim, excluir!',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            
            // VERIFICAÇÃO INTELIGENTE
            if (element.tagName === 'FORM') {
                // Se for um formulário (caso das Pastas), envia o form
                element.submit();
            } else if (element.tagName === 'A') {
                // Se for um link (caso dos Arquivos), redireciona para a URL
                window.location.href = element.href;
            } else {
                console.error("Elemento desconhecido para exclusão:", element);
            }
            
        }
    });
}

// Função de pausa (Delay)
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Função de Upload em Lote
async function uploadInBatch(inputElement) {
    console.log("--> Iniciando uploadInBatch...");

    if (typeof Swal === 'undefined') {
        alert("ERRO CRÍTICO: SweetAlert não carregado!");
        return;
    }

    const files = Array.from(inputElement.files);
    const total = files.length;
    console.log(`--> Arquivos selecionados para upload: ${total}`);

    if (total === 0) return;

    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    const clientIdInput = document.getElementById('clientId');
    const folderIdInput = document.getElementById('folderId');

    if (!csrfInput || !clientIdInput) {
        Swal.fire('Erro', 'Dados do formulário (ID ou Token) não encontrados no HTML.', 'error');
        return;
    }

    const csrfToken = csrfInput.value;
    const clientId = clientIdInput.value;
    const folderId = folderIdInput ? folderIdInput.value : '';

    Swal.fire({
        title: 'Gerenciador de Upload',
        html: `
            <div style="text-align:left; margin-bottom:5px; font-weight:bold; color:#333;">Progresso Total:</div>
            <div style="width: 100%; background-color: #e9ecef; border-radius: 8px; height: 20px; margin-bottom: 20px; overflow: hidden; border: 1px solid #ced4da;">
                <div id="swal-progress-bar" style="width: 0%; height: 100%; background-color: var(--primary-color); transition: width 0.3s ease;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom:10px; font-size:0.9rem; color:#555;">
                <span id="swal-progress-text">0/${total} arquivos</span>
                <span id="swal-percent-text">0%</span>
            </div>
            <div id="swal-log-container" style="height: 150px; overflow-y: auto; background-color: #1f2937; color: #f3f4f6; text-align: left; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 0.8rem; border: 1px solid #374151;">
                <div style="color: #9ca3af;">> Iniciando fila de upload...</div>
            </div>
        `,
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        width: '600px',
        didOpen: () => { Swal.showLoading(); }
    });

    await sleep(200);

    const progressBar = document.getElementById('swal-progress-bar');
    const progressText = document.getElementById('swal-progress-text');
    const percentText = document.getElementById('swal-percent-text');
    const logContainer = document.getElementById('swal-log-container');

    const addLog = (message, type = 'info') => {
        if (!logContainer) return;
        const div = document.createElement('div');
        div.style.marginTop = '4px';
        div.style.borderBottom = '1px solid #374151';
        if (type === 'success') div.style.color = '#4ade80';
        else if (type === 'error') div.style.color = '#f87171';
        else div.style.color = '#d1d5db';
        div.innerText = `> ${message}`;
        logContainer.appendChild(div);
        logContainer.scrollTop = logContainer.scrollHeight;
    };

    let successCount = 0;
    let errorCount = 0;

    for (const [index, file] of files.entries()) {
        const formData = new FormData();
        formData.append('foto', file);
        formData.append('client_id', clientId);
        if (folderId) formData.append('folder_id', folderId);

        addLog(`Enviando: ${file.name}...`, 'info');

        try {
            if (index > 0) await sleep(200);

            const response = await fetch('/api/upload/photo/', {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken },
                body: formData
            });

            const data = await response.json().catch(() => ({}));

            if (response.ok && data.status === 'success') {
                successCount++;
                addLog(`✓ Sucesso: ${file.name}`, 'success');
            } else {
                errorCount++;
                addLog(`✗ Falha: ${file.name} (${data.message || response.status})`, 'error');
            }
        } catch (err) {
            errorCount++;
            console.error(err);
            addLog(`! Erro Rede: ${file.name}`, 'error');
        }

        const currentStep = index + 1;
        const percent = Math.round((currentStep / total) * 100);
        
        if (progressBar) progressBar.style.width = `${percent}%`;
        if (progressText) progressText.innerText = `${currentStep}/${total} arquivos`;
        if (percentText) percentText.innerText = `${percent}%`;
    }

    await sleep(500);
    
    let iconType = 'success';
    let titleText = 'Upload Finalizado';
    let confirmBtnColor = 'var(--primary-color)';

    if (errorCount > 0) {
        iconType = successCount === 0 ? 'error' : 'warning';
        titleText = errorCount > 0 ? 'Finalizado com Erros' : 'Falha';
        confirmBtnColor = errorCount > 0 ? '#d97706' : '#dc2626';
    }

    Swal.fire({
        title: titleText,
        html: `Processo concluído!<br><br><b style="color:#16a34a">✅ Sucesso: ${successCount}</b><br><b style="color:#dc2626">❌ Falhas: ${errorCount}</b>`,
        icon: iconType,
        confirmButtonColor: confirmBtnColor,
        confirmButtonText: 'OK'
    }).then(() => {
        location.reload();
    });
}

// 4. Lógica de Seleção (Checkboxes e Barra Flutuante)
function toggleSelection(id, event) {
    // Se clicar no checkbox direto, o navegador já alterna o estado.
    // Se clicar no card, nós invertemos manualmente.
    const checkbox = document.getElementById('check-' + id);
    const card = document.getElementById('card-' + id);

    if (!checkbox || !card) return;

    if (event.target !== checkbox) {
        checkbox.checked = !checkbox.checked;
    }

    // Atualiza visual
    if (checkbox.checked) {
        card.classList.add('selected');
    } else {
        card.classList.remove('selected');
    }
    updateSelectionBar();
}

function updateSelectionBar() {
    const checked = document.querySelectorAll('.file-select-checkbox:checked');
    const bar = document.getElementById('selectionBar');
    const countSpan = document.getElementById('selectionCount');
    
    if (!bar) return;

    if (checked.length > 0) {
        bar.classList.add('active');
        if(countSpan) countSpan.innerText = `${checked.length} selecionados`;
    } else {
        bar.classList.remove('active');
    }
}

function clearSelection() {
    document.querySelectorAll('.file-select-checkbox').forEach(cb => {
        cb.checked = false;
        const card = document.getElementById('card-' + cb.value);
        if (card) card.classList.remove('selected');
    });
    updateSelectionBar();
}