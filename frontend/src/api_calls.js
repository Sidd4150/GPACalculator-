// Upload transcript file
export const uploadTranscript = async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("http://localhost:8000/api/v1/upload", {//"https://gpacalculator-qm9d.onrender.com/api/v1/upload", {
        method: "POST",
        body: formData,
    });

    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json(); // transcript data
};

// Calculate GPA
export const fetchGPA = async (courses) => {
    const res = await fetch("http://localhost:8000/api/v1/gpa", {//"https://gpacalculator-qm9d.onrender.com/api/v1/gpa", 
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ courses }),
    });

    if (!res.ok) throw new Error(`GPA fetch failed: ${res.status}`);
    return res.json(); // gpa value
};