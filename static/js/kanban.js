/* static/js/kanban.js */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Kanban JS iniciado'); // Debug

    // 1. Inicializa o Quadro (Lendo do window)
    if (window.KANBAN_INITIAL_DATA) {
        renderBoard(window.KANBAN_INITIAL_DATA);
    } else {
        console.error('Dados iniciais (KANBAN_INITIAL_DATA) não encontrados.');
    }

    // 2. Configura Eventos Globais (Botão Nova Tarefa está aqui dentro)
    setupGlobalEventListeners();

    // 3. Inicializa Drag and Drop
    setupDragAndDrop();

    // 4. Ativa ícones Feather
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
});

/**
 * Renderiza todas as colunas e cards
 */
function renderBoard(data) {
    // Limpa visualmente as colunas
    document.querySelectorAll('.column-cards').forEach(el => el.innerHTML = '');

    // --- CORREÇÃO DO ERRO ---
    // Cria uma lista única de tarefas, não importa se veio como Objeto ou Array
    let allTasks = [];

    if (Array.isArray(data)) {
        // Se já for array, usa direto
        allTasks = data;
    } else if (typeof data === 'object' && data !== null) {
        // Se for objeto (ex: {'todo': [t1], 'done': [t2]}), junta tudo numa lista só
        Object.values(data).forEach(columnTasks => {
            if (Array.isArray(columnTasks)) {
                allTasks = allTasks.concat(columnTasks);
            }
        });
    }

    // Agora 'allTasks' é garantidamente um Array, então o forEach funciona
    allTasks.forEach(task => {
        const column = document.getElementById(`column-${task.status}`);
        if (column) {
            const container = column.querySelector('.column-cards');
            
            const safeTask = {
                ...task,
                priority: task.priority || 'low',
                id: task.id
            };

            const cardHTML = createCardHTML(safeTask);
            container.insertAdjacentHTML('beforeend', cardHTML);
        }
    });

    updateTaskCounts();
    if (typeof feather !== 'undefined') feather.replace();
}

/**
 * GERA O HTML DO CARD
 */
function createCardHTML(task) {
    let priorityClass = 'priority-low';
    let priorityLabel = 'Baixa';

    // Lógica corrigida para suportar as 3 cores
    if (task.priority === 'high') {
        priorityClass = 'priority-high';
        priorityLabel = 'Alta';
    } else if (task.priority === 'medium') {
        priorityClass = 'priority-medium';
        priorityLabel = 'Média';
    } else {
        priorityClass = 'priority-low';
        priorityLabel = 'Baixa';
    }
    
    let tagsHTML = '';
    if (task.tags && Array.isArray(task.tags)) {
        task.tags.forEach(tag => {
            tagsHTML += `<span class="context-tag">${tag}</span>`;
        });
    }

    const userInitials = task.assigned_to_username 
        ? task.assigned_to_username.substring(0, 2).toUpperCase() 
        : '--';

    return `
    <div class="kanban-card" draggable="true" data-id="${task.id}" data-priority="${task.priority}">
        <div class="card-header">
            <span class="priority-pill ${priorityClass}">
                <i data-feather="flag" style="width: 12px; height: 12px;"></i> ${priorityLabel}
            </span>
            
            <div class="card-actions" style="position: absolute; top: 15px; right: 15px;">
                <button type="button" class="btn-delete-task" data-id="${task.id}" title="Excluir">
                    <i data-feather="trash-2" style="width: 16px; height: 16px;"></i>
                </button>
            </div>
        </div>

        <h4 class="kanban-card-title">${task.title}</h4>
        
        <div class="card-footer">
            <div class="tags-container">
                ${tagsHTML}
            </div>
            <div class="card-assignee-avatar" title="${task.assigned_to_username || 'Sem responsável'}">
            ${userInitials}
            </div>
        </div>
    </div>
    `;
}

/**
 * Event Listeners Globais (Incluindo o BOTÃO NOVA TAREFA)
 */
