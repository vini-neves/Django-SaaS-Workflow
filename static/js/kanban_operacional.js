// static/js/kanban_operational.js

document.addEventListener('DOMContentLoaded', () => {
    
    // --- ELEMENTOS DO DOM ---
    const addOpBtn = document.getElementById('add-operational-btn');
    const addOpModal = document.getElementById('add-op-modal');
    const addOpForm = document.getElementById('add-op-form');
    // Seleciona o botão de fechar ESPECÍFICO deste modal
    const closeOpModalBtn = addOpModal ? addOpModal.querySelector('.close-button') : null;

    // --- FUNÇÕES DE CONTROLE DE MODAL ---

    function openModal() {
        if(addOpModal) {
            addOpModal.style.display = 'flex';
            document.body.classList.add('modal-open'); // Opcional: para travar scroll do fundo
        }
    }

    function closeModal() {
        if(addOpModal) {
            addOpModal.style.display = 'none';
            document.body.classList.remove('modal-open');
            if(addOpForm) addOpForm.reset();
        }
    }

    // --- EVENT LISTENERS ---

    // 1. Abrir
    if (addOpBtn) {
        addOpBtn.addEventListener('click', (e) => {
            e.preventDefault(); // Previne comportamento padrão se for link
            openModal();
        });
    }

    // 2. Fechar (Botão X)
    if (closeOpModalBtn) {
        closeOpModalBtn.addEventListener('click', closeModal);
    }

    // 3. Fechar (Clicar fora)
    window.addEventListener('click', (e) => {
        if (e.target === addOpModal) {
            closeModal();
        }
    });

    // --- SUBMISSÃO DO FORMULÁRIO (AJAX) ---
    if (addOpForm) {
        addOpForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitBtn = addOpForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerText;
            submitBtn.innerText = "Criando...";
            submitBtn.disabled = true;

            const formData = new FormData(addOpForm);
            // Adiciona o tipo de kanban manualmente se não estiver no form
            formData.append('kanban_type', 'operational'); 

            try {
                const response = await fetch(ADD_OP_URL, { // ADD_OP_URL vem do HTML
                    method: 'POST',
                    headers: { 'X-CSRFToken': CSRF_TOKEN },
                    body: formData
                });

                const result = await response.json();

                if (response.ok) {
                    if (typeof Swal !== 'undefined') {
                        Swal.fire('Sucesso!', 'Demanda iniciada.', 'success').then(() => {
                            location.reload(); // Recarrega para ver o card novo
                        });
                    } else {
                        alert("Sucesso!");
                        location.reload();
                    }
                    closeModal();
                } else {
                    const msg = result.message || 'Erro ao criar demanda.';
                    if (typeof Swal !== 'undefined') Swal.fire('Erro', msg, 'error');
                    else alert(msg);
                }
            } catch (error) {
                console.error(error);
                alert('Erro de conexão.');
            } finally {
                submitBtn.innerText = originalText;
                submitBtn.disabled = false;
            }
        });
    }
    
    // Inicializa ícones se necessário
    if (typeof feather !== 'undefined') feather.replace();
});