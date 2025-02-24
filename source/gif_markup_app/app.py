from flask import Flask, render_template, request, redirect, url_for, flash
from data_preprocessing.data_preprocessing_module import VideoToGIF
import os
from datetime import datetime

app = Flask(__name__)
# Folder for uploaded .mp4 files
app.config['UPLOAD_FOLDER'] = 'source/gif_markup_app/static/uploads'
# Folder for processed GIFs
app.config['PROCESSED_FOLDER'] = 'source/gif_markup_app/static/processed'
app.config['ALLOWED_EXTENSIONS'] = {'mp4'}
app.secret_key = 'your_secret_key_here'  # Required for flashing messages

# Ensure the upload and processed folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return (
        '.' in filename
        and
        filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
    )


def preprocess_video(video_path, output_folder):
    gif_cutter = VideoToGIF(video_path)
    gif_cutter.save_GIFs_to_directory(output_folder)


def get_tags(filename, folder):
    tag_file = os.path.join(folder, f'{filename}.txt')
    tags = {}
    if os.path.exists(tag_file):
        with open(tag_file, 'r') as f:
            for line in f.readlines():
                if ': ' in line:
                    key, value = line.strip().split(': ', 1)
                    tags[key] = value
    return tags


@app.route('/')
def index():
    # List all processed folders
    processed_folders = []
    for folder_name in os.listdir(app.config['PROCESSED_FOLDER']):
        folder_path = os.path.join(app.config['PROCESSED_FOLDER'], folder_name)
        if os.path.isdir(folder_path):
            processed_folders.append(folder_name)
    return render_template('index.html', processed_folders=processed_folders)


@app.route('/markup/<folder_name>')
def markup_folder(folder_name):
    folder_path = os.path.join(app.config['PROCESSED_FOLDER'], folder_name)
    if not os.path.exists(folder_path):
        flash('Folder not found', 'error')
        return redirect(url_for('index'))

    # List all GIFs in the selected folder
    gifs = []
    for f in os.listdir(folder_path):
        if f.endswith('.gif'):
            tags = get_tags(f, folder_path)
            gifs.append({'filename': f, 'tags': tags})
    return render_template(
        'markup_folder.html', folder_name=folder_name, gifs=gifs
    )


@app.route('/markup/<folder_name>/<filename>', methods=['GET', 'POST'])
def markup(folder_name, filename):
    folder_path = os.path.join(app.config['PROCESSED_FOLDER'], folder_name)
    if not os.path.exists(folder_path):
        flash('Folder not found', 'error')
        return redirect(url_for('index'))

    tag_file = os.path.join(folder_path, f'{filename}.txt')

    if request.method == 'POST':
        # Get selected values from the form
        gender = request.form.get('gender')
        stage = request.form.get('stage')
        anomaly = request.form.get('anomaly')

        # Read existing tags
        tags = {}
        if os.path.exists(tag_file):
            with open(tag_file, 'r') as f:
                for line in f.readlines():
                    if ': ' in line:
                        key, value = line.strip().split(': ', 1)
                        tags[key] = value

        # Update tags if new values are provided
        if gender:
            tags['Gender'] = gender
        if stage:
            tags['Stage'] = stage
        if anomaly:
            tags['Anomaly'] = anomaly

        # Save the updated tags to the tag file
        with open(tag_file, 'w') as f:
            for key, value in tags.items():
                f.write(f'{key}: {value}\n')

        flash('Markup saved successfully', 'success')
        return redirect(url_for(
            'markup', folder_name=folder_name, filename=filename)
        )

    # Read existing tags
    tags = get_tags(filename, folder_path)
    return render_template(
        'markup.html', folder_name=folder_name, filename=filename, tags=tags
    )


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # Create a unique folder for this upload
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            folder_name = f'upload_{timestamp}'
            folder_path = os.path.join(
                app.config['PROCESSED_FOLDER'], folder_name
            )
            os.makedirs(folder_path, exist_ok=True)

            # Save the uploaded file
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            # Pre-process the video (convert to GIFs)
            preprocess_video(filepath, folder_path)

            flash('File uploaded and processed successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid file type. Only .mp4 files are allowed.', 'error')

    return render_template('upload.html')


if __name__ == '__main__':
    app.run(debug=True)
