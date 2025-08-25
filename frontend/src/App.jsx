
import './App.css'
import { useState } from 'react'

function App() {

  const [file, setFile] = useState(null);
  const [courses, setCourses] = useState([])
  const [gpa, setGpa] = useState(null)



  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };


  const handleUpload = async () => {
    if (!file) {
      alert("Please provide a file")
    }
    const formData = new FormData();
    formData.append("file", file);

    const uploadRes = await fetch("http://localhost:8000/api/v1/upload", {
      method: "POST",
      body: formData,
    })

    if (!uploadRes.ok) throw new Error(`Upload failed: ${uploadRes.status}`);


    const transcripData = await uploadRes.json()
    console.log(transcripData)
    setCourses(transcripData)

    const gpaRes = await fetch("http://localhost:8000/api/v1/gpa", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ courses: transcripData }),

    })
    const gpaData = await gpaRes.json();
    setGpa(gpaData)
    console.log("GPA Success:", gpaData);

  }

  return (
    <>
      <div>
        <h1>USF</h1>
        <input type="file" onChange={handleFileChange} className="transcriptFile" />
        <input type='button' value="Submit" onClick={handleUpload} />
      </div>

      <h1>Courses</h1>
      <div>
        <ul>
          {courses.map((course, index) => (
            <li key={index}>
              {course.subject} {course.number} - {course.title}: {course.grade} ({course.units} units)
            </li>
          ))}
        </ul>
        <text>Your GPA is {gpa}</text>
      </div>

      <input type='button' value="Add Course" />


    </>
  )
}

export default App
