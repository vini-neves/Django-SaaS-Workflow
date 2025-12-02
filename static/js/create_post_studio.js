// static/js/create_post_studio.js

document.addEventListener('DOMContentLoaded', () => {
    
    // Inicializa ícones
    if (typeof feather !== 'undefined') feather.replace();

    // --- 1. Lógica de Preview (O que você vê é o que você tem) ---

    // Atualiza o texto em TODOS os mockups ao mesmo tempo
    const captionInput = document.getElementById('input-caption');
    if (captionInput) {
        captionInput.addEventListener('input', function() {
            const text = this.value;
            const displayText = text || "Sua legenda aparecerá aqui...";
            document.querySelectorAll('.caption-text').forEach(el => el.innerText = displayText);
        });
    }

    // Atualiza a Mídia (Imagem/Vídeo)
    const mediaInput = document.getElementById('input-media');
    if (mediaInput) {
        mediaInput.addEventListener('change', function() {
            const file = this.files[0];
            
            if (file) {
                const objectUrl = URL.createObjectURL(file);
                const isImage = file.type.startsWith('image/');
                const isVideo = file.type.startsWith('video/');

                // Esconde placeholder
                document.querySelectorAll('#placeholder-media').forEach(el => el.style.display = 'none');

                if (isImage) {
                    document.querySelectorAll('video').forEach(v => v.style.display = 'none');
                    document.querySelectorAll('img[id^="preview-img"]').forEach(img => {
                        img.src = objectUrl;
                        img.style.display = 'block';
                    });
                } else if (isVideo) {
                    document.querySelectorAll('img[id^="preview-img"]').forEach(img => img.style.display = 'none');
                    document.querySelectorAll('video').forEach(video => {
                        video.src = objectUrl;
                        video.style.display = 'block';
                    });
                }
            }
        });
    }

    // Atualiza o Cliente (Nome e Avatar)
    const clientSelect = document.getElementById('post-client');
    if (clientSelect) {
        clientSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            const name = selectedOption.text;
            const logo = selectedOption.dataset.logo || "https://via.placeholder.com/50";

            document.querySelectorAll('.client-name').forEach(el => el.innerText = name);
            document.querySelectorAll('.client-avatar').forEach(img => img.src = logo);
        });
    }

    // --- 2. Lógica de Abas ---
    
    // Torna a função global para ser usada no onclick do HTML, ou adiciona listeners aqui
    window.switchPreview = function(type) {
        document.querySelectorAll('.device-mockup').forEach(el => el.style.display = 'none');
        document.querySelectorAll('.preview-tab').forEach(tab => tab.classList.remove('active'));
        
        // Adiciona classe active na aba clicada (gambiarra visual simples)
        // O ideal seria passar o evento 'e' e fazer e.target.classList.add('active')
        
        if (type === 'feed') {
            document.getElementById('mockup-instagram_feed').style.display = 'block';
        } else if (type === 'story') {
            document.getElementById('mockup-vertical').style.display = 'block';
        } else if (type === 'linkedin') {
            document.getElementById('mockup-linkedin').style.display = 'block';
        }
    };


    // --- 3. Envio do Formulário ---

    const form = document.getElementById('create-post-form');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerText;
            submitBtn.innerText = "Salvando...";
            submitBtn.disabled = true;

            const formData = new FormData(this);

            try {
                // USA AS VARIÁVEIS GLOBAIS DEFINIDAS NO HTML
                const response = await fetch(API_URL, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': CSRF_TOKEN
                    },
                    body: formData
                });

                const result = await response.json();

                if (response.ok) {
                    if (typeof Swal !== 'undefined') {
                        Swal.fire({
                            icon: 'success',
                            title: 'Sucesso!',
                            text: 'Postagem criada e enviada para o Kanban Operacional!',
                            confirmButtonText: 'Ir para o Kanban'
                        }).then((result) => {
                            if (result.isConfirmed) {
                                window.location.href = KANBAN_URL;
                            }
                        });
                    } else {
                        alert("Postagem criada com sucesso!");
                        window.location.href = KANBAN_URL;
                    }
                } else {
                    if (typeof Swal !== 'undefined') {
                        Swal.fire('Erro', result.message, 'error');
                    } else {
                        alert('Erro: ' + result.message);
                    }
                }
            } catch (error) {
                console.error(error);
                alert('Erro de rede ao salvar postagem.');
            } finally {
                submitBtn.innerText = originalText;
                submitBtn.disabled = false;
            }
        });
    }
});