(() => {
	const dropzone = document.getElementById('dropzone');
	const fileInput = document.getElementById('file-input');
	const fileName = document.getElementById('file-name');
	const submitBtn = document.getElementById('submit-btn');
	const form = document.getElementById('upload-form');
	const overlay = document.getElementById('loading');

	if (!dropzone || !fileInput) return;

	const setFile = (file) => {
		if (!file) return;
		const allowed = ['application/pdf', 'image/jpeg', 'image/png', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
		if (!allowed.includes(file.type)) {
			alert('Only PDF, DOCX, JPG, or PNG files are supported.');
			return;
		}
		const maxBytes = 5 * 1024 * 1024;
		if (file.size > maxBytes) {
			alert('File exceeds 5 MB limit.');
			return;
		}
		fileInput.files = new DataTransfer().files; // reset
		const dt = new DataTransfer();
		dt.items.add(file);
		fileInput.files = dt.files;
		fileName.textContent = file.name;
		submitBtn.disabled = false;
	};

	dropzone.addEventListener('click', () => fileInput.click());
	dropzone.addEventListener('keydown', (e) => {
		if (e.key === 'Enter' || e.key === ' ') {
			e.preventDefault();
			fileInput.click();
		}
	});

	['dragenter', 'dragover'].forEach(ev => dropzone.addEventListener(ev, (e) => {
		e.preventDefault();
		dropzone.classList.add('dragging');
	}));
	['dragleave', 'drop'].forEach(ev => dropzone.addEventListener(ev, (e) => {
		e.preventDefault();
		dropzone.classList.remove('dragging');
	}));

	dropzone.addEventListener('drop', (e) => {
		const file = e.dataTransfer?.files?.[0];
		setFile(file);
	});

	fileInput.addEventListener('change', (e) => {
		const file = e.target.files?.[0];
		setFile(file);
	});

	form.addEventListener('submit', () => {
		submitBtn.textContent = 'Analyzing…';
		submitBtn.disabled = true;
		if (overlay) overlay.hidden = false;
	});
})();


