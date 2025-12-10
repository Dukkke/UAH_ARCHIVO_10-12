<?php echo get_component('default', 'updateCheck') ?>
<?php echo get_component('default', 'privacyMessage') ?>

<?php if ($sf_user->isAdministrator() && (string)QubitSetting::getByName('siteBaseUrl') === ''): ?>
  <div class="site-warning">
    <?php echo link_to(__('Please configure your site base URL'), 'settings/siteInformation', array('rel' => 'home', 'title' => __('Home'))) ?>
  </div>
<?php endif; ?>

<!-- FORZAR ESTILOS UAH - Override completo del tema por defecto -->
<style>
/* === OCULTAR HEADER ORIGINAL DE ATOM === */
#top-bar.original-atom-header { display: none !important; }

/* === NUEVO HEADER UAH === */
.uah-header {
    background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%) !important;
    padding: 0 !important;
    margin: 0 !important;
    position: relative !important;
    z-index: 9000 !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.15) !important;
}

.uah-header-inner {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    padding: 8px 20px !important;
    max-width: 1400px !important;
    margin: 0 auto !important;
    flex-wrap: wrap !important;
}

.uah-logo-section {
    display: flex !important;
    align-items: center !important;
    gap: 15px !important;
}

.uah-logo-section img {
    height: 45px !important;
    width: auto !important;
}

.uah-logo-text {
    color: #ffffff !important;
    font-size: 18px !important;
    font-weight: 400 !important;
    font-family: 'Segoe UI', Arial, sans-serif !important;
    text-decoration: none !important;
}

.uah-logo-text span {
    font-weight: 600 !important;
}

.uah-nav-section {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    flex-wrap: wrap !important;
}

.uah-btn {
    background: #c9a227 !important;
    color: #1a365d !important;
    border: none !important;
    padding: 8px 16px !important;
    border-radius: 4px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    cursor: pointer !important;
    text-decoration: none !important;
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    transition: all 0.2s !important;
}

.uah-btn:hover {
    background: #d4b94c !important;
    transform: translateY(-1px) !important;
}

.uah-btn-secondary {
    background: rgba(255,255,255,0.15) !important;
    color: #ffffff !important;
}

.uah-btn-secondary:hover {
    background: rgba(255,255,255,0.25) !important;
}

.uah-search-box {
    display: flex !important;
    align-items: center !important;
    background: #ffffff !important;
    border-radius: 4px !important;
    overflow: hidden !important;
    min-width: 280px !important;
}

.uah-search-box input {
    border: none !important;
    padding: 10px 14px !important;
    font-size: 14px !important;
    min-width: 200px !important;
    outline: none !important;
}

.uah-search-box button {
    background: #c9a227 !important;
    border: none !important;
    padding: 10px 14px !important;
    color: #1a365d !important;
    cursor: pointer !important;
}

.uah-icons {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}

.uah-icon-btn {
    background: rgba(255,255,255,0.15) !important;
    color: #ffffff !important;
    border: none !important;
    width: 36px !important;
    height: 36px !important;
    border-radius: 50% !important;
    cursor: pointer !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 16px !important;
    text-decoration: none !important;
}

.uah-icon-btn:hover {
    background: rgba(255,255,255,0.25) !important;
}

