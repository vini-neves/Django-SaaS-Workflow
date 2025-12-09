// static/js/create_post_studio.js

document.addEventListener('DOMContentLoaded', () => {
    
    // Inicializa ícones do Feather se disponível
    if (typeof feather !== 'undefined') feather.replace();

    // --- ELEMENTOS DO DOM ---
    const clientSelect = document.getElementById('post-client');
    const channelBar = document.getElementById('channel-bar-container');
    const captionInput = document.getElementById('input-caption');
    const mediaInput = document.getElementById('input-media');
    
    // --- LISTA MESTRA DE PLATAFORMAS (Fixa) ---
    // O JS vai desenhar ESSA lista, não importa o que venha do banco.
    const SUPPORTED_PLATFORMS = [
        { id: 'facebook', name: 'Facebook', icon: 'facebook-f', type: 'brands' },
        { id: 'instagram', name: 'Instagram', icon: 'instagram', type: 'brands' },
        { id: 'linkedin', name: 'LinkedIn', icon: 'linkedin-in', type: 'brands' },
        { id: 'youtube', name: 'YouTube', icon: 'youtube', type: 'brands' },
        { id: 'tiktok', name: 'TikTok', icon: 'tiktok', type: 'brands' },
        { id: 'x', name: 'X (Twitter)', icon: 'x-twitter', type: 'brands' },
        { id: 'threads', name: 'Threads', icon: 'threads', type: 'brands' },
        { id: 'pinterest', name: 'Pinterest', icon: 'pinterest-p', type: 'brands' }
    ];

    // --- FUNÇÃO DE RENDERIZAÇÃO ---
    function renderChannelBar(clientId) {
        channelBar.innerHTML = ''; 
        
        if (!clientId) {
            channelBar.innerHTML = '<p style="color:#999; font-size:0.9em; width:100%; text-align:center;">Selecione um cliente acima para ver os canais.</p>';
            return;
        }

        const clientAccounts = (typeof CLIENTS_MAP !== 'undefined' && CLIENTS_MAP[clientId]) ? CLIENTS_MAP[clientId] : {};

        SUPPORTED_PLATFORMS.forEach(platform => {
            const account = clientAccounts[platform.id]; 
            const isConnected = !!account;

            const label = document.createElement('label');
            label.className = 'channel-select-item';
            
            // Definimos o tipo de ícone (padrão 'brands' se não especificado)
            const iconType = platform.type || 'brands';

            if (isConnected) {
                // --- CONECTADO ---
                label.title = `${platform.name}: ${account.name}`;
                label.innerHTML = `
                    <input type="checkbox" name="accounts" value="${account.id}" data-platform="${platform.id}">
                    <div class="channel-icon-lg bg-${platform.id}">
                        <i class="fa-${iconType} fa-${platform.icon}"></i>
                    </div>
                    <span class="channel-name-label">${platform.name}</span>
                `;
                
                const checkbox = label.querySelector('input');
                checkbox.addEventListener('change', () => {
                    if (window.updateTabs) window.updateTabs();
                });

            } else {
                // --- DESCONECTADO ---
                label.title = `Conectar ${platform.name}`;
                label.innerHTML = `
                    <div class="channel-icon-lg disconnected" onclick="redirectToConnect('${platform.name}')">
                        <i class="fa-${iconType} fa-${platform.icon}"></i>
                        <span class="plus-badge">+</span>
                    </div>
                    <span class="channel-name-label">${platform.name}</span>
                `;
            }

            channelBar.appendChild(label);
        });
    

        // Atualiza os ícones SVG
        if (typeof feather !== 'undefined') feather.replace();
    }

    // --- FUNÇÃO PARA CONECTAR (Redirecionamento) ---
    window.redirectToConnect = function(platformName) {
        const targetUrl = (typeof SOCIAL_DASHBOARD_URL !== 'undefined') ? SOCIAL_DASHBOARD_URL : '/social/';
        
        Swal.fire({
            title: `Conectar ${platformName}?`,
            text: `Nenhuma conta vinculada. Deseja ir para a tela de conexões?`,
            icon: 'info',
            showCancelButton: true,
            confirmButtonText: 'Ir para Conexões',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: 'var(--primary-color)'
        }).then((result) => {
            if (result.isConfirmed) {
                window.open(targetUrl, '_blank');
            }
        });
    };

    // --- INICIALIZAÇÃO DA TELA ---
    
    // 1. Verifica se veio cliente pré-selecionado da URL
    if (typeof PRE_SELECTED_CLIENT_ID !== 'undefined' && PRE_SELECTED_CLIENT_ID && PRE_SELECTED_CLIENT_ID !== 'None') {
        if(clientSelect) clientSelect.value = PRE_SELECTED_CLIENT_ID;
        renderChannelBar(PRE_SELECTED_CLIENT_ID);
        // Atualiza avatar
        updateClientPreviewInfo(clientSelect);
    }

    // 2. Listener para troca manual de cliente
    if (clientSelect) {
        clientSelect.addEventListener('change', function() {
            renderChannelBar(this.value);
            updateClientPreviewInfo(this);
        });
    }

    // --- (RESTO DO CÓDIGO: PREVIEW, UPLOAD, ETC.) ---
    
    function updateClientPreviewInfo(selectElement) {
        if (selectElement.selectedIndex > -1) {
            const opt = selectElement.options[selectElement.selectedIndex];
            const name = opt.text;
            const logo = opt.dataset.logo || "https://ui-avatars.com/api/?name=" + name + "&background=random";
            
            document.querySelectorAll('.client-name').forEach(el => el.innerText = name);
            document.querySelectorAll('.client-avatar').forEach(el => el.src = logo);
        }
    }

    if(captionInput) {
        captionInput.addEventListener('input', function() {
            const text = this.value || "Sua legenda...";
            document.querySelectorAll('.caption-text').forEach(el => el.innerText = text);
        });
    }
    
    if(mediaInput) {
        mediaInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const objectUrl = URL.createObjectURL(file);
                const isVideo = file.type.startsWith('video/');
                document.querySelectorAll('.placeholder-media').forEach(el => el.style.display = 'none');
                
                if (isVideo) {
                    document.querySelectorAll('.preview-img').forEach(el => el.style.display = 'none');
                    document.querySelectorAll('.preview-video').forEach(el => {
                        el.src = objectUrl; el.style.display = 'block';
                    });
                } else {
                    document.querySelectorAll('.preview-video').forEach(el => el.style.display = 'none');
                    document.querySelectorAll('.preview-img').forEach(el => {
                        el.src = objectUrl; el.style.display = 'block';
                    });
                }
                const fileNameDisplay = document.getElementById('file-name-display');
                if(fileNameDisplay) fileNameDisplay.innerText = file.name;
            }
        });
    }

    // SUBMIT FORM
    const form = document.getElementById('create-post-form');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            // Valida se tem conta selecionada
            if(document.querySelectorAll('input[name="accounts"]:checked').length === 0) {
                Swal.fire('Atenção', 'Selecione pelo menos uma rede social para publicar.', 'warning');
                return;
            }
            
            const btn = this.querySelector('button[type="submit"]');
            const originalText = btn.innerText;
            btn.innerText = "Salvando...";
            btn.disabled = true;

            const formData = new FormData(this);

            try {
                const response = await fetch(API_URL, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': CSRF_TOKEN },
                    body: formData
                });
                const result = await response.json();

                if (response.ok) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Sucesso!',
                        text: 'Post agendado e enviado para o Kanban!'
                    }).then(() => {
                        window.location.href = KANBAN_URL;
                    });
                } else {
                    Swal.fire('Erro', result.message, 'error');
                }
            } catch (error) {
                Swal.fire('Erro', 'Falha na conexão.', 'error');
            } finally {
                btn.innerText = originalText;
                btn.disabled = false;
            }
        });
    }
});