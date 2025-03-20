from flask import Flask, render_template, request, redirect, url_for, flash
import os
from datetime import datetime
from data_preprocessing.data_preprocessing_module import VideoToGIF

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'gif_markup_app/static/uploads'
app.config['PROCESSED_FOLDER'] = 'gif_markup_app/static/processed'
app.config['ALLOWED_EXTENSIONS'] = {'mp4'}
app.secret_key = 'your_secret_key_here'

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


def get_tags_frame(filename, folder):
    tag_file = os.path.join(folder, filename)
    tags = {}
    if os.path.exists(tag_file):
        with open(tag_file, 'r') as f:
            current_frame = None
            for line in f.readlines():
                line = line.strip()
                if line.endswith(':'):  # Frame name
                    current_frame = line[:-1]
                    tags[current_frame] = {}
                elif ': ' in line and current_frame:
                    key, value = line.split(': ', 1)
                    tags[current_frame][key] = value
    return tags


def save_tags_frame(filename, folder, tags):
    tag_file = os.path.join(folder, filename)
    with open(tag_file, 'w') as f:
        for frame, frame_tags in tags.items():
            f.write(f'{frame}:\n')
            for key, value in frame_tags.items():
                f.write(f'{key}: {value}\n')


def get_tags_gif(filename, folder):
    tag_file = os.path.join(folder, filename)
    tags = {}
    if os.path.exists(tag_file):
        with open(tag_file, 'r') as f:
            for line in f.readlines():
                if ': ' in line:
                    key, value = line.strip().split(': ', 1)
                    tags[key] = value
    return tags


def save_tags_gif(filename, folder, tags):
    tag_file = os.path.join(folder, filename)
    with open(tag_file, 'w') as f:
        for key, value in tags.items():
            f.write(f'{key}: {value}\n')


@app.route('/')
def index():
    # List all processed folders
    processed_folders = []
    for folder_name in os.listdir(app.config['PROCESSED_FOLDER']):
        folder_path = os.path.join(app.config['PROCESSED_FOLDER'], folder_name)
        if os.path.isdir(folder_path):
            processed_folders.append(folder_name)
    return render_template('index.html', processed_folders=processed_folders)


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

            # Pre-process the video (convert to GIFs and extract frames)
            preprocess_video(filepath, folder_path)

            flash('File uploaded and processed successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid file type. Only .mp4 files are allowed.', 'error')

    return render_template('upload.html')


@app.route('/markup/<folder_name>')
def markup_folder(folder_name):
    folder_path = os.path.join(app.config['PROCESSED_FOLDER'], folder_name)
    if not os.path.exists(folder_path):
        flash('Folder not found', 'error')
        return redirect(url_for('index'))

    # List all GIFs in the selected folder
    gifs = []
    for f in os.listdir(folder_path):
        if f.startswith('fish_') and f.endswith('.gif'):
            tags = get_tags_gif(f'{f}.txt', folder_path)
            gifs.append({'filename': f, 'tags': tags})
    return render_template(
        'markup_folder.html',
        folder_name=folder_name,
        gifs=gifs
    )


@app.route('/markup/<folder_name>/<filename>', methods=['GET', 'POST'])
def markup_gif(folder_name, filename):
    folder_path = os.path.join(app.config['PROCESSED_FOLDER'], folder_name)
    if not os.path.exists(folder_path):
        flash('Folder not found', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Get selected values from the form
        gender = request.form.get('gender')
        stage = request.form.get('stage')
        anomaly = request.form.get('anomaly')

        # Read existing tags
        tags = get_tags_gif(f'{filename}.txt', folder_path)

        # Update tags if new values are provided
        if gender:
            tags['Gender'] = gender
        if stage:
            tags['Stage'] = stage
        if anomaly:
            tags['Anomaly'] = anomaly

        # Save the updated tags to the tag file
        save_tags_gif(f'{filename}.txt', folder_path, tags)

        flash('Markup saved successfully', 'success')
        return redirect(
            url_for(
                'markup_gif',
                folder_name=folder_name,
                filename=filename,
                tags=tags
            )
        )

    # Read existing tags
    tags = get_tags_gif(f'{filename}.txt', folder_path)
    return render_template(
        'markup_gif.html',
        folder_name=folder_name,
        filename=filename,
        tags=tags
    )


@app.route('/markup/<folder_name>/<filename>/frames', methods=['GET', 'POST'])
def markup_frames(folder_name, filename):
    folder_path = os.path.join(app.config['PROCESSED_FOLDER'], folder_name)
    if not os.path.exists(folder_path):
        flash('Folder not found', 'error')
        return redirect(url_for('index'))

    # Extract the fish number from the filename
    fish_number = filename.split('.')[0]
    frames_folder = os.path.join(folder_path, fish_number)
    if not os.path.exists(frames_folder):
        flash('Frames folder not found', 'error')
        return redirect(
            url_for('markup_gif', folder_name=folder_name, filename=filename)
        )

    # List all frames in the frames folder
    frames = [f for f in os.listdir(frames_folder) if f.endswith('.jpg')]

    if request.method == 'POST':
        # Get frame markup data
        frame_name = request.form.get('frame_name')
        gender_informative = request.form.get('gender_informative')
        stage_informative = request.form.get('stage_informative')
        anomaly_informative = request.form.get('anomaly_informative')
        not_informative = request.form.get('not_informative')

        # Read existing frame tags
        frame_tags = get_tags_frame(f'{fish_number}_frames.txt', folder_path)

        # Update frame tags with new values
        if frame_name not in frame_tags:
            frame_tags[frame_name] = {}

        if gender_informative:
            frame_tags[frame_name]['Gender Informative'] = gender_informative
        if stage_informative:
            frame_tags[frame_name]['Stage Informative'] = stage_informative
        if anomaly_informative:
            frame_tags[frame_name]['Anomaly Informative'] = anomaly_informative
        if not_informative:
            frame_tags[frame_name]['Not Informative'] = not_informative

        # Save the updated tags to the tag file
        save_tags_frame(f'{fish_number}_frames.txt', folder_path, frame_tags)

        flash('Frame markup saved successfully', 'success')
        return redirect(
            url_for(
                'markup_frames', folder_name=folder_name, filename=filename
            )
        )

    # Read existing frame tags
    frame_tags = get_tags_frame(f'{fish_number}_frames.txt', folder_path)
    return render_template(
        'markup_frames.html',
        folder_name=folder_name,
        filename=filename,
        frames=frames,
        frame_tags=frame_tags
    )


if __name__ == '__main__':
    app.run(debug=True)
