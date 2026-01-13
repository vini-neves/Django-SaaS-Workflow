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