/* Banner amarillo */
.uah-banner {
    background: linear-gradient(135deg, #c9a227 0%, #d4b94c 100%) !important;
    color: #1a365d !important;
    padding: 10px 20px !important;
    text-align: center !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}

/* Dropdown menu */
.uah-dropdown {
    position: relative !important;
    display: inline-block !important;
}

.uah-dropdown-content {
    display: none;
    position: absolute !important;
    top: 100% !important;
    left: 0 !important;
    background: #ffffff !important;
    min-width: 200px !important;
    box-shadow: 0 8px 30px rgba(0,0,0,0.15) !important;
    border-radius: 8px !important;
    z-index: 9999 !important;
    padding: 8px 0 !important;
    margin-top: 5px !important;
}

.uah-dropdown:hover .uah-dropdown-content,
.uah-dropdown-content.show {
    display: block !important;
}

.uah-dropdown-content a {
    display: block !important;
    padding: 10px 16px !important;
    color: #1a365d !important;
    text-decoration: none !important;
    font-size: 14px !important;
}

.uah-dropdown-content a:hover {
    background: #f0f4f8 !important;
}

/* Login form dropdown */
.uah-login-dropdown {
    padding: 16px !important;
    min-width: 250px !important;
}

.uah-login-dropdown h4 {
    margin: 0 0 12px 0 !important;
    color: #1a365d !important;
    font-size: 14px !important;
}

.uah-login-dropdown input {
    width: 100% !important;
    padding: 10px !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 4px !important;
    margin-bottom: 10px !important;
    font-size: 14px !important;
    box-sizing: border-box !important;
}

.uah-login-dropdown button {
    width: 100% !important;
}

/* Ocultar elementos originales de AtoM */
#top-bar:not(.uah-header) {
    display: none !important;
}
</style>

<!-- NUEVO HEADER UAH PERSONALIZADO -->
<header class="uah-header">
    <div class="uah-header-inner">
        <!-- Logo y título -->
        <div class="uah-logo-section">
            <a href="<?php echo url_for('@homepage') ?>">
                <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIwIiBoZWlnaHQ9IjQ1IiB2aWV3Qm94PSIwIDAgMTIwIDQ1IiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjx0ZXh0IHg9IjUiIHk9IjMwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMjQiIGZvbnQtd2VpZ2h0PSJib2xkIiBmaWxsPSIjZmZmZmZmIj51YWg8L3RleHQ+PHRleHQgeD0iNTUiIHk9IjIwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iOCIgZmlsbD0iI2ZmZmZmZiI+VW5pdmVyc2lkYWQ8L3RleHQ+PHRleHQgeD0iNTUiIHk9IjMwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iOCIgZmlsbD0iI2ZmZmZmZiI+QWxiZXJ0byBIdXJ0YWRvPC90ZXh0Pjwvc3ZnPg==" alt="UAH">
            </a>
            <a href="<?php echo url_for('@homepage') ?>" class="uah-logo-text">
                <span>Archivo Patrimonial</span>
            </a>
        </div>

        <!-- Navegación -->
        <div class="uah-nav-section">
            <!-- Menú Navegar -->
            <div class="uah-dropdown">
                <button class="uah-btn" onclick="this.nextElementSibling.classList.toggle('show')">
                    Navegar ▼
                </button>
                <div class="uah-dropdown-content">
                    <a href="<?php echo url_for('informationobject/browse') ?>">Fondos</a>
                    <a href="<?php echo url_for('taxonomy/index?id=35') ?>">Materias</a>
                    <a href="<?php echo url_for('taxonomy/index?id=42') ?>">Lugares</a>
                    <a href="<?php echo url_for('actor/browse') ?>">Registro de autoridad</a>
                    <a href="<?php echo url_for('repository/browse') ?>">Instituciones archivísticas</a>
                    <a href="<?php echo url_for('informationobject/browse?onlyMedia=1') ?>">Objetos digitales</a>
                </div>
            </div>

            <!-- Configuración -->
            <button class="uah-btn uah-btn-secondary" title="Configuración">⚙</button>

            <!-- Búsqueda -->
            <form class="uah-search-box" action="<?php echo url_for('informationobject/browse') ?>" method="get">
                <input type="text" name="query" placeholder="Búsqueda Global">
                <button type="submit">🔍</button>
            </form>

            <!-- Iconos -->
            <div class="uah-icons">
                <a href="<?php echo url_for('clipboard/view') ?>" class="uah-icon-btn" title="Clipboard">📎</a>
                <a href="#" class="uah-icon-btn" title="Accesibilidad">♿</a>
                <a href="#" class="uah-icon-btn" title="Info">ℹ</a>
            </div>

            <!-- Login -->
            <div class="uah-dropdown">
                <button class="uah-btn" onclick="this.nextElementSibling.classList.toggle('show')">
                    Iniciar sesión ▼
                </button>
                <div class="uah-dropdown-content uah-login-dropdown">
                    <h4>¿Estás registrado?</h4>
                    <form action="<?php echo url_for('user/login') ?>" method="post">
                        <input type="text" name="email" placeholder="Correo electrónico">
                        <input type="password" name="password" placeholder="Contraseña">
                        <button type="submit" class="uah-btn">Iniciar sesión</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</header>

