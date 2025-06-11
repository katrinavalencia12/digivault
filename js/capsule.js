// Elements
const content = document.getElementById("content");
const overlay = document.getElementById("overlay");
const viewButton = document.getElementById("view");


const modal = document.getElementById("modal");
const media = document.getElementById("media");
const desc = document.getElementById("desc");
const metadata = document.getElementById("metadata");
const download = document.getElementById("download");
const closeButton = document.getElementById("close");

const contentArr = Array.from(content.children);

// This applies the "visible" class to make items fade in
const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        if (entry.isIntersecting && !entry.target.classList.contains("visible")) {
            entry.target.classList.add("visible");
        } else {
            if (entry.target.classList.contains("visible")) {
                entry.target.classList.remove("visible");
            }
        }
    });
});

contentArr.forEach((node, index) => {
    // Apply the center to the firstItem
    if (index == 0) node.classList.add("in-center");

    // Apply random rotation
    node.style.transform = `rotate(${(index % 2 == 0 ? -1 : 1) * Math.max(5, Math.random() * 12)}deg)`;

    // Observe each node
    observer.observe(node)
});

// Functions

function openModal(element) {    
    // Change content
    media.innerHTML = element.firstChild.outerHTML;
    desc.innerText = element.lastChild.innerText.trim() == "" ? "No description available." : (element.lastChild.innerText.charAt(0).toUpperCase() + element.lastChild.innerText.substring(1));
    
    // Metadata display
    var data = JSON.parse(element.dataset.metadata);
    metadata.innerHTML = "";

    if (Object.keys(data) == 0) {
        metadata.innerHTML += "<p>No metadata available.</p>";
    } else {
        for (const [key, value] of Object.entries(data)) {
            metadata.innerHTML += `<p class="data"><span>${key}:</span>${value}</p>`;
        }
    }

    // Open modal
    modal.classList.remove("closed");
    modal.classList.add("active");
}

function close() {
    modal.classList.remove("active");
    modal.classList.add("closed");
}

// Event Listeners

content.addEventListener("wheel", function(e) {
    content.scrollBy(e.deltaY, 0);
});

// Grows the item in the center
content.addEventListener("scroll", function(e) {
    const viewportCenter = window.innerWidth / 2;
    let closestElement = null;
    let minDistance = Infinity;

    contentArr.forEach(element => {
        // Calculations
        const rect = element.getBoundingClientRect();
        const imageCenter = rect.left + (rect.width / 2);
        const distance = Math.abs(viewportCenter - imageCenter);

        // Change image if its closest
        if (distance < minDistance) {
            minDistance = distance;
            closestElement = element;
        }

        // Remove in center
        if (element.classList.contains("in-center")) {
            element.classList.remove("in-center");
        }
    });

    // Apply new style
    if (closestElement) {
        closestElement.classList.add("in-center");
    }
});

content.addEventListener("click", function(e) {
    if (e.target.classList.contains("in-center")) {
        openModal(e.target);
    }
});

viewButton.addEventListener("click", function() {
    overlay.classList.add("hidden");
    contentArr.forEach((node, index) => {
        node.style.animation = `popIn 1s forwards`;
        node.style.animationDelay = `${index * 0.1}s`;
    })
});

closeButton.addEventListener("click", close);
modal.addEventListener("click", function(e) {
    if (e.target == modal) close();
});