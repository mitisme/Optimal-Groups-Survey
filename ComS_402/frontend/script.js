if (window.location.href.includes('success.html')) {
    function returnHomeScreen() {
        window.location.href = 'upload.html';
    }
    function timeConversion(militaryTime) {
        let colonIndex = militaryTime.indexOf(":")
        let hours = parseInt(militaryTime.substring(0, colonIndex));
        let minutes = militaryTime.substring(colonIndex + 1);
        let ampm = "AM";
        if(hours == 0) {
            hours = 12
        }
        else if(hours >= 12){
            ampm = "PM";
            if(hours > 12) {
                hours = hours - 12;
            }
        }
        return hours + ":" + minutes + " " + ampm;
    }
    document.getElementById("sumCourseID").textContent = localStorage.getItem("course");
    document.getElementById("sumGroupSizeID").textContent = localStorage.getItem("groupSize");
    document.getElementById("sumDeadlineDateID").textContent = localStorage.getItem("deadlineDate");
    document.getElementById("sumDeadlineTimeID").textContent = timeConversion(localStorage.getItem("deadlineTime"));
    document.getElementById("sumFileID").textContent = localStorage.getItem("uploadedFile");
}
else {
    const dropArea = document.getElementById("dropArea");
    const fileInput = document.getElementById("fileInput");
    const uploadStatus = document.getElementById("uploadStatus");
    const removeFileButton = document.getElementById('removeFileButton');
    const selectedFile = document.getElementById("selectedFile");
    const deadlineDateInput = document.getElementById("deadlineDateID");
    const deadlineTimeInput = document.getElementById("deadlineTimeID");
    const uploadButton = document.getElementById("uploadBttn");
    const spinAnimation = document.getElementById("spinAnimation");
    
    // event listeners for dragging and dropping of files
    dropArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropArea.classList.add("highlight");
    });
    
    dropArea.addEventListener("dragleave", () => {
        dropArea.classList.remove("highlight");
    });
    
    dropArea.addEventListener("drop", (e) => {
        e.preventDefault();
        dropArea.classList.remove("highlight");
    
        const files = e.dataTransfer.files;
        fileInput.files = files;
        if (fileInput.files.length > 0) {
            selectedFile.textContent = `Selected File: ${fileInput.files[0].name}`;
            removeFileButton.style.display = "inline";
            uploadStatus.textContent = "";

            // check if the file contains the column "SIS Login ID" (presumably, the net-id column)
            isValidCSV(fileInput.files[0]);
        } else {
            selectedFile.textContent = "No file selected";
            removeFileButton.style.display = "none";
            uploadStatus.textContent = "";
        }
    });
    
    // event listener for normal selection of file
    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            selectedFile.textContent = `Selected File: ${fileInput.files[0].name}`;
            removeFileButton.style.display = "inline";
            uploadStatus.textContent = "";
            
            // check if the file contains the column "SIS Login ID" (presumably, the net-id column)
            isValidCSV(fileInput.files[0]);
        } else {
            selectedFile.textContent = "No file selected";
            removeFileButton.style.display = "none";
            uploadStatus.textContent = "";
        }
    });
    // event listener for removal of file
    removeFileButton.addEventListener("click", () => {
        fileInput.value = ""; // removes previously selected file
        selectedFile.textContent = "No file selected";
        removeFileButton.style.display = "none";
        uploadStatus.textContent = "";
    });
    
    // event listener for the upload of the inputs and csv file
    document.querySelector("form").addEventListener("submit", async (e) => {
        e.preventDefault()
        if (fileInput.files.length > 0) {
            const isValid = await isValidCSV(fileInput.files[0]);
            
            if (!isValid) {
                e.preventDefault();
                uploadStatus.style.visibility = "visible";
                uploadStatus.textContent = "Invalid CSV - Missing column 'SIS Login ID' or 'Student'";
            }
            else {
                const course= document.getElementById("courseID").value;
                const groupSize = document.getElementById("groupSizeID").value;
                const deadlineDate = convertDateFormat(deadlineDateInput.value);
                const deadlineTime = deadlineTimeInput.value;
                const uploadedFile = fileInput.files[0].name;

                localStorage.setItem("course", course);
                localStorage.setItem("groupSize", groupSize);
                localStorage.setItem("deadlineDate", deadlineDate);
                localStorage.setItem("deadlineTime", deadlineTime);
                localStorage.setItem("uploadedFile", uploadedFile);
                
                uploadButton.disabled = true;
                uploadButton.querySelector("strong").textContent = "";
                spinAnimation.style.display = "block";

                e.target.submit();
            }
        }
        else {

            e.preventDefault();
            uploadStatus.style.visibility = "visible";
            uploadStatus.textContent = "Please select a file to upload.";
        }
    });
    // Below function to be implemented later to ensure CSV contains net-ids
    async function isValidCSV(file) {
        let temp = new Promise((resolve, reject) => {
            const reader = new FileReader();

            reader.onload = function(event) {
                const fileContent = event.target.result;
                const lines = fileContent.split('\n');
                const headerRow = lines[0];
                const columnTitles = headerRow.split(',');
    
                if (columnTitles.includes("SIS Login ID") && columnTitles.includes("Student")) {
                    resolve(true); // Resolve with true if CSV is valid
                } else {
                    resolve(false);
                }
            };
            reader.onerror = function(event) {
                console.log("Error reading the file:", event.target.error);
                reject("Error reading the file."); // Reject with an error message
            };
            // Read file as a text string. This is for the reader.onload event to work.
            reader.readAsText(file);
        });
        return await temp;
    }
    function convertDateFormat(date) {
        let dateArray = date.split('-');
        let year = dateArray[0];
        let month = dateArray[1];
        let day = dateArray[2];

        return month + "/" + day + "/" + year;
    }
    function setDateRange() {
        const currentDate = new Date();
        
        let minDate = currentDate.toLocaleDateString();
        let dateArray = minDate.split('/');
        let month = dateArray[0].padStart(2,"0");
        let day = dateArray[1].padStart(2,"0");
        let year = dateArray[2];
        let minDateString = year + "-" + month + "-" + day;
        deadlineDateInput.setAttribute('min', minDateString);

        let maxDate = new Date(currentDate);
        maxDate.setDate(currentDate.getDate() + 7);
        let maxDateString = maxDate.toLocaleDateString();
    
        dateArray = maxDateString.split('/');
        month = dateArray[0].padStart(2,"0");
        day = dateArray[1].padStart(2,"0");
        year = dateArray[2];
        maxDateString = year + "-" + month + "-" + day;

        deadlineDateInput.setAttribute('max', maxDateString);
    }
    setDateRange()
}