function setupGlobalEventListeners() {
    const board = document.querySelector('.kanban-board');

    // A. Cliques no Board (Lixeira e Detalhes)
    if (board) {
        board.addEventListener('click', function(e) {
            const deleteBtn = e.target.closest('.btn-delete-task');
            if (deleteBtn) {
                e.stopPropagation(); 
                const taskId = deleteBtn.dataset.id;
                confirmDeleteTask(taskId);
                return;
            }

            const card = e.target.closest('.kanban-card');
            if (card) {
                const taskId = card.dataset.id;
                openTaskDetails(taskId);
            }
        });
    }

    // B. Botão "Nova Tarefa" (Abre Modal)
    const addTaskBtn = document.getElementById('add-task-btn');
    if(addTaskBtn) {
        // Remove listener antigo clonando (segurança contra múltiplos eventos)
        const newBtn = addTaskBtn.cloneNode(true);
        addTaskBtn.parentNode.replaceChild(newBtn, addTaskBtn);

        newBtn.addEventListener('click', (e) => {
            e.preventDefault();
            console.log('Botão Nova Tarefa clicado!'); // LOG PARA DEBUG
            const modal = document.getElementById('add-task-modal');
            if(modal) {
                modal.style.display = 'flex';
            } else {
                console.error('Erro: Modal #add-task-modal não encontrado no HTML.');
            }
        });
    } else {
        console.error('Erro: Botão #add-task-btn não encontrado no HTML.');
    }

    // C. Form "Nova Tarefa" (Salvar)
    const addForm = document.getElementById('add-task-form');
    if(addForm) {
        const newForm = addForm.cloneNode(true);
        addForm.parentNode.replaceChild(newForm, addForm);
        newForm.addEventListener('submit', handleAddTaskSubmit);
    }

    // D. Fechar Modais
    document.querySelectorAll('.close-button').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const modalId = e.target.dataset.modalId;
            const modal = document.getElementById(modalId) || e.target.closest('.modal');
            if(modal) modal.style.display = 'none';
        });
    });

    // E. Fechar clicando fora
    window.onclick = function(event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = "none";
        }
    }
}

/**
 * Lógica de Drag and Drop
 */
function setupDragAndDrop() {
    const columns = document.querySelectorAll('.kanban-column');

    document.addEventListener('dragstart', (e) => {
        if (e.target.classList.contains('kanban-card')) {
            e.target.classList.add('dragging');
            e.dataTransfer.setData('text/plain', e.target.dataset.id);
        }
    });

    document.addEventListener('dragend', (e) => {
        if (e.target.classList.contains('kanban-card')) {
            e.target.classList.remove('dragging');
        }
    });

    columns.forEach(column => {
        column.addEventListener('dragover', (e) => {
            e.preventDefault(); 
            const afterElement = getDragAfterElement(column.querySelector('.column-cards'), e.clientY);
            const draggable = document.querySelector('.dragging');
            const container = column.querySelector('.column-cards');
            
            if (draggable) {
                if (afterElement == null) {
                    container.appendChild(draggable);
                } else {
                    container.insertBefore(draggable, afterElement);
                }
            }
        });

        column.addEventListener('drop', (e) => {
            e.preventDefault();
            const draggable = document.querySelector('.dragging');
            if (!draggable) return;

            const newStatus = column.dataset.status;
            const taskId = draggable.dataset.id;
            
            updateTaskStatus(taskId, newStatus);
            updateTaskCounts();
        });
    });
}

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

/**
 * Atualiza status (Backend)
 */
function updateTaskStatus(taskId, newStatus) {
    // Usa window.URL e window.CSRF
    const url = window.KANBAN_UPDATE_URL;
    const csrf = window.CSRF_TOKEN;

    if (!url) { console.error("URL de update não definida"); return; }

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf
        },
        body: JSON.stringify({
            task_id: taskId,
            status: newStatus
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status !== 'success') {
            alert('Erro ao mover tarefa. Recarregue a página.');
        }
    })
    .catch(error => console.error('Erro de rede:', error));
}

/**
 * Salvar Nova Tarefa
 */
function handleAddTaskSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = 'Salvando...';
    submitBtn.disabled = true;

    const formData = new FormData(form);

    fetch(window.ADD_TASK_API_URL, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': window.CSRF_TOKEN
        }
    })
    .then(response => {
        // Se a resposta não for OK (ex: 500 ou 404), pegamos o texto (HTML) para ver o erro
        if (!response.ok) {
            return response.text().then(text => {
                throw new Error(`Erro do Servidor (${response.status}): \n${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            const column = document.getElementById(`column-${data.task.status}`);
            if (column) {
                const container = column.querySelector('.column-cards');
                const cardHTML = createCardHTML(data.task);
                container.insertAdjacentHTML('beforeend', cardHTML);
                updateTaskCounts();
                if (typeof feather !== 'undefined') feather.replace();
            }
            form.reset();
            document.getElementById('add-task-modal').style.display = 'none';
        } else {
            alert('Erro de validação: ' + JSON.stringify(data.errors));
        }
    })
    .catch(error => {
        console.error('ERRO DETALHADO:', error);
        
        // Se o erro for HTML, tenta mostrar só a mensagem principal no alert
        if (error.message.includes('<!DOCTYPE html>')) {
             alert('Erro Interno no Servidor (500). Verifique o terminal do Django ou o Console do navegador para detalhes.');
        } else {
             alert('Erro ao salvar: ' + error.message);
        }
    })
    .finally(() => {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    });
}

/**
 * Abre Detalhes da Tarefa
 */
function openTaskDetails(taskId) {
    const modal = document.getElementById('task-details-modal');
    const contentDiv = document.getElementById('task-details-content');
    const url = window.GET_TASK_DETAILS_URL_BASE + taskId + '/';
    
    contentDiv.innerHTML = '<div style="padding:20px; text-align:center;">Carregando...</div>';
    modal.style.display = 'flex';

    fetch(url)
        .then(res => res.json())
        .then(data => {
            if(data.error) throw new Error(data.error);

            contentDiv.innerHTML = `
                <h2>${data.title}</h2>
                <div class="detail-grid">
                    <div class="detail-item"><strong>Status:</strong> ${data.status_display}</div>
                    <div class="detail-item"><strong>Prioridade:</strong> ${data.priority_display}</div>
                    <div class="detail-description">
                        <strong>Descrição:</strong>
                        <p>${data.description || 'Nenhuma descrição.'}</p>
                    </div>
                    <div class="detail-item"><strong>Responsável:</strong> ${data.assigned_to_username || 'Ninguém'}</div>
                </div>
                
                <div style="margin-top: 20px; text-align: right; border-top: 1px solid #eee; padding-top: 15px;">
                     <button id="btn-modal-delete" style="background:none; border:none; color: #EF4444; cursor:pointer; font-weight:bold; display:flex; align-items:center; gap:5px; margin-left:auto;">
                        <i data-feather="trash-2" style="width:16px;"></i> Excluir Tarefa
                     </button>
                </div>
            `;
            
            document.getElementById('btn-modal-delete').onclick = () => confirmDeleteTask(taskId);
            if (typeof feather !== 'undefined') feather.replace();
        })
        .catch(err => {
            contentDiv.innerHTML = `<p style="color:red; text-align:center;">Erro ao carregar detalhes.</p>`;
        });
}

/**
 * Excluir Tarefa
 */
function confirmDeleteTask(taskId) {
    if(confirm('Tem certeza que deseja excluir esta tarefa permanentemente?')) {
        const url = window.DELETE_TASK_URL_BASE + taskId + '/';

        fetch(url, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': window.CSRF_TOKEN,
                'Content-Type': 'application/json'
            }
        })
        .then(res => {
            if(res.ok) {
                const card = document.querySelector(`.kanban-card[data-id="${taskId}"]`);
                if(card) card.remove();
                document.getElementById('task-details-modal').style.display = 'none';
                updateTaskCounts();
            } else {
                alert('Erro ao excluir tarefa.');
            }
        })
        .catch(err => console.error(err));
    }
}

function updateTaskCounts() {
    document.querySelectorAll('.kanban-column').forEach(col => {
        const count = col.querySelectorAll('.kanban-card').length;
        const badge = col.querySelector('.task-count');
        if(badge) badge.textContent = count;
    });
}