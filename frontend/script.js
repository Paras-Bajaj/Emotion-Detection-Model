const API = "http://localhost:5000";

function getToken() {
    return sessionStorage.getItem("token");
}

function isAuthPage() {
    return document.getElementById("email") && document.getElementById("password");
}

function isProtectedPage() {
    return document.getElementById("uploadBtn") || document.body.dataset.requiresAuth === "true";
}

function redirectToLogin(message) {
    if (message) {
        alert(message);
    }
    window.location.href = "login.html";
}

async function signup() {
    const email = document.getElementById("email")?.value.trim();
    const password = document.getElementById("password")?.value;

    if (!email || !password) {
        alert("Enter email and password");
        return;
    }

    try {
        const res = await fetch(`${API}/signup`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.msg || "Signup failed");
        }

        alert("Signup successful. Please login.");
        window.location.href = "login.html";
    } catch (error) {
        alert(error.message || "Signup failed");
    }
}

async function login() {
    const email = document.getElementById("email")?.value.trim();
    const password = document.getElementById("password")?.value;

    if (!email || !password) {
        alert("Enter email and password");
        return;
    }

    try {
        const res = await fetch(`${API}/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password })
        });

        const data = await res.json();

        if (!res.ok || !data.token) {
            throw new Error(data.msg || "Login failed");
        }

        sessionStorage.setItem("token", data.token);
        window.location.href = "dashboard.html";
    } catch (error) {
        alert(error.message || "Login failed");
    }
}

function logout() {
    sessionStorage.removeItem("token");
    window.location.href = "login.html";
}

function checkAuth() {
    if (!getToken()) {
        redirectToLogin("Please login first");
    }
}

async function uploadVideo() {
    const token = getToken();
    const file = document.getElementById("video")?.files?.[0];
    const resultDiv = document.getElementById("result");

    if (!file) {
        alert("Select a video");
        return;
    }

    const formData = new FormData();
    formData.append("video", file);

    if (resultDiv) {
        resultDiv.textContent = "Processing...";
    }

    try {
        const res = await fetch(`${API}/upload`, {
            method: "POST",
            headers: {
                "Authorization": token
            },
            body: formData
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.msg || data.message || "Upload failed");
        }

        if (resultDiv) {
            resultDiv.innerHTML = `<h2>Emotion: ${data.summary}</h2>`;
        }
    } catch (error) {
        if (resultDiv) {
            resultDiv.textContent = error.message || "Upload failed";
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (isAuthPage()) {
        return;
    }

    if (isProtectedPage()) {
        checkAuth();
    }

    const uploadBtn = document.getElementById("uploadBtn");
    if (uploadBtn) {
        uploadBtn.addEventListener("click", uploadVideo);
    }

    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", logout);
    }
});

window.signup = signup;
window.login = login;
window.logout = logout;
window.checkAuth = checkAuth;