import { fetchGPA } from "../api_calls";


export default function CourseEdit({ courses, setCourses, gpa, setGpa }) {

    // Deletes depending on if its a parsed course or a manually enter course
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
        const subject = prompt("Add subject (Subject must be 2-4 UPPERCASE letters Ex: MATH, CS");
        if (!subject) return;

        const number = prompt("Add course number (Must be Number)");
        if (!number) return;

        const title = prompt("Add class title");
        if (!title) return;

        const grade = prompt("Add grade (Must be a single uppercase letter that follows the A-F grading scale");
        if (!grade) return;

        const unitsInput = prompt("Add number of units (Must be number)");
        const units = parseFloat(unitsInput);


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


    // Gets Index of course so you can edit Grade and Units
    const handleEdit = (index) => {
        const courseToEdit = courses[index];

        // Ask for new grade
        const newGrade = prompt("Enter new grade:", courseToEdit.grade);
        if (!newGrade) return;

        // Ask for new units
        const unitsInput = prompt("Enter new number of units:", courseToEdit.units);
        const newUnits = parseFloat(unitsInput);
        if (isNaN(newUnits) || newUnits <= 0) {
            alert("Units must be a positive number!");
            return;
        }

        // Update the course
        const updatedCourses = [...courses];
        updatedCourses[index] = {
            ...courseToEdit,
            grade: newGrade,
            units: newUnits
        };
        setCourses(updatedCourses);

        // Recalculate GPA for active courses
        const activeCourses = updatedCourses
            .filter(c => !c.deleted)
            .map(({ deleted, ...rest }) => rest);
        fetchGPA(activeCourses).then(setGpa);
    };
    return (
        <>
            <div>
                <ul>
                    {courses.map((course, index) => (
                        <li
                            key={index}
                        >
                            <span style={{ color: course.deleted ? 'grey' : 'black', textDecoration: course.deleted ? 'line-through' : 'none' }}>
                                {course.subject} {course.number} - {course.title}: {course.grade} ({course.units} units )
                            </span>
                            <div className='button-group'>
                                {course.source === "manual" && <span>( MANUALLY ADDED)</span>}
                                <button className='editButton' onClick={() => handleEdit(index)} >Edit</button>
                                {!course.deleted && <button onClick={() => handleDelete(index)} className="deleteButton" >Delete</button>}
                                {course.deleted && <button onClick={() => handleAdd(index)} className="addButton">Add</button>}

                            </div>

                        </li>
                    ))}
                </ul>
                <p>Your GPA is {gpa}</p>
            </div >

            <input type='button' value="Add Course" onClick={() => handleNewCourse()} className="addCrsBtn" />
        </>
    )
}