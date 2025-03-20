import cv2
import os
from cv2.typing import MatLike
from typing import Self, Optional
from numpy import mean as np_mean
from imageio import get_writer

# upper left corner of the ultrasound
_x_image_begin = 63
_y_image_begin = 18

# image size
_image_width = 386
_image_height = 424

# critical value of sum pixels in a frame
_critical_value = 23


def is_uninformative(
    image: MatLike,
) -> bool:
    """
    Checks if an image is uninformative.
    """
    if image is None:
        return True
    return np_mean(image) < _critical_value


class _VideoCaptureContextManager:
    """
    Auxiliary class to prevent the video capture object from leaking.
    """
    _capture: cv2.VideoCapture

    def __init__(
        self,
        video_capture: cv2.VideoCapture
    ) -> None:
        """
        Initializes the `_VideoCaptureContextManager` object.
        """
        self._capture = video_capture

    def read(
        self
    ) -> tuple[bool, MatLike]:
        """
        Returns the next frame from the video.
        """
        ret, frame = self._capture.read()
        return ret, self._crop_image(frame)

    @staticmethod
    def _crop_image(
        image: Optional[MatLike],
        x: int = _x_image_begin,
        y: int = _y_image_begin,
        width: int = _image_width,
        height: int = _image_height
    ) -> MatLike:
        if image is not None:
            image = image[y:y + height, x:x + width]
        return image

    def skip(
        self,
        frames: int = 1
    ) -> None:
        """
        Skips the specified number of frames.
        """
        for _ in range(frames):
            self._capture.grab()

    def skip_uninformative(
        self,
    ) -> tuple[bool, MatLike]:
        """
        Skips the uninformative frames.
        """
        while True:
            success, frame = self.read()
            if not success or not is_uninformative(frame):
                return success, frame

    def __enter__(
        self
    ) -> Self:
        """
        Enters the context manager.
        """
        return self

    def __exit__(
        self,
        *args
    ) -> None:
        """
        Exits the context manager.
        Releases the video capture object when exiting the context.
        """
        self._capture.release()


class _VideoCutter():
    """
    A class that converts a video into preprocessed frames.
    """
    _capture: cv2.VideoCapture
    _video_name: str

    def __init__(
        self,
        file_name: str
    ) -> None:
        """
        Initializes `_VideoCutter` object.
        """
        try:
            self._capture = cv2.VideoCapture(file_name)
        except Exception:
            raise FileNotFoundError(
                f"File {file_name} not found"
            )
        self._video_name = self._get_video_name(file_name)

    @staticmethod
    def _validate_directory_to_save(
        directory: str
    ) -> None:
        """
        Validates the directory to save the pre-processed frames.
        """
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception:
            raise NotADirectoryError(
                f"Directory {directory} is not a valid directory"
            )

    def _get_video_name(
        self,
        video_address: str
    ) -> str:
        """
        Extracts the video name from the video address.
        """
        video_name = ""
        for i in range(len(video_address) - 5, -1, -1):
            if video_address[i] == "/":
                break
            video_name = video_address[i] + video_name
        return video_name

    @staticmethod
    def _preprocess_frame(
        image: MatLike
    ) -> MatLike:
        """
        Pre-processes the frame.
        """
        # TODO:
        # - add Homomorphic Filtering

        image = cv2.ximgproc.anisotropicDiffusion(image, 0.2, 0.1, 5)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = cv2.equalizeHist(image)
        image = cv2.fastNlMeansDenoising(image, None, 20, 7, 21)

        return image


class VideoToFrames(_VideoCutter):
    """
    A class that cuts a video into frames and saves them to a directory.
    """
    def save_to_directory(
        self,
        directory: str,
        preprocess: bool = True
    ) -> None:
        """
        Saves the frames to the specified directory.
        """
        self._validate_directory_to_save(directory)

        number_of_frames = 0
        number_of_fish = 0

        directory_to_save = f"{directory}/{self._video_name}"

        with _VideoCaptureContextManager(self._capture) as capture:
            while True:
                success, frame = capture.skip_uninformative()

                os.makedirs(
                    f"{directory_to_save}/"
                    f"fish_{number_of_fish}/"
                )

                if not success:
                    return

                while success and not is_uninformative(frame):
                    assert cv2.imwrite(
                        f"{directory_to_save}/"
                        f"fish_{number_of_fish}/"
                        f"frame_{number_of_frames}.jpg",
                        frame
                        if not preprocess else
                        self._preprocess_frame(frame)
                    )
                    capture.skip()
                    success, frame = capture.read()
                    number_of_frames += 1

                number_of_frames = 0
                number_of_fish += 1


class VideoToGIF(_VideoCutter):
    """
    A class that cuts a video into GIFs and saves them to a directory.
    """
    def save_GIFs_to_directory(
        self,
        directory: str,
        preprocess: bool = False
    ) -> None:
        """
        Saves GIFs to the specified directory.
        """
        self._validate_directory_to_save(directory)

        number_of_fish = 0

        with _VideoCaptureContextManager(self._capture) as capture:
            while True:
                success, frame = capture.skip_uninformative()

                if not success:
                    return

                with get_writer(
                    f"{directory}/fish_{number_of_fish}.gif", mode='I', fps=30
                ) as writer:
                    number_of_frames = 0
                    os.makedirs(
                        f"{directory}/"
                        f"fish_{number_of_fish}/",
                        exist_ok=True
                    )
                    while success and not is_uninformative(frame):
                        assert cv2.imwrite(
                            f"{directory}/"
                            f"fish_{number_of_fish}/"
                            f"frame_{number_of_frames}.jpg",
                            frame
                            if not preprocess else
                            self._preprocess_frame(frame)
                        )
                        writer.append_data(
                            frame
                            if not preprocess else
                            self._preprocess_frame(frame)
                        )
                        del frame
                        success, frame = capture.read()
                        number_of_frames += 1
                number_of_fish += 1
