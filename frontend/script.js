// Define API URL (Assuming default FastAPI port)
const API_URL = "http://localhost:8000/generate-plan";
const FOOD_API_URL = "http://localhost:8000/analyze-food";
let currentPlanData = null;

document.addEventListener("DOMContentLoaded", () => {

    // --- Sidebar Logic ---
    const sidebar = document.getElementById("sidebar");
    const sidebarToggle = document.getElementById("sidebarToggle");
    const sidebarClose = document.getElementById("sidebarClose");
    const sidebarOverlay = document.getElementById("sidebarOverlay");

    if (sidebarToggle) {
        sidebarToggle.addEventListener("click", () => {
            sidebar.classList.add("open");
            sidebarOverlay.classList.add("show");
        });
    }

    function closeSidebar() {
        sidebar.classList.remove("open");
        sidebarOverlay.classList.remove("show");
    }

    if (sidebarClose) sidebarClose.addEventListener("click", closeSidebar);
    if (sidebarOverlay) sidebarOverlay.addEventListener("click", closeSidebar);

    // --- Index Page Logic ---
    const detailsForm = document.getElementById("detailsForm");
    if (detailsForm) {
        detailsForm.addEventListener("submit", (e) => {
            e.preventDefault();

            // Collect Data
            const formData = {
                age: parseInt(document.getElementById("age").value),
                height: parseFloat(document.getElementById("height").value),
                weight: parseFloat(document.getElementById("weight").value),
                gender: document.getElementById("gender").value,
                foodType: document.getElementById("foodType").value,
                activityLevel: document.getElementById("activityLevel").value,
                health_condition: document.getElementById("health_condition").value,
                goal: document.getElementById("goal").value
            };

            // Basic Validation Check (HTML5 handles most, but ensuring)
            if (!formData.gender || !formData.foodType || !formData.activityLevel) {
                alert("Please fill in all details.");
                return;
            }

            // Save to Session Storage
            sessionStorage.setItem("userProfile", JSON.stringify(formData));

            // Navigate
            window.location.href = "results.html";
        });
    }

    // --- Results Page Logic ---
    const planContent = document.getElementById("planContent");
    if (planContent && window.location.pathname.includes("results.html")) {
        const userProfileStr = sessionStorage.getItem("userProfile");

        if (!userProfileStr) {
            alert("No user data found. Please enter your details first.");
            window.location.href = "index.html";
            return;
        }

        const userProfile = JSON.parse(userProfileStr);
        fetchPlan(userProfile);

        // Setup Accordion Interactions
        setupAccordion();

        // Setup PDF Download header
        document.getElementById("downloadBtn").addEventListener("click", downloadPDF);
    }

    // --- Food Analysis Page Logic ---
    const uploadArea = document.getElementById("uploadArea");
    const foodImageInput = document.getElementById("foodImageInput");
    const imagePreview = document.getElementById("imagePreview");
    const uploadPlaceholder = document.getElementById("uploadPlaceholder");
    const analyzeBtn = document.getElementById("analyzeBtn");

    if (uploadArea && foodImageInput) {
        let selectedFile = null;

        // Click to upload
        uploadArea.addEventListener("click", () => foodImageInput.click());

        // Drag & Drop
        uploadArea.addEventListener("dragover", (e) => {
            e.preventDefault();
            uploadArea.classList.add("dragging");
        });
        uploadArea.addEventListener("dragleave", () => uploadArea.classList.remove("dragging"));
        uploadArea.addEventListener("drop", (e) => {
            e.preventDefault();
            uploadArea.classList.remove("dragging");
            if (e.dataTransfer.files.length > 0) {
                handleFileSelect(e.dataTransfer.files[0]);
            }
        });

        // File input change
        foodImageInput.addEventListener("change", (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });

        function handleFileSelect(file) {
            if (!file.type.startsWith("image/")) {
                alert("Please select a valid image file.");
                return;
            }
            selectedFile = file;
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                imagePreview.classList.remove("hidden");
                uploadPlaceholder.classList.add("hidden");
            };
            reader.readAsDataURL(file);
            analyzeBtn.disabled = false;
        }

        // Analyze button
        analyzeBtn.addEventListener("click", async () => {
            if (!selectedFile) return;

            const loading = document.getElementById("analysisLoading");
            const results = document.getElementById("analysisResults");
            const error = document.getElementById("analysisError");
            const errorText = document.getElementById("analysisErrorText");

            loading.classList.remove("hidden");
            results.classList.add("hidden");
            error.classList.add("hidden");
            analyzeBtn.disabled = true;

            try {
                const formData = new FormData();
                formData.append("file", selectedFile);

                const response = await fetch(FOOD_API_URL, {
                    method: "POST",
                    body: formData
                });

                if (!response.ok) {
                    const errData = await response.json();
                    throw new Error(errData.detail || "Server error");
                }

                const data = await response.json();
                renderFoodResults(data);

                loading.classList.add("hidden");
                results.classList.remove("hidden");

            } catch (err) {
                console.error(err);
                loading.classList.add("hidden");
                error.classList.remove("hidden");
                errorText.textContent = err.message || "Failed to analyze food image.";
            }

            analyzeBtn.disabled = false;
        });
    }
});

