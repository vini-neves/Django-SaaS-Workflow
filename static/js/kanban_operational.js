// static/js/kanban_operational.js

document.addEventListener('DOMContentLoaded', () => {
    console.log("--> Kanban Operacional Iniciado");

    // --- ELEMENTOS ---
    const columns = document.querySelectorAll('.kanban-column');
    
    // Modais
    const detailsModal = document.getElementById('task-details-modal');
    const detailsContent = document.getElementById('task-details-content');
    const closeDetailsBtn = detailsModal ? detailsModal.querySelector('.close-button') : null;

    let draggedCard = null;

    // --- 1. INICIALIZAÇÃO (Desenhar os Cards) ---
    function initializeKanban() {
        // KANBAN_INITIAL_DATA vem do HTML
        if (typeof KANBAN_INITIAL_DATA === 'undefined') {
            console.error("ERRO: Dados do Kanban não encontrados.");
            return;
        }

        for (const status in KANBAN_INITIAL_DATA) {
            const columnCards = document.querySelector(`#column-${status} .column-cards`);
            if (columnCards) {
                columnCards.innerHTML = ''; // Limpa antes de desenhar
                KANBAN_INITIAL_DATA[status].forEach(task => {
                    const card = createTaskCard(task);
                    columnCards.appendChild(card);
                });
            }
        }
        updateTaskCounts();
    }

    // --- 2. CRIAÇÃO DO CARD (Com Eventos) ---
    function createTaskCard(task) {
        const card = document.createElement('div');
        card.classList.add('kanban-card');
        card.setAttribute('draggable', 'true'); // VITAL PARA ARRASTAR
        card.dataset.taskId = task.id;
        card.dataset.status = task.status;

        // Conteúdo do Card
        let footerHtml = `<span class="project-tag">${task.project_name || 'Sem Projeto'}</span>`;
        
        // Ícones extras (Avatar, Imagem)
        let iconsHtml = '<div style="display:flex; gap:5px;">';
        if (task.social_post_id) {
            iconsHtml += `<i data-feather="image" style="width:14px; color:#666"></i>`;
        }
        if (task.assigned_to_initials) {
            iconsHtml += `<div class="card-assignee-avatar" title="${task.assigned_to}">${task.assigned_to_initials}</div>`;
        }
        iconsHtml += '</div>';

        card.innerHTML = `
            <h4>${task.title}</h4>
            <div class="card-footer" style="display:flex; justify-content:space-between; align-items:center; margin-top:10px;">
                ${footerHtml}
                ${iconsHtml}
            </div>
        `;

        // --- EVENTOS DE ARRASTAR (DRAG & DROP) ---
        card.addEventListener('dragstart', (e) => {
            draggedCard = card;
            setTimeout(() => card.classList.add('dragging'), 0);
        });

        card.addEventListener('dragend', () => {
            if (draggedCard) draggedCard.classList.remove('dragging');
            draggedCard = null;
        });

        // --- EVENTO DE CLIQUE (ABRIR DETALHES) ---
        card.addEventListener('click', () => {
            openTaskDetails(task.id);
        });

        return card;
    }

    // --- 3. LÓGICA DE DROP NAS COLUNAS ---
    columns.forEach(column => {
        column.addEventListener('dragover', (e) => {
            e.preventDefault(); // Permite o drop (VITAL)
            const afterElement = getDragAfterElement(column.querySelector('.column-cards'), e.clientY);
            const draggable = document.querySelector('.dragging');
            
            if (draggable) {
                const container = column.querySelector('.column-cards');
                if (afterElement == null) {
                    container.appendChild(draggable);
                } else {
                    container.insertBefore(draggable, afterElement);
                }
            }
        });

        column.addEventListener('drop', (e) => {
            if (draggedCard) {
                const newStatus = column.dataset.status;
                const taskId = draggedCard.dataset.taskId;
                
                // Só salva se mudou de coluna
                if (draggedCard.dataset.status !== newStatus) {
                    draggedCard.dataset.status = newStatus;
                    saveTaskChanges(taskId, newStatus, column.querySelector('.column-cards'));
                }
            }
        });
    });

    // --- 4. FUNÇÕES AUXILIARES ---

    function getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.kanban-card:not(.dragging)')];

        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    async function saveTaskChanges(taskId, newStatus, columnElement) {
        // Pega a nova ordem dos IDs na coluna
        const newOrderList = Array.from(columnElement.querySelectorAll('.kanban-card'))
                                .map(card => card.dataset.taskId);
        
        try {
            const response = await fetch(KANBAN_UPDATE_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: JSON.stringify({
                    taskId: taskId,
                    newStatus: newStatus,
                    newOrderList: newOrderList
                })
            });
            
            if (!response.ok) console.error("Erro ao salvar mudança no servidor.");
            
            updateTaskCounts();

        } catch (error) {
            console.error('Erro de rede:', error);
        }
    }

    function updateTaskCounts() {
        columns.forEach(column => {
            const count = column.querySelector('.column-cards').children.length;
            const badge = column.querySelector('.task-count');
            if(badge) badge.textContent = count;
        });
    }

    // --- 5. DETALHES DA TAREFA ---
    async function openTaskDetails(taskId) {
        try {
            // Usa a URL base + ID + '/details/'
            const url = `${GET_TASK_DETAILS_URL_BASE}${taskId}/details/`;
            console.log("Buscando detalhes em:", url);

            const response = await fetch(url);
            if (!response.ok) throw new Error("Erro na API");

            const task = await response.json();

            // Monta o HTML do modal
            detailsContent.innerHTML = `
                <h2 style="color:var(--primary-color); margin-top:0;">${task.title}</h2>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:15px; margin-bottom:20px;">
                    <div><strong>Status:</strong> ${task.status}</div>
                    <div><strong>Projeto:</strong> ${task.project_name}</div>
                    <div><strong>Atribuído a:</strong> ${task.assigned_to}</div>
                    <div><strong>Data:</strong> ${task.created_at}</div>
                </div>
                <div style="background:#f9f9f9; padding:15px; border-radius:5px;">
                    <strong>Descrição:</strong>
                    <p style="white-space: pre-wrap;">${task.description}</p>
                </div>
                ${task.social_post_id ? `<div style="margin-top:20px;"><a href="#" class="form-button" style="display:inline-block; text-align:center;">Ver Postagem</a></div>` : ''}
            `;

            detailsModal.style.display = 'flex';

        } catch (error) {
            console.error(error);
            alert("Não foi possível carregar os detalhes.");
        }
    }

    // Fechar Modal Detalhes
    if (closeDetailsBtn) {
        closeDetailsBtn.addEventListener('click', () => {
            detailsModal.style.display = 'none';
        });
    }
    
    // Inicia tudo
    initializeKanban();
    if (typeof feather !== 'undefined') feather.replace();
});