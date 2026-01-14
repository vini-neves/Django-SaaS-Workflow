/* static/js/media_manager.js */

document.addEventListener("DOMContentLoaded", function () {
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
});

// Função de Delete com SweetAlert
function confirmDelete(event, title, text, form) {
    event.stopPropagation();
    event.preventDefault();

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
            form.submit();
        }
    });
}

// Função de pausa (Delay)
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function uploadInBatch(inputElement) {
    console.log("--> Iniciando uploadInBatch..."); // DEBUG

    // 1. Verifica bibliotecas
    if (typeof Swal === 'undefined') {
        alert("ERRO CRÍTICO: SweetAlert não carregado!");
        return;
    }

    const files = Array.from(inputElement.files);
    const total = files.length;
    console.log(`--> Arquivos selecionados: ${total}`); // DEBUG

    if (total === 0) return;

    // 2. Prepara os dados
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

    console.log("--> Abrindo SweetAlert..."); // DEBUG

    // 3. Abre o Modal (SEM AWAIT para não travar a execução)
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

            <div id="swal-log-container" style="
                height: 150px; 
                overflow-y: auto; 
                background-color: #1f2937; 
                color: #f3f4f6; 
                text-align: left; 
                padding: 10px; 
                border-radius: 6px; 
                font-family: monospace; 
                font-size: 0.8rem;
                border: 1px solid #374151;
            ">
                <div style="color: #9ca3af;">> Iniciando fila de upload...</div>
            </div>
        `,
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        width: '600px',
        didOpen: () => {
            Swal.showLoading();
        }
    });

    // Pausa para renderizar o DOM
    await sleep(200);

    // Referências aos elementos
    const progressBar = document.getElementById('swal-progress-bar');
    const progressText = document.getElementById('swal-progress-text');
    const percentText = document.getElementById('swal-percent-text');
    const logContainer = document.getElementById('swal-log-container');

    if (!progressBar) console.error("--> ERRO: Não consegui achar a barra de progresso no HTML do SweetAlert!");

    // Função interna de log
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

    console.log("--> Iniciando Loop..."); // DEBUG

    // 4. Loop de Upload
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

        // Atualiza Barra
        const currentStep = index + 1;
        const percent = Math.round((currentStep / total) * 100);
        
        if (progressBar) progressBar.style.width = `${percent}%`;
        if (progressText) progressText.innerText = `${currentStep}/${total} arquivos`;
        if (percentText) percentText.innerText = `${percent}%`;
    }

    // 5. Finalização
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