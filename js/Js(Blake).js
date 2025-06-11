// Dashboard Capsule Countdown + Delete Renderer
document.addEventListener("DOMContentLoaded", () => {
    const capsuleDisplay = document.getElementById("capsuleDisplay");
    const capsuleList = document.getElementById("capsuleList");
    const tipText = document.getElementById("tip");
    const badgeContainer = document.getElementById("fiveCapsuleBadge"); // Badge container placeholder div
    const firstBadgeContainer = document.getElementById("firstCapsuleBadge"); // New badge container for first capsule

    // Format a date in MM/DD/YYYY format
    function formatDate(isoDate) {
        const date = new Date(isoDate);
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        const year = date.getFullYear();
        return `${month}/${day}/${year}`;
    }

    // Check and show or hide the tip message
    function tipCheck() {
        if (capsuleList && capsuleList.children.length === 0 && tipText) {
            tipText.style.display = "block";
        } else if (tipText) {
            tipText.style.display = "none";
        }
    }

    // Only run if capsules are defined and valid
    if (typeof capsules !== "undefined" && Array.isArray(capsules) && capsuleList) {

        //  If user has uploaded 5 or more capsules, show badge
        const badgeEarned = capsules.length >= 5;
        if (badgeEarned && badgeContainer) {
            const badgeElement = document.createElement("div");
            badgeElement.classList.add("badge");
            badgeElement.innerHTML = `
                <img src="/static/svg/fiveCapsuleBadge.png" alt="Five Capsule Badge">
                <div class="badge-content">
                    <p class="badge-text">Thank you for creating 5 time capsules!</p>
                </div>
            `;
            badgeContainer.appendChild(badgeElement);
        }

        // If user has uploaded at least one capsule and earned the first badge
        if (typeof badgeEarnedFirst !== "undefined" && badgeEarnedFirst && firstBadgeContainer) {
            const firstBadgeElement = document.createElement("div");
            firstBadgeElement.classList.add("badge");
            firstBadgeElement.innerHTML = `
                <img src="/static/svg/firstCapsuleBadge.png" alt="First Capsule Badge">
                <div class="badge-content">
                    <p class="badge-text">Congrats on sending your first time capsule!</p>
                </div>
            `;
            firstBadgeContainer.appendChild(firstBadgeElement);
        }

        // Handles countdown logic and updates UI every second
        function updateCountdown(sendAt, element, successText) {
            function render() {
                const now = new Date();
                const target = new Date(sendAt);
                const diff = target - now;

                if (isNaN(target.getTime())) {
                    element.innerHTML = "⛔ Invalid delivery time.";
                    clearInterval(timer);
                    return;
                }

                if (diff <= 0) {
                    element.innerHTML = `<strong>${successText}</strong>`;
                    clearInterval(timer);
                    return;
                }

                const seconds = Math.floor((diff / 1000) % 60);
                const minutes = Math.floor((diff / (1000 * 60)) % 60);
                const hours = Math.floor((diff / (1000 * 60 * 60)) % 24);
                const days = Math.floor(diff / (1000 * 60 * 60 * 24));
                element.innerHTML = `${days}d ${hours}h ${minutes}m ${seconds}s`;
            }

            render();
            const timer = setInterval(render, 1000);
        }

        // Render each capsule in the dashboard
        let i = 0;
        capsules.forEach(capsule => {
            const filePaths = capsule.file_path || [];
            const filenames = filePaths.map(path => path.split("/").pop()).join(", ");
            const recipient = capsule.email;
            const name = capsule.name;

            const capsuleCard = document.createElement("div");
            capsuleCard.className = "capsule-card";
            capsuleCard.style.animationDelay = `${i * 0.3}s`;

            const capsuleRow1 = document.createElement("div");
            capsuleRow1.className = "capsule-row";

            const title = document.createElement("h4");
            title.textContent = name;
            capsuleRow1.appendChild(title);

            const deleteButton = document.createElement("a");
            deleteButton.className = "delete-button";
            deleteButton.innerHTML = "&#10005;";
            capsuleRow1.appendChild(deleteButton);
            capsuleCard.appendChild(capsuleRow1);

            // Add delete button logic
            deleteButton.addEventListener("click", async () => {
                const confirmed = confirm("Are you sure you want to delete this time capsule?");
                if (!confirmed) return;

                try {
                    const res = await fetch("/delete_capsule", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ job_id: capsule.job_id })
                    });

                    const result = await res.json();
                    if (res.ok) {
                        alert(result.message || "Capsule deleted.");
                        capsuleCard.remove();
                        tipCheck(); // Check if we need to show the tip
                    } else {
                        alert("Error: " + (result.error || "Unknown error"));
                    }

                } catch (err) {
                    console.error(err);
                    alert("Something went wrong. Try again.");
                }
            });

            const capsuleRow2 = document.createElement("div");
            capsuleRow2.className = "capsule-row";

            const fileCountLabel = document.createElement("p");
            fileCountLabel.textContent = "File Count:";
            capsuleRow2.appendChild(fileCountLabel);

            const fileCountValue = document.createElement("p");
            fileCountValue.textContent = filePaths.length;
            capsuleRow2.appendChild(fileCountValue);
            capsuleCard.appendChild(capsuleRow2);

            const capsuleRow3 = document.createElement("div");
            capsuleRow3.className = "capsule-row";

            const unlockDateLabel = document.createElement("p");
            unlockDateLabel.textContent = "Unlock Date:";
            capsuleRow3.appendChild(unlockDateLabel);

            const unlockDateValue = document.createElement("p");
            unlockDateValue.textContent = formatDate(capsule.timestamp);
            capsuleRow3.appendChild(unlockDateValue);
            capsuleCard.appendChild(capsuleRow3);

            const capsuleRow4 = document.createElement("div");
            capsuleRow4.className = "capsule-row";

            const countdownLabel = document.createElement("p");
            countdownLabel.textContent = "Countdown:";
            capsuleRow4.appendChild(countdownLabel);

            const countdownValue = document.createElement("p");
            capsuleRow4.appendChild(countdownValue);
            capsuleCard.appendChild(capsuleRow4);

            updateCountdown(capsule.timestamp, countdownValue, `✅ Delivered to ${recipient}`);

            capsuleList.appendChild(capsuleCard);
            i++;
        });
    }

});

