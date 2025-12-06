// static/js/kanban.js

document.addEventListener('DOMContentLoaded', () => {
    
    // --- Seletores do DOM ---
    const kanbanBoard = document.querySelector('.kanban-board');
    const columns = document.querySelectorAll('.kanban-column');
    
    // --- Seletores de Botões ---
    const addTaskBtn = document.getElementById('add-task-btn');
    const toggleDoneBtn = document.getElementById('toggle-done-column');

    // --- Seletores do Modal (Adicionar Tarefa) ---
    const addTaskModal = document.getElementById('add-task-modal');
    const addTaskForm = document.getElementById('add-task-form');
    const closeTaskModal = addTaskModal.querySelector('.close-button');

    // --- Seletores do Modal (Detalhes da Tarefa) ---
    const detailsModal = document.getElementById('task-details-modal');
    const detailsContent = document.getElementById('task-details-content');
    const closeDetailsModal = detailsModal.querySelector('.close-button');

    let draggedCard = null;

    // --- Funções de Ajuda ---

    function updateTaskCounts() {
        columns.forEach(column => {
            const count = column.querySelector('.column-cards').children.length;
            column.querySelector('.task-count').textContent = count;
        });
    }

    // --- CRIAÇÃO DE CARD ATUALIZADA ---
    function createTaskCard(task) {
        const card = document.createElement('div');
        card.classList.add('kanban-card');
        card.setAttribute('draggable', 'true');
        card.dataset.taskId = task.id;
        card.dataset.status = task.status;

        // Avatar (Iniciais)
        const avatar = task.assigned_to_username
            ? `<div class="card-assignee-avatar" title="${task.assigned_to_username}">${task.assigned_to_initials}</div>`
            : `<div class="card-assignee-avatar" title="Ninguém atribuído">?</div>`;

        // Botão Deletar
        const deleteBtn = `
            <div class="card-delete-btn" title="Excluir tarefa">
                <i data-feather="trash-2" style="width:16px; height:16px;"></i>
            </div>
        `;

        card.innerHTML = `
            <div class="card-header">
                <h4 class="kanban-card-title">${task.title}</h4>
                ${deleteBtn}
            </div>
            <p class="kanban-card-description">${task.description || ''}</p>
            <div class="card-footer">
                <span class="kanban-card-project">${task.project_name}</span>
                ${avatar}
            </div>
        `;

        // --- Event Listeners do Card ---
        card.addEventListener('dragstart', (e) => {
            draggedCard = card;
            setTimeout(() => card.classList.add('dragging'), 0);
        });

        card.addEventListener('dragend', () => {
            if (draggedCard) { // Prevenção de erro
                draggedCard.classList.remove('dragging');
            }
            draggedCard = null;
        });
        
       
        card.addEventListener('click', (e) => {
           
            if (e.target.closest('.card-delete-btn')) {
                return;
            }
            openDetailsModal(task.id);
        });

        // --- DELETAR TAREFA ---
        card.querySelector('.card-delete-btn').addEventListener('click', (e) => {
            e.stopPropagation(); // Impede que o modal de detalhes abra
            deleteTask(task.id, card);
        });

        return card;
    }

    async function saveTaskChanges(taskId, newStatus, columnElement) {
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
            if (response.ok) updateTaskCounts();
        } catch (error) {
            console.error('Erro na API de atualização:', error);
        }
    }

    // --- NOVO: Deletar Tarefa (com SweetAlert) ---
    function deleteTask(taskId, cardElement) {
        Swal.fire({
            title: 'Você tem certeza?',
            text: "Esta ação não pode ser revertida!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sim, excluir!',
            cancelButtonText: 'Cancelar'
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    const response = await fetch(`${DELETE_TASK_URL_BASE}${taskId}/delete/`, {
                        method: 'DELETE',
                        headers: { 'X-CSRFToken': CSRF_TOKEN }
                    });
                    
                    if (response.ok) {
                        cardElement.remove(); // Remove o card do DOM
                        updateTaskCounts(); // Atualiza a contagem
                        Swal.fire('Excluído!', 'A tarefa foi excluída.', 'success');
                    } else {
                        Swal.fire('Erro!', 'Não foi possível excluir a tarefa.', 'error');
                    }
                } catch (error) {
                    Swal.fire('Erro!', 'Erro de rede.', 'error');
                }
            }
        });
    }

    // --- NOVO: Abrir Modal de Detalhes ---
    async function openDetailsModal(taskId) {
        try {
            const response = await fetch(`${GET_TASK_DETAILS_URL_BASE}${taskId}/details/`);
            if (!response.ok) throw new Error('Falha ao buscar dados.');
            
            const task = await response.json();
            
            // Popula o conteúdo do modal
            detailsContent.innerHTML = `
                <h2>${task.title}</h2>
                <div class="detail-grid">
                    <div class="detail-item">
                        <strong>Status</strong>
                        <span>${task.status}</span>
                    </div>
                    <div class="detail-item">
                        <strong>Projeto</strong>
                        <span>${task.project_name}</span>
                    </div>
                    <div class="detail-item">
                        <strong>Criado em</strong>
                        <span>${task.created_at}</span>
                    </div>
                    <div class="detail-item">
                        <strong>Atribuído a</strong>
                        <span>${task.assigned_to}</span>
                    </div>
                </div>
                <div class="detail-item detail-description">
                    <strong>Descrição</strong>
                    <p>${task.description.replace(/\n/g, '<br>')}</p>
                </div>
            `;
            detailsModal.style.display = 'flex';
            document.body.classList.add('modal-open');
        } catch (error) {
            console.error("Erro ao abrir detalhes:", error);
            Swal.fire('Erro', 'Não foi possível carregar os detalhes da tarefa.', 'error');
        }
    }

    // --- Inicialização do Kanban ---
    function initializeKanban() {
        for (const status in KANBAN_INITIAL_DATA) {
            const columnCards = document.querySelector(`#column-${status} .column-cards`);
            if (columnCards) {
                KANBAN_INITIAL_DATA[status].forEach(task => {
                    columnCards.appendChild(createTaskCard(task));
                });
            }
        }
        updateTaskCounts();
        feather.replace(); // Ativa os ícones nos cards
    }

    // --- Lógica de Drag & Drop ---
    columns.forEach(column => {
        column.addEventListener('dragover', (e) => {
            e.preventDefault();
            const afterElement = getDragAfterElement(column.querySelector('.column-cards'), e.clientY);
            if (draggedCard) {
                if (afterElement == null) {
                    column.querySelector('.column-cards').appendChild(draggedCard);
                } else {
                    column.querySelector('.column-cards').insertBefore(draggedCard, afterElement);
                }
            }
        });

        column.addEventListener('drop', () => {
            if (draggedCard) {
                const newStatus = column.dataset.status;
                const taskId = draggedCard.dataset.taskId;
                draggedCard.dataset.status = newStatus;
                saveTaskChanges(taskId, newStatus, column.querySelector('.column-cards'));
            }
        });
    });

    function getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.kanban-card:not(.dragging)')];
        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else { return closest; }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    // --- Lógica do Modal (Adicionar Tarefa) ---
    addTaskBtn.addEventListener('click', () => {
        addTaskModal.style.display = 'flex';
        document.body.classList.add('modal-open');
    });
    closeTaskModal.addEventListener('click', () => {
        addTaskModal.style.display = 'none';
        document.body.classList.remove('modal-open');
        addTaskForm.reset();
    });

    // --- Lógica do Modal (Detalhes) ---
    closeDetailsModal.addEventListener('click', () => {
        detailsModal.style.display = 'none';
        document.body.classList.remove('modal-open');
        detailsContent.innerHTML = ""; // Limpa o conteúdo
    });

    window.addEventListener('click', (event) => {
        if (event.target == addTaskModal) {
            addTaskModal.style.display = 'none';
            document.body.classList.remove('modal-open');
            addTaskForm.reset();
        }
        if (event.target == detailsModal) {
            detailsModal.style.display = 'none';
            document.body.classList.remove('modal-open');
            detailsContent.innerHTML = "";
        }
    });

    // --- Lógica de Submissão do Formulário (Adicionar Tarefa) ---
    addTaskForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(addTaskForm);
        const data = Object.fromEntries(formData.entries());

        try {
            const response = await fetch(ADD_TASK_API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const new_task_data = await response.json();
                const todoColumn = document.querySelector('#column-todo .column-cards');
                const newCard = createTaskCard(new_task_data);
                todoColumn.appendChild(newCard);
                updateTaskCounts();
                feather.replace(); // Ativa o ícone no novo card
                
                addTaskModal.style.display = 'none';
                addTaskForm.reset();
                Swal.fire('Sucesso!', 'Nova tarefa criada.', 'success');
            } else {
                Swal.fire('Erro!', 'Não foi possível criar a tarefa.', 'error');
            }
        } catch (error) {
            Swal.fire('Erro!', 'Erro de rede.', 'error');
        }
    });

    // --- NOVO: Lógica para Ocultar Coluna "Concluído" ---
    toggleDoneBtn.addEventListener('click', () => {
        const doneColumn = document.getElementById('column-done');
        const icon = toggleDoneBtn.querySelector('i');
        const span = toggleDoneBtn.querySelector('span');

        doneColumn.classList.toggle('is-hidden');
        
        if (doneColumn.classList.contains('is-hidden')) {
            // Se está oculta
            icon.innerHTML = feather.icons.eye.toSvg();
            span.textContent = 'Mostrar Concluídos';
        } else {
            // Se está visível
            icon.innerHTML = feather.icons['eye-off'].toSvg();
            span.textContent = 'Ocultar Concluídos';
        }
    });

    // --- Inicializar o Kanban ---
    initializeKanban();
});