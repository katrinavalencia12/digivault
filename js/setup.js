/* 
=====================
    HTML ELEMENTS
=====================
*/
const files = document.getElementById("files");
const date = document.getElementById("date");
const totalDisplay = document.getElementById("total");
const fileButton = document.getElementById("fileButton");
const fileDisplay = document.getElementById("fileDisplay");
const fileHolder = document.getElementById("fileHolder");
const tipText = document.getElementById("tipText");
const fileOverlay = document.getElementById("fileOverlay")
const uploadForm = document.getElementById("uploadForm");

const messageModal = document.getElementById("messageModal");
const closeButton = document.getElementById("closeButton");
const saveMessageButton = document.getElementById("saveMessageButton");
const recipientsButton = document.getElementById("recipientsButton");
const fileMessage = document.getElementById("fileMessage");

const recipientModal = document.getElementById("recipientModal");
const saveRecipientButton = document.getElementById("saveRecipientButton");
const recipients = document.getElementById("recipients");

/* 
=====================
 IMPORTANT VARIABLES
=====================
*/

var fileList = new DataTransfer();
var messageList = new Map();
var recipientList = [];
var currentFileIndex = null;

/* 
=====================
      FUNCTIONS
=====================
*/

function updateDisplay() {
    // Clear the display before updating
    var totalSize = 0;
    fileHolder.innerHTML = "";

    // Check size and reset
    if (fileList.files.length == 0) {
        tipText.style.display = "block";
        totalDisplay.innerHTML = "0 / 1000 MB";
        return;
    } else {
        tipText.style.display = "none";
    }

    // Obtain array
    var fileArr = Array.from(fileList.files);

    fileArr.forEach((file, index) => {
        // Total file size calculation
        var calc = (file.size / (1024 * 1024));
        totalSize += calc;

        // Create new file element
        var fileElement = document.createElement("div");
        fileElement.className = "file";
        fileElement.dataset.index = index; 

        // Create message button
        var messageButton = document.createElement("button");
        messageButton.innerText = "+";

        // Create file name
        var fileName = document.createElement("p");
        fileName.innerText = file.name;

        // File information display
        var fileInfo = document.createElement("p");
        fileInfo.innerText = `${calc.toFixed(2)} MB`;

        // Event listeners
        messageButton.addEventListener("click", (event) => {
            event.preventDefault(); 
            currentFileIndex = event.currentTarget.parentElement.dataset.index;

            // Load data
            if (messageList.has(currentFileIndex)) {
                fileMessage.value = messageList.get(currentFileIndex);
            } else {
                fileMessage.value = "";
            }

            messageModal.style.display = "block";
            // Enable focus
            fileMessage.focus();
        });

        fileName.addEventListener("click", (event) => {
            var fileIndex = event.currentTarget.parentElement.dataset.index;
            fileArr.splice(fileIndex, 1);

            //remove message if file has one
            removeMessage(fileIndex);

            // Create new data transfer
            var dataTransfer = new DataTransfer();
            fileArr.forEach(file => dataTransfer.items.add(file));
            fileList = dataTransfer;
            files.files = dataTransfer.files;

            updateDisplay(); 
        });

        // Append elements
        fileElement.appendChild(messageButton);
        fileElement.appendChild(fileName);
        fileElement.appendChild(fileInfo);

        // Add to display
        fileHolder.appendChild(fileElement);
    });
    
    var color = totalSize > 1000 ? "#f00505" : "#02db4e";
    totalDisplay.innerHTML = `<span style="color: ${color}">${totalSize.toFixed(2)} / 1000 MB</span>`;

    return totalSize; 
}

function updateFileInput(newFiles) {
    for (let x of newFiles) {
        fileList.items.add(x);
    }
    files.files = fileList.files;
}

function removeMessage(fileIndex) {
    if (messageList.has(fileIndex)) {
        messageList.delete(fileIndex);
    }
}

/* 
=====================
   EVENT LISTENERS
=====================
*/

files.addEventListener("change", function(event) {
    event.preventDefault();

    // Update files and display
    updateFileInput(Array.from(event.target.files));
    updateDisplay();
});

// Drag and Drop
fileDisplay.addEventListener("dragover", function(event) {
    event.preventDefault();
    fileOverlay.style.display = "flex";
});

fileDisplay.addEventListener("dragleave", function(event) {
    fileOverlay.style.display = "none";
});

fileDisplay.addEventListener("drop", function(event) {
    event.preventDefault();
    fileOverlay.style.display = "none";
    updateFileInput(Array.from(event.dataTransfer.files));
    updateDisplay();
});

// Message Modal Listeners
closeButton.addEventListener("click", () => {
    messageModal.style.display = "none";
});

// Save message
saveMessageButton.addEventListener("click", () => {
    const message = fileMessage.value;
    
    if (currentFileIndex !== null && message.trim() !== "") {
        //add message to message list
        messageList.set(currentFileIndex, message);
        console.log(`Message for file ${currentFileIndex}: ${message}`);
        messageModal.style.display = "none";
        fileMessage.value = "";
    }
});

// Save recipients
saveRecipientButton.addEventListener("click", () => {
    const people = recipients.value;
    
    if (people.trim() !== "") {
        //add message to message list
        recipientList = people.trim().split(',');
        recipientModal.style.display = "none";
        recipients.value = "";
    }
});

// Open recipients modal
recipientsButton.addEventListener("click", function(event) {
    event.preventDefault();
    recipientModal.style.display = "block";
    recipients.focus();
});

// Ensure default functionality to buttons
fileButton.addEventListener("click", () => files.click());
date.addEventListener("click", function() {
    try {
        date.showPicker();
    } catch(e){}
});
