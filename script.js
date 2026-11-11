// Smart Traffic Violation Logger - Obsidian Dark Interactive Engine

document.addEventListener('DOMContentLoaded', function () {
    // 1. Create Glowing Blue Pointer Follower
    const cursorDot = document.createElement('div');
    cursorDot.className = 'cursor-dot no-print';
    const cursorGlow = document.createElement('div');
    cursorGlow.className = 'cursor-glow no-print';
    document.body.appendChild(cursorDot);
    document.body.appendChild(cursorGlow);

    let mouseX = window.innerWidth / 2;
    let mouseY = window.innerHeight / 2;
    let glowX = mouseX;
    let glowY = mouseY;

    window.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
        cursorDot.style.left = ${mouseX}px;
        cursorDot.style.top = ${mouseY}px;
    });

    // Smooth trailing animation for cursor glow
    function animateCursor() {
        glowX += (mouseX - glowX) * 0.18;
        glowY += (mouseY - glowY) * 0.18;
        cursorGlow.style.left = ${glowX}px;
        cursorGlow.style.top = ${glowY}px;
        requestAnimationFrame(animateCursor);
    }
    requestAnimationFrame(animateCursor);

    // Enlarge glow on clickable interactive elements
    const interactiveElements = document.querySelectorAll('a, button, input, select, .vehicle-plate-modern, .stat-card-modern, .card-modern');
    interactiveElements.forEach((el) => {
        el.addEventListener('mouseenter', () => cursorGlow.classList.add('hovering'));
        el.addEventListener('mouseleave', () => cursorGlow.classList.remove('hovering'));
    });

    // 2. Interactive Vehicle Registration Formatter
    const vehicleInputs = document.querySelectorAll('.vehicle-input');
    vehicleInputs.forEach(input => {
        input.addEventListener('input', function () {
            let formatted = this.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
            if (formatted.length > 12) formatted = formatted.substring(0, 12);
            this.value = formatted;
        });
    });

    // 3. Initialize Bootstrap Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 4. Auto dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            try {
                bsAlert.close();
            } catch (e) {}
        }, 5000);
    });
});

// Print Challan Trigger
function printChallan() {
    window.print();
}
