document.addEventListener('DOMContentLoaded', () => {

    // =========================================================
    // 1. DYNAMIC RISK CLASS ASSIGNMENT (New Logic)
    //    Reads the percentage and applies 'low-risk', 'medium-risk', or 'high-risk' class.
    // =========================================================
    
    const notificationCards = document.querySelectorAll('.notification-card');

    notificationCards.forEach(card => {
        const spoilageElement = card.querySelector('.spoilage-risk');
        
        if (spoilageElement && spoilageElement.textContent) {
            
            // Regex to find the number before the '%' sign
            const textContent = spoilageElement.textContent;
            const match = textContent.match(/(\d+)%/); 
            
            if (match) {
                const spoilagePercent = parseInt(match[1]);
                let riskClass = '';
                
                // --- DEFINITION OF THE DYNAMIC RANGES (0-10, 11-39, 40+) ---
                if (spoilagePercent <= 10) {
                    riskClass = 'low-risk';
                } 
                else if (spoilagePercent <= 39) { 
                    // Medium Risk: 11% to 39%
                    riskClass = 'medium-risk';
                } 
                else {
                    // High Risk: 40% and above
                    riskClass = 'high-risk';
                }
                
                // Remove existing risk classes and apply the new one
                card.classList.remove('low-risk', 'medium-risk', 'high-risk', 'placeholder-card');
                card.classList.add(riskClass);
            }
        }
    });
    
    // --- (Optional: Click handler for 'selected' state) ---
    notificationCards.forEach(card => {
        card.addEventListener('click', () => {
            // Remove 'selected' from all other cards
            notificationCards.forEach(c => c.classList.remove('selected'));
            // Add 'selected' to the clicked card
            card.classList.add('selected');
        });
    });


    // =========================================================
    // 2. IMAGE ROTATION LOGIC (Existing Code, integrated)
    // =========================================================

    const imageElement = document.getElementById('rotatingImage');
    const dots = document.querySelectorAll('.image-dots .dot');

    // Ensure imageElement and dots are found before proceeding
    if (!imageElement || dots.length === 0) {
        console.warn("Image rotation elements not found. Skipping rotation logic.");
        return; // Exit if elements are missing
    }

    const images = [
        "../images/maize.png",
        "../images/farmer.jpeg", 
        "../images/cornnn.jpeg", 
        "../images/corn_damaged.jpg" 
    ];

    let currentIndex = 0;

    function rotateImage() {
        // Update image source
        currentIndex = (currentIndex + 1) % images.length;
        imageElement.src = images[currentIndex];
        imageElement.alt = `Close-up of corn storage ${currentIndex + 1}`;
        
        // Update dots
        dots.forEach((dot, index) => {
            dot.classList.remove('active');
            if (index === currentIndex) {
                dot.classList.add('active');
            }
        });
    }

    // Start the rotation: change image every 3000 milliseconds (3 seconds)
    // We start the interval after the DOM is fully loaded.
    setInterval(rotateImage, 3000);
});