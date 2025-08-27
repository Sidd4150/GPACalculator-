import './App.css'
import { useState } from 'react'

function App() {
  const [file, setFile] = useState(null);
  const [courses, setCourses] = useState([]);
  const [gpa, setGpa] = useState(null);

  // Upload transcript file
  const uploadTranscript = async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("https://gpacalculator-qm9d.onrender.com/api/v1/upload", {
      method: "POST",
      body: formData,
    });

    if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
    return res.json(); // transcript data
  };

  // Calculate GPA
  const fetchGPA = async (courses) => {
    const res = await fetch("https://gpacalculator-qm9d.onrender.com/api/v1/gpa", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ courses }),
    });

    if (!res.ok) throw new Error(`GPA fetch failed: ${res.status}`);
    return res.json(); // gpa value
  };

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

  // Mark course as deleted (greyed out)
  const handleDelete = (index) => {
    const updatedCourses = [];

    for (let i = 0; i < courses.length; i++) {
      const course = courses[i];
      if (i === index) {
        if (course.source === "manual") {
          // Skip adding manual course — completely remove
          continue;
        } else {
          updatedCourses.push({ ...course, deleted: true });
        }

      } else {
        updatedCourses.push(course);
      }
    }
    setCourses(updatedCourses);

    // Recalculate GPA excluding deleted courses
    const activeCourses = updatedCourses.filter(c => !c.deleted);
    fetchGPA(activeCourses).then(gpaData => setGpa(gpaData));
  };

  const handleAdd = (index) => {
    const updatedCourses = [];

    for (let i = 0; i < courses.length; i++) {
      const course = courses[i];
      if (i === index) {
        updatedCourses.push({ ...course, deleted: false });
      } else {
        updatedCourses.push(course);
      }
    }
    setCourses(updatedCourses);

    // Recalculate GPA excluding deleted courses
    const activeCourses = updatedCourses.filter(c => !c.deleted);
    fetchGPA(activeCourses).then(gpaData => setGpa(gpaData));
  };

  const handleNewCourse = () => {
    const subject = prompt("Add subject");
    if (!subject) return;

    const number = prompt("Add course number");
    if (!number) return;

    const title = prompt("Add class title");
    if (!title) return;

    const grade = prompt("Add grade");
    if (!grade) return;

    const unitsInput = prompt("Add number of units");
    const units = parseFloat(unitsInput);
    if (isNaN(units) || units <= 0) {
      alert("Units must be a positive number!");
      return;
    }

    const newCourse = {
      subject,
      number,
      title,
      grade,
      units,
      source: "manual"
    };

    const updatedCourses = [];
    for (let i = 0; i < courses.length; i++) {
      updatedCourses.push(courses[i]);
    }
    updatedCourses.push(newCourse); // add the new course at the end

    setCourses(updatedCourses);

    // Recalculate GPA excluding deleted courses
    const activeCourses = updatedCourses
      .filter(c => !c.deleted)
      .map(({ deleted, ...rest }) => rest); // strip frontend-only keys
    fetchGPA(activeCourses).then(setGpa);
  };


  return (
    <>
      <div className='container'>
        <header>
          <h1>USF</h1>
        </header>
        <p>To get your academic transcript: Go to your myUSF, press Academic Transcript under Records. Once
          you are there hit the keyboard shortcut Command+P on a Mac or Ctrl+P on Windows and save as a .pdf
        </p>
        <input type="file" onChange={handleFileChange} className="transcriptFile" />
        <input type='button' value="Submit" onClick={handleUpload} />
      </div>

      <h1>Courses</h1>
      <div>
        <ul>
          {courses.map((course, index) => (
            <li
              key={index}
              style={{ color: course.deleted ? 'grey' : 'black', textDecoration: course.deleted ? 'line-through' : 'none' }}
            >
              {course.subject} {course.number} - {course.title}: {course.grade} ({course.units} units )
              {!course.deleted && <button onClick={() => handleDelete(index)}>Delete</button>}
              {course.deleted && <button onClick={() => handleAdd(index)}>Add</button>}
              {course.source === "manual" && <span>( MANUALLY ADDED)</span>}
            </li>
          ))}
        </ul>
        <p>Your GPA is {gpa}</p>
      </div>

      <input type='button' value="Add Course" onClick={() => handleNewCourse()} />
    </>
  )
}

export default App;
