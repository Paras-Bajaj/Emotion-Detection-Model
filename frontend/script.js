const API = "http://localhost:5000";

console.log("JS LOADED");

// 🔐 RUN ONLY ON PAGE LOAD
document.addEventListener("DOMContentLoaded", () => {

    const token = sessionStorage.getItem("token");

    console.log("TOKEN:", token);

    if (!token) {
        alert("Please login first");
        window.location.href = "login.html";
        return;
    }

    // 🔥 UPLOAD BUTTON
    document.getElementById("uploadBtn").addEventListener("click", async () => {

        console.log("UPLOAD CLICKED");

        const file = document.getElementById("video").files[0];

        if (!file) {
            alert("Select video");
            return;
        }

        let formData = new FormData();
        formData.append("video", file);

        const resultDiv = document.getElementById("result");
        resultDiv.innerHTML = "⏳ Processing...";

        try {
            const res = await fetch(`${API}/upload`, {
                method: "POST",
                headers: {
                    "Authorization": token
                },
                body: formData
            });

            const data = await res.json();

            console.log("RESPONSE:", data);

            resultDiv.innerHTML = `
                <h2>🎯 Emotion: ${data.summary}</h2>
            `;

        } catch (err) {
            console.error(err);
            resultDiv.innerHTML = "❌ Error";
        }
    });

    // 🔐 LOGOUT
    document.getElementById("logoutBtn").addEventListener("click", () => {
        sessionStorage.removeItem("token");
        window.location.href = "login.html";
    });

});