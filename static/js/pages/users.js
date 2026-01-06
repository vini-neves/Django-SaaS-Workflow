/* static/js/pages/users.js */

let userModal;

document.addEventListener('DOMContentLoaded', function() {
    // 1. Inicializa o Modal do Bootstrap
    const modalEl = document.getElementById('userModal');
    
    if(modalEl && typeof bootstrap !== 'undefined') {
        // --- CORREÇÃO DO BACKDROP ---
        // Move o modal para o final do body para evitar problemas de z-index/sobreposição
        document.body.appendChild(modalEl);
        
        userModal = new bootstrap.Modal(modalEl);
    } else {
        console.error("Bootstrap ou Modal não encontrado!");
    }

    // 2. Filtros da Tabela
    const searchInput = document.getElementById('userSearch');
    const agencyFilter = document.getElementById('agencyFilter');
    const roleFilter = document.getElementById('roleFilter');

    if(searchInput) searchInput.addEventListener('keyup', filterTable);
    if(agencyFilter) agencyFilter.addEventListener('change', filterTable);
    if(roleFilter) roleFilter.addEventListener('change', filterTable);

    // 3. Envio do Formulário
    const form = document.getElementById('createUserForm');
    if(form) {
        form.addEventListener('submit', handleUserSubmit);
    }
});

// --- FUNÇÕES GLOBAIS (Para o onclick funcionar) ---

/**
 * Abre o modal em modo de CRIAÇÃO
 */
window.openUserModal = function() {
    const form = document.getElementById('createUserForm');
    if(form) form.reset();

    // Limpa o ID oculto (indica criação)
    const idInput = document.getElementById('editUserId');
    if(idInput) idInput.value = "";

    // Restaura textos e validações para "Novo Usuário"
    const title = document.getElementById('modalTitleLabel'); // Certifique-se de ter esse ID no <h5> do modal
    if(title) title.innerText = "Adicionar Novo Membro";

    const activeSwitch = document.getElementById('userActiveSwitch');
    if(activeSwitch) activeSwitch.checked = true;

    const submitBtn = document.querySelector('#createUserForm button[type="submit"]');
    if(submitBtn) submitBtn.innerText = "Criar Usuário";
    
    // Senha é obrigatória na criação
    const passInput = document.getElementById('userPassword');
    if(passInput) {
        passInput.setAttribute('required', 'required');
        passInput.placeholder = "Mínimo 8 caracteres";
    }
    
    if(userModal) userModal.show();
}

window.editUser = function(button) {
    const form = document.getElementById('createUserForm');
    if(form) form.reset();

    // 1. Pega os dados dos atributos data-
    const id = button.dataset.id;
    const firstName = button.dataset.firstname;
    const lastName = button.dataset.lastname;
    const email = button.dataset.email;
    const username = button.dataset.username;
    const agency = button.dataset.agency; // ID da agência
    const role = button.dataset.role;
    const isActive = button.dataset.isactive === 'true';
    // 2. Preenche os campos
    document.getElementById('editUserId').value = id;
    if(document.querySelector('input[name="first_name"]')) document.querySelector('input[name="first_name"]').value = firstName;
    if(document.querySelector('input[name="last_name"]')) document.querySelector('input[name="last_name"]').value = lastName;
    if(document.querySelector('input[name="email"]')) document.querySelector('input[name="email"]').value = email;
    if(document.querySelector('input[name="username"]')) document.querySelector('input[name="username"]').value = username;
    
    // Selects
    const agencySelect = document.querySelector('select[name="agency"]');
    if (agencySelect && agency) agencySelect.value = agency;
    
    const roleSelect = document.querySelector('select[name="role"]');
    if(roleSelect) roleSelect.value = role;

    // 3. Ajusta UI para Edição
    const title = document.querySelector('.modal-title');
    if(title) title.innerText = "Editar Membro";

    const activeSwitch = document.getElementById('userActiveSwitch');
    if(activeSwitch) activeSwitch.checked = isActive;

    const submitBtn = document.querySelector('#createUserForm button[type="submit"]');
    if(submitBtn) submitBtn.innerText = "Salvar Alterações";

    // 4. Senha opcional na edição
    const passInput = document.getElementById('userPassword');
    if(passInput) {
        passInput.removeAttribute('required');
        passInput.placeholder = "Deixe em branco para manter a atual";
    }

    if(userModal) userModal.show();
}

window.togglePass = function() {
    const input = document.getElementById('userPassword');
    const icon = document.querySelector('.toggle-password');
    if (input.type === "password") {
        input.type = "text";
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = "password";
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// Lógica de Filtro
function filterTable() {
    const search = document.getElementById('userSearch').value.toLowerCase();
    const agencyEl = document.getElementById('agencyFilter');
    const agency = agencyEl ? agencyEl.value.toLowerCase() : '';
    const role = document.getElementById('roleFilter').value.toLowerCase();
    
    const rows = document.querySelectorAll('#usersTableBody tr');

    rows.forEach(row => {
        // Se for a linha de "Nenhum membro encontrado", ignora
        if(row.children.length < 2) return;

        const text = row.innerText.toLowerCase();
        
        // Ajuste conforme indices das colunas (0=Nome, 1=Email, 2=Agencia, 3=Funcao)
        // Verifique se a ordem bate com seu HTML
        const agencyCell = row.children[2] ? row.children[2].innerText.toLowerCase() : ''; 
        const roleCell = row.children[3] ? row.children[3].innerText.toLowerCase() : '';

        const matchesSearch = text.includes(search);
        const matchesAgency = agency === '' || agencyCell.includes(agency);
        const matchesRole = role === '' || roleCell.includes(role);

        if (matchesSearch && matchesAgency && matchesRole) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Lógica de Envio do Form
function handleUserSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    
    const url = form.dataset.url;
    
    // Feedback visual no botão
    const btnSubmit = form.querySelector('button[type="submit"]');
    const originalText = btnSubmit.innerHTML;
    btnSubmit.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Salvando...';
    btnSubmit.disabled = true;

    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(res => res.json())
    .then(data => {
        if(data.success || data.status === 'success') { // Aceita ambos os formatos
            if(userModal) userModal.hide();
            
            if(typeof Swal !== 'undefined') {
                Swal.fire({
                    title: "Sucesso!",
                    text: data.message || "Operação realizada com sucesso!",
                    icon: "success",
                    timer: 1500,
                    showConfirmButton: false
                }).then(() => location.reload());
            } else {
                alert(data.message || "Sucesso!");
                location.reload();
            }
        } else {
            // Tratamento de erro
            let errorMsg = data.message || "Erro desconhecido.";
            if(data.errors) {
                // Se o Django mandar erros de validação (JSON)
                errorMsg = JSON.stringify(data.errors);
            }

            if(typeof Swal !== 'undefined') {
                Swal.fire("Erro", errorMsg, "error");
            } else {
                alert("Erro: " + errorMsg);
            }
            
            btnSubmit.innerHTML = originalText;
            btnSubmit.disabled = false;
        }
    })
    .catch(err => {
        console.error(err);
        alert("Erro de conexão com o servidor.");
        btnSubmit.innerHTML = originalText;
        btnSubmit.disabled = false;
    });
}