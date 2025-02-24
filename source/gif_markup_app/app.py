from flask import Flask, render_template, request, redirect, url_for, flash
import os
from data_preprocessing.data_preprocessing_module import VideoToGIF
# import shutil

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


def preprocess_video(video_path):
    # Preprocess the video using the data_preprocessing module
    gif_cutter = VideoToGIF(video_path)
    gif_cutter.save_GIFs_to_directory(app.config['PROCESSED_FOLDER'])


def get_tags(filename):
    tag_file = os.path.join(app.config['PROCESSED_FOLDER'], f'{filename}.txt')
    if os.path.exists(tag_file):
        with open(tag_file, 'r') as f:
            return f.read().splitlines()
    return []


@app.route('/')
def index():
    # List all processed GIFs in the processed folder
    gifs = []
    for f in os.listdir(app.config['PROCESSED_FOLDER']):
        if f.endswith('.gif'):
            tags = get_tags(f)
            gifs.append({'filename': f, 'tags': tags})
    return render_template('index.html', gifs=gifs)


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
            # Ensure the upload folder exists
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

            # Save the file to the upload folder
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            # Debug: Print the file path to verify
            print(f"File saved to: {filepath}")

            # Pre-process the video (convert to GIFs)
            preprocess_video(filepath)

            flash('File uploaded and processed successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid file type. Only .mp4 files are allowed.', 'error')

    return render_template('upload.html')


@app.route('/markup/<filename>', methods=['GET', 'POST'])
def markup(filename):
    if request.method == 'POST':
        # Get selected values from the form
        gender = request.form.get('gender')
        stage = request.form.get('stage')
        anomaly = request.form.get('anomaly')

        # Save the selected values to the tag file
        tag_file = os.path.join(
            app.config['PROCESSED_FOLDER'], f'{filename}.txt'
        )
        with open(tag_file, 'a') as f:
            if gender:
                f.write(f'Gender: {gender}\n')
            if stage:
                f.write(f'Stage: {stage}\n')
            if anomaly:
                f.write(f'Anomaly: {anomaly}\n')

        flash('Markup saved successfully', 'success')
        return redirect(url_for('markup', filename=filename))

    # Read existing tags
    tags = get_tags(filename)
    return render_template('markup.html', filename=filename, tags=tags)


@app.route('/delete/<filename>')
def delete(filename):
    gif_path = os.path.join(app.config['PROCESSED_FOLDER'], filename)
    tag_file = os.path.join(app.config['PROCESSED_FOLDER'], f'{filename}.txt')
    if os.path.exists(gif_path):
        os.remove(gif_path)
    if os.path.exists(tag_file):
        os.remove(tag_file)
    flash('File deleted successfully', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