async function fetchPlan(userProfile) {
    const loading = document.getElementById("loading");
    const results = document.getElementById("results");
    const errorMsg = document.getElementById("errorMsg");
    const errorText = document.getElementById("errorText");

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(userProfile)
        });

        if (!response.ok) {
            throw new Error(`Server Error: ${response.statusText}`);
        }

        const data = await response.json();
        currentPlanData = data; // Store for PDF generation
        renderResults(data);

        // Hide loading, show results
        loading.classList.add("hidden");
        results.classList.remove("hidden");

    } catch (err) {
        console.error(err);
        loading.classList.add("hidden");
        errorMsg.classList.remove("hidden");
        errorText.textContent = "Failed to connect to the G&G Intelligence Layer. Ensure the backend is running.";
    }
}

function renderResults(data) {
    // 1. Stats
    const statsDiv = document.getElementById("dailyStats");
    const stats = data.daily_stats;
    statsDiv.innerHTML = `
        <div class="stat-box">
            <span class="stat-value">${stats.target_calories}</span>
            <span class="stat-label">Calories</span>
        </div>
        <div class="stat-box">
            <span class="stat-value">${stats.target_protein}g</span>
            <span class="stat-label">Protein</span>
        </div>
        <div class="stat-box">
            <span class="stat-value">${stats.target_carbs}g</span>
            <span class="stat-label">Carbs</span>
        </div>
        <div class="stat-box">
            <span class="stat-value">${stats.target_fats}g</span>
            <span class="stat-label">Fats</span>
        </div>
    `;

    // 2. Diet Table (7-Day Logic)
    renderDietSection(data.diet_plan);

    // 3. Workout Table
    const workoutTable = document.getElementById("workoutTableBody");
    workoutTable.innerHTML = data.workout_plan.map(item => `
        <tr>
            <td>${item.Exercise_Name}</td>
            <td>${item["Difficulty Level"] || "N/A"}</td>
            <td>${item.Equipment || "None"}</td>
            <td>${item.Sets || "3"} x ${item.Reps || "10-12"}</td>
        </tr>
    `).join("");

    // 4. Tips
    const tipsList = document.getElementById("tipsList");
    tipsList.innerHTML = data.additional_tips.map(tip => `<li>${tip}</li>`).join("");
}

