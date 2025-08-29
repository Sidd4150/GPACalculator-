
//Jsx for the File Upload Section 
function FileUploader({ handleFileChange, handleUpload }) {
    return (
        <>
            <input type="file" onChange={handleFileChange} className="transcriptFile" />
            <input type="button" value="Submit" onClick={handleUpload} className="submitFileBtn" />
        </>
    )
}
export default FileUploader;
