/**
 * uploader.js
 * Handles drag-and-drop and click-to-browse file upload.
 * Sends the file to POST /upload and returns the parsed API response.
 */

const Uploader = (() => {
  const API_BASE = 'http://localhost:5000';

  /**
   * Initialise the upload drop-zone.
   * @param {string}   dropZoneId  - ID of the drop-zone element
   * @param {string}   fileInputId - ID of the hidden <input type="file">
   * @param {Function} onResult    - callback(data) called with API response
   * @param {Function} onError     - callback(message) called on error
   * @param {Function} onLoading   - callback(bool) called to toggle loading state
   */
  function init(dropZoneId, fileInputId, onResult, onError, onLoading) {
    const dropZone  = document.getElementById(dropZoneId);
    const fileInput = document.getElementById(fileInputId);

    if (!dropZone || !fileInput) return;

    // Click to open file browser
    dropZone.addEventListener('click', () => fileInput.click());

    // File selected from browser
    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        _uploadFile(fileInput.files[0], onResult, onError, onLoading);
      }
    });

    // Drag-and-drop events
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        _uploadFile(files[0], onResult, onError, onLoading);
      }
    });
  }

  /**
   * Upload a single file to the /upload endpoint.
   */
  async function _uploadFile(file, onResult, onError, onLoading) {
    const ext = file.name.split('.').pop().toLowerCase();

    if (!['txt', 'eml'].includes(ext)) {
      onError(`Unsupported file type ".${ext}". Please upload a .txt or .eml file.`);
      return;
    }

    onLoading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        onError(data.error || 'Upload failed. Please try again.');
        return;
      }

      onResult(data, { fromFile: true, filename: file.name });

    } catch (err) {
      onError('Could not reach the backend. Is the Flask server running on port 5000?');
    } finally {
      onLoading(false);
    }
  }

  return { init };
})();
