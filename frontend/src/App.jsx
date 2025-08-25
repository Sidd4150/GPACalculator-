
import './App.css'
import { useState } from 'react'

function App() {


  const [file, setFile] = useState(null);

  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };


  const handleUpload = () => {
    if (!file) {
      alert("Please provide a file")
    }
    const formData = new FormData();
    formData.append("file", file);

    fetch("http://localhost:8000/api/v1/upload", {
      method: "POST",
      body: formData,
    })
      .then((res) => res.json())
      .then((data) => console.log("Success:", data))
      .catch((err) => console.error("Error:", err));

  }



  return (
    <>
      <div>
        <h1>USF</h1>
        <input type="file" onChange={handleFileChange} className="transcriptFile" />
        <input type='button' value="Submit" onClick={handleUpload} />
      </div>
    </>
  )
}

export default App