<!-- Banner amarillo -->
<div class="uah-banner">
    A través de este portal usted puede buscar documentos, imágenes, u otros documentos digitalizados, pudiendo buscar aquella información que es de su interés.
</div>

<?php echo get_component_slot('header') ?>

<!-- ===== CHATBOT ARCHIVO PATRIMONIAL ===== -->
<style>
:root {
    --chatbot-primary: #1a365d;
    --chatbot-primary-light: #2c5282;
    --chatbot-accent: #c9a227;
    --chatbot-white: #ffffff;
    --chatbot-border: #e2e8f0;
    --chatbot-text-dark: #1a202c;
    --chatbot-text-muted: #64748b;
    --chatbot-shadow-lg: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

#chatbot-container {
    display: none;
    position: fixed;
    bottom: 100px;
    right: 30px;
    width: 380px;
    height: 520px;
    background: var(--chatbot-white);
    border-radius: 24px;
    box-shadow: var(--chatbot-shadow-lg);
    z-index: 10000;
    overflow: hidden;
    animation: chatbotSlideUp 0.4s ease;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

@keyframes chatbotSlideUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}

#chatbot-header {
    background: linear-gradient(135deg, var(--chatbot-primary) 0%, var(--chatbot-primary-light) 100%);
    color: var(--chatbot-white);
    padding: 20px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: move;
}

