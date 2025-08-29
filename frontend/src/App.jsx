import './App.css'
import { useState } from 'react'
import { fetchGPA, uploadTranscript } from "./api_calls";
import Header from './components/Header'
import FileUploader from './components/FileUploader';
import CourseEdit from './components/CourseEdit';

function App() {

  const [file, setFile] = useState(null);
  const [courses, setCourses] = useState([]);
  const [gpa, setGpa] = useState(null);


  const handleFileChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Please provide a file");
      return;
    }

    const uploadRes = await uploadTranscript(file);
    console.log(uploadRes)
    // Add deleted property to each course
    const transcripData = uploadRes.map(course => ({ ...course, deleted: false }));
    setCourses(transcripData);

    const gpaData = await fetchGPA(transcripData.filter(c => !c.deleted));
    setGpa(gpaData);
    console.log("GPA Success:", gpaData);
  };




  return (
    <>
      <div className='container'>
        <Header></Header>
        <p>To get your academic transcript: Go to your myUSF, press Academic Transcript under Records. Once
          you are there hit the keyboard shortcut Command+P on a Mac or Ctrl+P on Windows and save as a .pdf
        </p>
        <FileUploader
          handleFileChange={handleFileChange}
          handleUpload={handleUpload}
        />
      </div>

      <h1>Courses</h1>
      <CourseEdit
        courses={courses}
        setCourses={setCourses}
        gpa={gpa}
        setGpa={setGpa}
      />
    </>
  )
}

export default App;