function renderDietSection(dietPlanRef) {
    const tabsContainer = document.getElementById("dietDayTabs");
    const tableBody = document.getElementById("dietTableBody");

    // Clear existing
    tabsContainer.innerHTML = "";
    tableBody.innerHTML = "";

    // 1. Create Tabs
    dietPlanRef.forEach((dayPlan, index) => {
        const btn = document.createElement("button");
        btn.textContent = dayPlan.day || `Day ${index + 1}`;
        btn.classList.add("day-tab-btn");
        if (index === 0) btn.classList.add("active");

        btn.addEventListener("click", () => {
            // Switch Tab UI
            document.querySelectorAll(".day-tab-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            // Render Table
            renderDietTable(dayPlan.meals);
        });

        tabsContainer.appendChild(btn);
    });

    // 2. Render First Day Initial
    if (dietPlanRef.length > 0) {
        renderDietTable(dietPlanRef[0].meals);
    }
}

function renderDietTable(meals) {
    const tableBody = document.getElementById("dietTableBody");
    if (!meals) return;

    tableBody.innerHTML = meals.map(item => `
        <tr>
            <td>${item.Food_Name}</td>
            <td>${item["Food Category"]}</td>
            <td>${item.Calories}</td>
            <td>${item.Protein}</td>
            <td>${item.Carbs}</td>
            <td>${item.Fats}</td>
        </tr>
    `).join("");
}

function setupAccordion() {
    const accButtons = document.querySelectorAll(".accordion-header");
    accButtons.forEach(btn => {
        btn.addEventListener("click", function () {
            this.classList.toggle("active");
            const content = this.nextElementSibling;
            if (content.style.display === "block") {
                content.style.display = "none";
            } else {
                content.style.display = "block";
            }
        });
    });
}

// Make sure window.jspdf is accessible
const { jsPDF } = window.jspdf;

function downloadPDF() {
    if (!currentPlanData) {
        alert("No plan data to download.");
        return;
    }

    // Create a temporary container for the PDF report
    const reportContainer = document.createElement("div");
    reportContainer.id = "pdf-report";

    // Generate Diet Plan HTML (Iterating over 7 days)
    let dietPlanHTML = "";
    currentPlanData.diet_plan.forEach(dayPlan => {
        dietPlanHTML += `
            <div class="pdf-sub-section">
                <h4>${dayPlan.day || "Day"}</h4>
                <table class="pdf-table">
                    <thead>
                        <tr>
                            <th>Food Item</th>
                            <th>Cat</th>
                            <th>Kcal</th>
                            <th>P(g)</th>
                            <th>C(g)</th>
                            <th>F(g)</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${dayPlan.meals.map(item => `
                            <tr>
                                <td>${item.Food_Name}</td>
                                <td>${item["Food Category"]}</td>
                                <td>${item.Calories}</td>
                                <td>${item.Protein}</td>
                                <td>${item.Carbs}</td>
                                <td>${item.Fats}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            </div>
        `;
    });

    reportContainer.innerHTML = `
        <div class="pdf-header">
            <h1>G&G Fitness Plan</h1>
            <p>Your personalized roadmap to health.</p>
        </div>

        <div class="pdf-section">
            <h3>Daily Nutrition Targets</h3>
            <div class="pdf-stats">
                <span><strong>Calories:</strong> ${currentPlanData.daily_stats.target_calories}</span>
                <span><strong>Protein:</strong> ${currentPlanData.daily_stats.target_protein}g</span>
                <span><strong>Carbs:</strong> ${currentPlanData.daily_stats.target_carbs}g</span>
                <span><strong>Fats:</strong> ${currentPlanData.daily_stats.target_fats}g</span>
            </div>
        </div>

        <div class="pdf-section">
            <h3>Weekly Diet Plan</h3>
            ${dietPlanHTML}
        </div>

        <div class="pdf-section page-break-before">
            <h3>Workout Plan</h3>
            <table class="pdf-table">
                <thead>
                    <tr>
                        <th>Exercise</th>
                        <th>Diff</th>
                        <th>Equipment</th>
                        <th>Sets x Reps</th>
                    </tr>
                </thead>
                <tbody>
                    ${currentPlanData.workout_plan.map(item => `
                        <tr>
                            <td>${item.Exercise_Name}</td>
                            <td>${item["Difficulty Level"] || "N/A"}</td>
                            <td>${item.Equipment || "None"}</td>
                            <td>${item.Sets || "3"} x ${item.Reps || "10-12"}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        </div>

        <div class="pdf-section">
            <h3>Additional Tips</h3>
            <ul class="pdf-list">
                ${currentPlanData.additional_tips.map(tip => `<li>${tip}</li>`).join("")}
            </ul>
        </div>
    `;

    // Make it visible as an overlay
    reportContainer.style.position = 'fixed';
    reportContainer.style.top = '0';
    reportContainer.style.left = '0';
    reportContainer.style.width = '210mm'; // Bind explicitly to A4 width on screen for better WYSIWYG
    reportContainer.style.minHeight = '297mm';
    reportContainer.style.background = '#ffffff';
    reportContainer.style.zIndex = '10000';
    reportContainer.style.padding = '20px';

    document.body.appendChild(reportContainer);

    setTimeout(() => {
        html2canvas(reportContainer, {
            scale: 2, // High resolution
            useCORS: true,
            scrollY: 0
        }).then(canvas => {
            const imgData = canvas.toDataURL('image/jpeg', 0.98);

            // Calculate PDF dimensions (A4)
            const pdf = new jsPDF('p', 'mm', 'a4');
            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = pdf.internal.pageSize.getHeight();

            const imgWidth = pdfWidth;
            const imgHeight = (canvas.height * imgWidth) / canvas.width;

            // If content is taller than one page, handle simple pagination or let it be one long page depending on requirement. 
            // The simple "image to pdf" approach works best for single pages or we just scale to fit.
            // For multi-page, we'd need to slice the canvas.
            // Given the complexity of splitting an image perfectly across pages, the simplest robust fix is:
            // Add the image. If it overflows, it just overflows (or we can add pages manually).

            // Simpler robust approach: Add image to PDF. 
            // If height > pdfHeight, add new page.

            let heightLeft = imgHeight;
            let position = 0;

            pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight);
            heightLeft -= pdfHeight;

            while (heightLeft >= 0) {
                position = heightLeft - imgHeight; // Move the image up
                pdf.addPage();
                pdf.addImage(imgData, 'JPEG', 0, position, imgWidth, imgHeight);
                heightLeft -= pdfHeight;
            }

            pdf.save('G&G_Fitness_Plan.pdf');

            // Cleanup
            if (document.body.contains(reportContainer)) {
                document.body.removeChild(reportContainer);
            }
        }).catch(err => {
            console.error(err);
            alert("Failed to generate PDF.");
            if (document.body.contains(reportContainer)) {
                document.body.removeChild(reportContainer);
            }
        });
    }, 500);
}

// ==================== FOOD ANALYSIS HELPERS ====================

function renderFoodResults(data) {
    // Food Name & Category
    document.getElementById("foodName").textContent = data.food_name || "Unknown Food";
    document.getElementById("foodCategory").textContent = data.food_category || "N/A";
    document.getElementById("foodDescription").textContent = data.description || "";
    document.getElementById("servingSize").textContent = data.estimated_serving_size || "N/A";

    // Health Rating Badge
    const ratingEl = document.getElementById("healthRating");
    const rating = (data.overall_health_rating || "").toLowerCase();
    ratingEl.textContent = data.overall_health_rating || "N/A";
    ratingEl.className = "health-rating-badge";
    if (rating.includes("healthy") && !rating.includes("unhealthy")) {
        ratingEl.classList.add("healthy");
    } else if (rating.includes("moderate")) {
        ratingEl.classList.add("moderate");
    } else if (rating.includes("unhealthy")) {
        ratingEl.classList.add("unhealthy");
    }

    // Nutrition Stats
    const n = data.nutrition_per_serving || {};
    document.getElementById("nutritionStats").innerHTML = `
        <div class="stat-box">
            <span class="stat-value">${n.calories || 0}</span>
            <span class="stat-label">Calories</span>
        </div>
        <div class="stat-box">
            <span class="stat-value">${n.protein_g || 0}g</span>
            <span class="stat-label">Protein</span>
        </div>
        <div class="stat-box">
            <span class="stat-value">${n.carbs_g || 0}g</span>
            <span class="stat-label">Carbs</span>
        </div>
        <div class="stat-box">
            <span class="stat-value">${n.fats_g || 0}g</span>
            <span class="stat-label">Fats</span>
        </div>
        <div class="stat-box">
            <span class="stat-value">${n.fiber_g || 0}g</span>
            <span class="stat-label">Fiber</span>
        </div>
        <div class="stat-box">
            <span class="stat-value">${n.sugar_g || 0}g</span>
            <span class="stat-label">Sugar</span>
        </div>
    `;

    // Lists
    renderList("ingredientsList", data.ingredients);
    renderList("benefitsList", data.health_benefits);
    renderList("warningsList", data.health_warnings);
    renderList("alternativesList", data.healthier_alternatives);

    // Detailed Analysis
    document.getElementById("detailedAnalysis").textContent = data.detailed_analysis || "";
}

function renderList(elementId, items) {
    const el = document.getElementById(elementId);
    if (!el) return;
    if (!items || items.length === 0) {
        el.innerHTML = "<li>None noted.</li>";
        return;
    }
    el.innerHTML = items.map(item => `<li>${item}</li>`).join("");
}

function resetAnalysis() {
    const imagePreview = document.getElementById("imagePreview");
    const uploadPlaceholder = document.getElementById("uploadPlaceholder");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const foodImageInput = document.getElementById("foodImageInput");

    if (imagePreview) {
        imagePreview.src = "";
        imagePreview.classList.add("hidden");
    }
    if (uploadPlaceholder) uploadPlaceholder.classList.remove("hidden");
    if (analyzeBtn) analyzeBtn.disabled = true;
    if (foodImageInput) foodImageInput.value = "";

    const results = document.getElementById("analysisResults");
    const error = document.getElementById("analysisError");
    if (results) results.classList.add("hidden");
    if (error) error.classList.add("hidden");
}