.chatbot-title { display: flex; align-items: center; gap: 12px; }
.chatbot-avatar { width: 40px; height: 40px; background: rgba(255,255,255,0.2); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
.chatbot-info h3 { font-size: 1rem; font-weight: 600; margin: 0 0 2px 0; }
.chatbot-info span { font-size: 0.75rem; opacity: 0.8; }
.online-dot { width: 8px; height: 8px; background: #22c55e; border-radius: 50%; display: inline-block; margin-right: 6px; animation: pulse 2s infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

#chatbot-close { background: rgba(255,255,255,0.15); border: none; color: var(--chatbot-white); font-size: 20px; cursor: pointer; width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; }
#chatbot-close:hover { background: rgba(255,255,255,0.25); }

#chatbot-messages { height: 340px; overflow-y: auto; padding: 20px; background: #f8fafc; display: flex; flex-direction: column; gap: 16px; }
#chatbot-input { padding: 16px 20px; border-top: 1px solid var(--chatbot-border); display: flex; gap: 12px; background: var(--chatbot-white); }
#chatbot-user-input { flex: 1; padding: 14px 18px; border: 2px solid var(--chatbot-border); border-radius: 14px; font-size: 15px; background: #f8fafc; }
#chatbot-user-input:focus { outline: none; border-color: var(--chatbot-primary); background: var(--chatbot-white); }
#chatbot-send { padding: 14px 20px; background: linear-gradient(135deg, var(--chatbot-primary) 0%, var(--chatbot-primary-light) 100%); color: var(--chatbot-white); border: none; border-radius: 14px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
#chatbot-send:hover { transform: scale(1.05); }
#chatbot-send:disabled { background: var(--chatbot-border); cursor: not-allowed; }

#chatbot-icon { position: fixed; bottom: 30px; right: 30px; width: 64px; height: 64px; background: linear-gradient(135deg, var(--chatbot-primary) 0%, var(--chatbot-primary-light) 100%); border-radius: 20px; cursor: pointer; z-index: 9999; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 30px rgba(26,54,93,0.35); transition: all 0.3s ease; }
#chatbot-icon:hover { transform: scale(1.1) rotate(-5deg); }
#chatbot-icon svg { width: 28px; height: 28px; color: var(--chatbot-white); }

.message { max-width: 85%; padding: 14px 18px; border-radius: 18px; font-size: 14px; line-height: 1.5; }
.user-message { background: linear-gradient(135deg, var(--chatbot-primary) 0%, var(--chatbot-primary-light) 100%); color: var(--chatbot-white); align-self: flex-end; border-bottom-right-radius: 6px; }
.bot-message { background: var(--chatbot-white); color: var(--chatbot-text-dark); border: 1px solid var(--chatbot-border); align-self: flex-start; max-width: 95%; }
.bot-message a { color: var(--chatbot-primary); text-decoration: none; font-weight: 600; }
.loading { color: var(--chatbot-text-muted); align-self: flex-start; display: flex; align-items: center; gap: 12px; background: var(--chatbot-white); padding: 14px 18px; border-radius: 18px; border: 1px solid var(--chatbot-border); }
.typing-indicator { display: flex; gap: 4px; }
.typing-indicator span { width: 8px; height: 8px; background: var(--chatbot-primary); border-radius: 50%; animation: bounce 1.4s infinite ease-in-out; }
.typing-indicator span:nth-child(1) { animation-delay: 0s; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; } 40% { transform: scale(1); opacity: 1; } }
.error-message { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; align-self: flex-start; }

.welcome-container { text-align: center; padding: 30px 20px; }
.welcome-emoji { font-size: 48px; margin-bottom: 16px; }
.welcome-text { color: var(--chatbot-text-dark); font-size: 15px; font-weight: 500; margin-bottom: 8px; }
.welcome-subtitle { color: var(--chatbot-text-muted); font-size: 13px; }

.folder-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 16px; }
.folder-btn { display: flex; flex-direction: column; align-items: center; justify-content: center; background: linear-gradient(145deg, var(--chatbot-white) 0%, #f8fafc 100%); border: 2px solid var(--chatbot-border); border-radius: 16px; padding: 16px 10px; cursor: pointer; transition: all 0.3s; }
.folder-btn:hover { border-color: var(--chatbot-primary); transform: translateY(-4px); box-shadow: 0 8px 25px rgba(26,54,93,0.15); }
.folder-icon { font-size: 28px; margin-bottom: 6px; }
.folder-label { font-size: 12px; font-weight: 600; color: var(--chatbot-primary); margin-bottom: 2px; }
.folder-count { font-size: 10px; color: var(--chatbot-text-muted); }

#categories-modal { display: none; position: absolute; top: 80px; left: 10px; right: 10px; bottom: 70px; background: var(--chatbot-white); border-radius: 16px; box-shadow: var(--chatbot-shadow-lg); z-index: 100; overflow: hidden; }
.modal-header { background: linear-gradient(135deg, var(--chatbot-accent) 0%, #d4b94c 100%); color: var(--chatbot-primary); padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; }
.modal-header h4 { font-size: 15px; font-weight: 600; margin: 0; }
.modal-close { background: rgba(0,0,0,0.1); border: none; width: 28px; height: 28px; border-radius: 8px; cursor: pointer; font-size: 16px; color: var(--chatbot-primary); }
.category-tabs { display: flex; border-bottom: 1px solid var(--chatbot-border); background: #f8fafc; }
.category-tab { flex: 1; padding: 12px 8px; border: none; background: transparent; cursor: pointer; font-size: 12px; font-weight: 500; color: var(--chatbot-text-muted); }
.category-tab:hover { color: var(--chatbot-primary); }
.category-tab.active { color: var(--chatbot-primary); border-bottom: 2px solid var(--chatbot-primary); background: var(--chatbot-white); }
.category-search { padding: 8px 12px; background: #f8fafc; border-bottom: 1px solid var(--chatbot-border); }
.category-search input { width: 100%; padding: 10px 14px; border: 1px solid var(--chatbot-border); border-radius: 10px; font-size: 13px; box-sizing: border-box; }
.category-search input:focus { border-color: var(--chatbot-primary); outline: none; }
.category-list { height: calc(100% - 155px); overflow-y: auto; padding: 12px; }
.category-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 14px; border: 1px solid var(--chatbot-border); border-radius: 10px; margin-bottom: 8px; cursor: pointer; background: var(--chatbot-white); }
.category-item:hover { border-color: var(--chatbot-primary); transform: translateX(4px); }
.category-item .name { font-size: 13px; color: var(--chatbot-text-dark); font-weight: 500; }
.category-item .count { font-size: 11px; color: var(--chatbot-white); background: var(--chatbot-primary); padding: 2px 8px; border-radius: 10px; }
.back-button { display: flex; align-items: center; justify-content: center; gap: 6px; background: transparent; border: 2px solid var(--chatbot-border); padding: 10px 20px; border-radius: 20px; font-size: 13px; color: var(--chatbot-text-muted); cursor: pointer; margin: 16px auto 0; }
.back-button:hover { background: var(--chatbot-primary); color: var(--chatbot-white); border-color: var(--chatbot-primary); }
.back-button svg { width: 16px; height: 16px; }
@media (max-width: 480px) { #chatbot-container { width: calc(100% - 20px); right: 10px; bottom: 80px; height: 70vh; } #chatbot-icon { right: 20px; bottom: 20px; } }
</style>

<div id="chatbot-container">
    <div id="chatbot-header">
        <div class="chatbot-title">
            <div class="chatbot-avatar">📚</div>
            <div class="chatbot-info">
                <h3>Archivo Patrimonial</h3>
                <span><span class="online-dot"></span>Asistente disponible</span>
            </div>
        </div>
        <button id="chatbot-close">✕</button>
    </div>
    <div id="chatbot-messages">
        <div class="welcome-container">
            <div class="welcome-emoji">👋</div>
            <p class="welcome-text">¡Hola! Soy tu asistente del Archivo Patrimonial</p>
            <p class="welcome-subtitle">Explora por categoría:</p>
            <div class="folder-grid">
                <button class="folder-btn" onclick="openCategoriesWithTab('materias')"><span class="folder-icon">📚</span><span class="folder-label">Materias</span><span class="folder-count">2644</span></button>
                <button class="folder-btn" onclick="openCategoriesWithTab('autores')"><span class="folder-icon">👤</span><span class="folder-label">Autores</span><span class="folder-count">3191</span></button>
                <button class="folder-btn" onclick="openCategoriesWithTab('lugares')"><span class="folder-icon">📍</span><span class="folder-label">Lugares</span><span class="folder-count">561</span></button>
            </div>
            <p style="font-size:11px; color:var(--chatbot-text-muted); margin-top:12px;">O escribe tu búsqueda abajo ⬇️</p>
        </div>
    </div>
    <div id="categories-modal">
        <div class="modal-header"><h4>📂 Explorar Categorías</h4><button class="modal-close" id="close-categories">✕</button></div>
        <div class="category-tabs"><button class="category-tab active" data-tab="materias">📚 Materias</button><button class="category-tab" data-tab="autores">👤 Autores</button><button class="category-tab" data-tab="lugares">📍 Lugares</button></div>
        <div class="category-search"><input type="text" id="category-search-input" placeholder="🔍 Buscar..." autocomplete="off"></div>
        <div class="category-list" id="category-list"><p style="text-align:center; padding: 20px;">Cargando...</p></div>
    </div>
    <div id="chatbot-input">
        <input type="text" id="chatbot-user-input" placeholder="Escribe tu pregunta...">
        <button id="chatbot-send"><svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/></svg></button>
    </div>
</div>

<div id="chatbot-icon"><svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg></div>

<script>
// Cerrar dropdowns al hacer click fuera
document.addEventListener('click', function(e) {
    if (!e.target.closest('.uah-dropdown')) {
        document.querySelectorAll('.uah-dropdown-content').forEach(d => d.classList.remove('show'));
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const chatbotIcon = document.getElementById('chatbot-icon');
    const chatbotContainer = document.getElementById('chatbot-container');
    const chatbotClose = document.getElementById('chatbot-close');
    const chatbotSend = document.getElementById('chatbot-send');
    const chatbotInput = document.getElementById('chatbot-user-input');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const API_BASE = '/api';

    chatbotIcon.addEventListener('click', () => { chatbotContainer.style.display = 'block'; chatbotIcon.style.display = 'none'; chatbotInput.focus(); });
    chatbotClose.addEventListener('click', () => { chatbotContainer.style.display = 'none'; chatbotIcon.style.display = 'flex'; });

    function sendMessage() {
        const message = chatbotInput.value.trim();
        if (!message) return;
        const welcome = document.querySelector('.welcome-container'); if (welcome) welcome.remove();
        addMessage(message, 'user'); chatbotInput.value = ''; chatbotSend.disabled = true; chatbotInput.disabled = true;
        const loading = document.createElement('div'); loading.className = 'message loading'; loading.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div><span>Escribiendo...</span>'; chatbotMessages.appendChild(loading); chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
        fetch(API_BASE + '/chat', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({query: message}) })
        .then(r => r.json()).then(data => { loading.remove(); addMessage(data.response || 'No pude procesar tu consulta.', 'bot', true); })
        .catch(e => { loading.remove(); addMessage('Error: ' + e.message, 'error'); })
        .finally(() => { chatbotSend.disabled = false; chatbotInput.disabled = false; chatbotInput.focus(); });
    }

    function addMessage(text, type, isHtml = false) {
        const div = document.createElement('div'); div.className = 'message ' + (type === 'user' ? 'user-message' : type === 'error' ? 'error-message' : 'bot-message');
        if (isHtml) { div.innerHTML = text; div.querySelectorAll('a').forEach(a => a.target = '_blank'); } else { div.textContent = text; }
        chatbotMessages.appendChild(div);
        if (type === 'bot') { chatbotMessages.scrollTop = div.offsetTop - chatbotMessages.offsetTop; addBackButton(); } else { chatbotMessages.scrollTop = chatbotMessages.scrollHeight; }
        return div;
    }

    function addBackButton() {
        const existing = document.querySelector('.back-button'); if (existing) existing.remove();
        const btn = document.createElement('button'); btn.className = 'back-button'; btn.innerHTML = '<svg fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg> Volver al inicio'; btn.onclick = resetChat; chatbotMessages.appendChild(btn);
    }

    function resetChat() {
        chatbotMessages.innerHTML = '<div class="welcome-container"><div class="welcome-emoji">👋</div><p class="welcome-text">¡Hola! Soy tu asistente del Archivo Patrimonial</p><p class="welcome-subtitle">Explora por categoría:</p><div class="folder-grid"><button class="folder-btn" onclick="openCategoriesWithTab(\'materias\')"><span class="folder-icon">📚</span><span class="folder-label">Materias</span><span class="folder-count">2644</span></button><button class="folder-btn" onclick="openCategoriesWithTab(\'autores\')"><span class="folder-icon">👤</span><span class="folder-label">Autores</span><span class="folder-count">3191</span></button><button class="folder-btn" onclick="openCategoriesWithTab(\'lugares\')"><span class="folder-icon">📍</span><span class="folder-label">Lugares</span><span class="folder-count">561</span></button></div><p style="font-size:11px; color:var(--chatbot-text-muted); margin-top:12px;">O escribe tu búsqueda abajo ⬇️</p></div>';
        chatbotInput.focus();
    }

    const modal = document.getElementById('categories-modal');
    const closeModal = document.getElementById('close-categories');
    const catList = document.getElementById('category-list');
    const tabs = document.querySelectorAll('.category-tab');
    let catData = null, curTab = 'materias';

    window.openCategoriesWithTab = function(tab) {
        curTab = tab; tabs.forEach(t => { t.classList.remove('active'); if (t.dataset.tab === tab) t.classList.add('active'); });
        modal.style.display = 'block';
        if (!catData) loadCategories(); else renderCategories(curTab);
    };
    closeModal.addEventListener('click', () => modal.style.display = 'none');

    async function loadCategories() {
        try { catList.innerHTML = '<p style="text-align:center;padding:20px;">Cargando...</p>'; const r = await fetch(API_BASE + '/categories'); const data = await r.json(); if (data.success) { catData = data.categories; renderCategories(curTab); } }
        catch (e) { catList.innerHTML = '<p style="text-align:center;color:#dc2626;padding:20px;">Error de conexión</p>'; }
    }

    function renderCategories(tab, filter = '') {
        let items = catData[tab] || []; if (filter) items = items.filter(i => i.name.toLowerCase().includes(filter.toLowerCase()));
        if (!items.length) { catList.innerHTML = '<p style="text-align:center;padding:20px;">Sin resultados</p>'; return; }
        catList.innerHTML = items.map(i => '<div class="category-item" data-type="' + tab + '" data-name="' + i.name + '"><span class="name">' + i.name + '</span><span class="count">' + i.count + '</span></div>').join('');
        catList.querySelectorAll('.category-item').forEach(el => el.onclick = () => searchByCategory(el.dataset.type, el.dataset.name));
    }

    async function searchByCategory(type, name) {
        modal.style.display = 'none'; const welcome = document.querySelector('.welcome-container'); if (welcome) welcome.remove();
        addMessage('Buscar en ' + type + ': ' + name, 'user'); chatbotSend.disabled = true; chatbotInput.disabled = true;
        const loading = addMessage('Buscando...', 'loading');
        try { const r = await fetch(API_BASE + '/search-by-category', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({category_type: type, category_name: name}) }); const data = await r.json(); loading.remove();
            if (data.success && data.results.length) { let html = '<p><strong>📂 ' + name + '</strong> (' + data.count + ' docs)</p><br>'; data.results.forEach((d, i) => html += '<div style="margin-bottom:12px;"><strong>' + (i+1) + '. ' + d.title + '</strong><br><a href="' + d.href + '">📄 Ver</a></div>'); addMessage(html, 'bot', true); } else { addMessage('No se encontraron documentos.', 'bot'); }
        } catch (e) { loading.remove(); addMessage('Error: ' + e.message, 'error'); } finally { chatbotSend.disabled = false; chatbotInput.disabled = false; }
    }

    tabs.forEach(t => t.onclick = function() { tabs.forEach(x => x.classList.remove('active')); this.classList.add('active'); curTab = this.dataset.tab; document.getElementById('category-search-input').value = ''; renderCategories(curTab); });
    document.getElementById('category-search-input').oninput = function() { if (catData) renderCategories(curTab, this.value.trim()); };
    chatbotSend.onclick = sendMessage;
    chatbotInput.onkeypress = e => { if (e.key === 'Enter' && !chatbotSend.disabled) sendMessage(); };

    let drag = false, ox, oy;
    document.getElementById('chatbot-header').onmousedown = function(e) { if (e.target.id === 'chatbot-close') return; drag = true; ox = e.clientX - chatbotContainer.offsetLeft; oy = e.clientY - chatbotContainer.offsetTop; chatbotContainer.style.position = 'fixed'; chatbotContainer.style.right = 'auto'; chatbotContainer.style.bottom = 'auto'; };
    document.onmousemove = e => { if (drag) { chatbotContainer.style.left = Math.max(0, Math.min(e.clientX - ox, innerWidth - chatbotContainer.offsetWidth)) + 'px'; chatbotContainer.style.top = Math.max(0, Math.min(e.clientY - oy, innerHeight - chatbotContainer.offsetHeight)) + 'px'; } };
    document.onmouseup = () => drag = false;
});
</script>