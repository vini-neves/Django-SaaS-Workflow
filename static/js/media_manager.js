/* static/js/media_manager.js */

document.addEventListener("DOMContentLoaded", function() {
    // 1. Inicializa ícones Feather
    if (typeof feather !== 'undefined') {
        feather.replace();
    }

    // 2. Funções para abrir/fechar modais
    window.openModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'flex';
    }

    window.closeModal = function(element) {
        const modal = element.closest('.modal');
        if (modal) modal.style.display = 'none';
    }

    // Fechar ao clicar fora do modal
    window.onclick = function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = "none";
        }
    }
});

/* static/js/media_manager.js */

function confirmDelete(event, title, text) {
    // 1. Impede que o clique propague para o Card (não abre a pasta)
    event.stopPropagation();
    
    // 2. Impede o envio imediato do formulário
    event.preventDefault();

    // 3. Identifica o formulário que contém o botão clicado
    const button = event.currentTarget;
    const form = button.closest('form');

    // 4. Dispara o SweetAlert
    Swal.fire({
        title: title,
        text: text,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444', // Vermelho
        cancelButtonColor: '#6b7280', // Cinza
        confirmButtonText: 'Sim, excluir!',
        cancelButtonText: 'Cancelar',
        reverseButtons: true // Botão de cancelar na esquerda (opcional)
    }).then((result) => {
        if (result.isConfirmed) {
            // 5. Se o usuário confirmou, envia o formulário manualmente
            form.submit();
        }
    });
}
async function uploadInBatch(inputElement) {
    // 1. Verificação de Segurança da Biblioteca
    if (typeof Swal === 'undefined') {
        alert("ERRO: A biblioteca SweetAlert2 não foi carregada no HTML.");
        return;
    }

    const files = Array.from(inputElement.files); // Garante que é um Array
    const total = files.length;
    
    if (total === 0) return;

    // 2. Abre o Alerta de Progresso
    Swal.fire({
        title: 'Iniciando Upload...',
        html: `Preparando fila de <b>${total}</b> arquivos.`,
        allowOutsideClick: false,
        allowEscapeKey: false,
        showConfirmButton: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });

    // Pega os tokens necessários
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    const clientIdInput = document.getElementById('clientId');

    if (!csrfInput || !clientIdInput) {
        Swal.fire('Erro', 'Não foi possível encontrar o Token ou o ID do Cliente.', 'error');
        return;
    }

    const csrfToken = csrfInput.value;
    const clientId = clientIdInput.value;

    let successCount = 0;
    let errorCount = 0;

    // 3. O LOOP MÁGICO (Um por um)
    // Usamos 'for...of' porque ele respeita o 'await'. 
    // Se usar 'forEach', ele tenta enviar tudo de uma vez e trava no arquivo 6.
    for (const [index, file] of files.entries()) {
        
        // Atualiza a mensagem na tela
        const msg = `Enviando <b>${index + 1}</b> de <b>${total}</b>...<br><small style="color:#666">${file.name}</small>`;
        if(Swal.getHtmlContainer()) Swal.getHtmlContainer().innerHTML = msg;

        const formData = new FormData();
        formData.append('foto', file); // Nome do campo esperado no Django
        formData.append('client_id', clientId);

        try {
            // AWAIT é o segredo: O código PARA aqui e espera o upload terminar antes de ir pro próximo
            const response = await fetch('/api/upload/photo/', { 
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken },
                body: formData
            });

            if (response.ok) {
                successCount++;
            } else {
                console.error(`Erro servidor no arquivo ${file.name}`);
                errorCount++;
            }
        } catch (err) {
            console.error(`Erro de rede no arquivo ${file.name}`, err);
            errorCount++;
        }
    }

    // 4. Relatório Final
    let iconType = 'success';
    let titleText = 'Finalizado!';
    
    if (errorCount > 0) {
        iconType = successCount > 0 ? 'warning' : 'error';
        titleText = 'Atenção no Resultado';
    }

    Swal.fire({
        title: titleText,
        html: `
            Processo finalizado.<br>
            <b style="color:var(--c-green)">Sucesso: ${successCount}</b><br>
            <b style="color:var(--c-red)">Falhas: ${errorCount}</b>
        `,
        icon: iconType,
        confirmButtonText: 'OK'
    }).then(() => {
        location.reload();
    });
}