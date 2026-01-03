// static/js/calendar.js

document.addEventListener('DOMContentLoaded', function() {
    
    // --- ELEMENTOS DOM ---
    const grid = document.getElementById('calendar-grid');
    const monthDisplay = document.getElementById('month-year-display');
    const modalOverlay = document.getElementById('event-modal-overlay');
    
    // Configurações
    const urls = JSON.parse(document.getElementById('django-urls').textContent);
    let currentDate = new Date();

    // --- 1. RENDERIZAÇÃO DO CALENDÁRIO ---
    async function renderCalendar() {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth();

        // 1. Atualiza Título do Mês
        monthDisplay.textContent = new Date(year, month).toLocaleString('pt-BR', { month: 'long', year: 'numeric' });
        monthDisplay.style.textTransform = 'capitalize';

        // 2. Limpa o Grid
        grid.innerHTML = '';

        // 3. Cálculos de Datas
        const firstDayIndex = new Date(year, month, 1).getDay(); // 0 = Domingo
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        const todayStr = new Date().toISOString().split('T')[0];

        // 4. Renderiza Células Vazias (Padding)
        for (let i = 0; i < firstDayIndex; i++) {
            const pad = document.createElement('div');
            pad.className = 'day-cell padding-cell';
            grid.appendChild(pad);
        }

        // 5. Renderiza os Dias (Estrutura Vazia Primeiro)
        for (let d = 1; d <= daysInMonth; d++) {
            const dateStr = `${year}-${String(month+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
            const cell = document.createElement('div');
            cell.className = `day-cell ${dateStr === todayStr ? 'today' : ''}`;
            cell.dataset.date = dateStr; // Guarda a data para usar depois
            
            // Número do dia
            cell.innerHTML = `<span class="day-number">${d}</span><div class="events-container"></div>`;
            
            grid.appendChild(cell);
        }

        // 6. Busca e Preenche Eventos (Assíncrono)
        try {
            const response = await fetch(`${urls.getEvents}?year=${year}&month=${month + 1}`);
            if (!response.ok) throw new Error('Erro na API');
            
            const events = await response.json();
            
            // Distribui os eventos nas células criadas
            events.forEach(evt => {
                const cell = grid.querySelector(`.day-cell[data-date="${evt.date}"] .events-container`);
                if (cell) {
                    const chip = createEventChip(evt);
                    cell.appendChild(chip);
                }
            });

        } catch (error) {
            console.error("Erro ao carregar eventos:", error);
        }
    }

    // --- HELPER: CRIA O CHIP VISUAL ---
    function createEventChip(evt) {
        const chip = document.createElement('div');
        chip.className = 'event-chip';
        
        // Define ícones
        let iconClass = 'fa-solid fa-share';
        if (evt.platform === 'instagram') iconClass = 'fa-brands fa-instagram';
        if (evt.platform === 'facebook') iconClass = 'fa-brands fa-facebook';
        if (evt.platform === 'linkedin') iconClass = 'fa-brands fa-linkedin';
        if (evt.platform === 'tiktok') iconClass = 'fa-brands fa-tiktok';

        // Define cores de status (bolinha)
        let statusClass = 'dot-draft';
        if (evt.status === 'Scheduled') statusClass = 'dot-scheduled';
        if (evt.status === 'Pending') statusClass = 'dot-pending';

        // Define Logo (Usa placeholder se falhar)
        const logoUrl = evt.brandLogo || 'https://via.placeholder.com/20';

        chip.innerHTML = `
            <div class="chip-left">
                <img src="${logoUrl}" class="chip-logo" onerror="this.src='https://via.placeholder.com/20'">
                <span class="chip-title">${evt.title}</span>
            </div>
            <div class="chip-right">
                <span class="dot ${statusClass}" style="margin-right:5px;"></span>
                <i class="${iconClass} chip-icon"></i>
            </div>
        `;
        
        // Adiciona clique para abrir sidebar (se necessário)
        chip.addEventListener('click', (e) => {
            e.stopPropagation();
            if(window.openSidebar) window.openSidebar(evt); // Chama função global se existir
        });

        return chip;
    }

    // --- CONTROLE DA MODAL ---
    const btnNewPost = document.getElementById('add-post-btn');
    const btnClose = document.getElementById('modal-close-button');
    const btnCancel = document.getElementById('modal-cancel-button');

    function openModal() {
        // Usa flex para centralizar graças ao CSS corrigido
        modalOverlay.style.display = 'flex'; 
        loadClients(); // Carrega clientes no select
    }

    function closeModal() {
        modalOverlay.style.display = 'none';
    }

    if(btnNewPost) btnNewPost.addEventListener('click', openModal);
    if(btnClose) btnClose.addEventListener('click', closeModal);
    if(btnCancel) btnCancel.addEventListener('click', closeModal);
    
    // Fechar ao clicar fora
    modalOverlay.addEventListener('click', (e) => {
        if(e.target === modalOverlay) closeModal();
    });

    // --- NAVEGAÇÃO ---
    document.getElementById('prev-month').addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar();
    });
    document.getElementById('next-month').addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar();
    });
    document.getElementById('today-button').addEventListener('click', () => {
        currentDate = new Date();
        renderCalendar();
    });

    // --- INICIALIZAÇÃO ---
    renderCalendar();

    // --- CARREGAR CLIENTES (Select) ---
    async function loadClients() {
        const select = document.getElementById('event-client');
        if(select.options.length > 1) return; // Evita recarregar se já tem dados
        
        try {
            const res = await fetch(urls.getClients);
            const data = await res.json();
            data.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c.id;
                opt.textContent = c.name;
                select.appendChild(opt);
            });
        } catch(e) { console.error(e); }
    }
});