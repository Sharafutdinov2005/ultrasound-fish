# This is an auxiliary class for data pre-processing.
# It cuts all .mp4 files to frames, pre-processes them, and saves them in a
# specified directory.
#
# It includes methods for
#     extracting frames from videos,
#     changing their color representation,
#     applying denoising techniques,
#     and improving image contrast.


import cv2
from cv2.typing import MatLike
from typing import Self
from pathlib import Path
import os


class _VideoCaptureManager:
    """
    Auxiliary class to prevent the video capture object from leaking.
    """

    _video_address: str
    _capture: cv2.VideoCapture

    def __init__(
        self,
        video_address: str
    ) -> None:
        """
        Initializes the video capture object.
        """

        self._validate_video_address(video_address)
        self._video_address = video_address

    def _validate_video_address(
        self,
        video_address: str = None
    ) -> None:
        """
        Validates the video address.
        """

        if not os.path.exists(video_address):
            raise FileNotFoundError(
                f"The video address '{video_address}' does not exist."
            )

    def read(
        self
    ) -> tuple[bool, MatLike]:
        """
        Returns the next frame from the video.
        """
        return self._capture.read()

    def __enter__(
        self
    ) -> Self:
        """
        Initializes the video capture object when entering the context.
        """

        self._capture = cv2.VideoCapture(self._video_address)
        return self

    def __exit__(
        self,
        *args
    ) -> None:
        """
        Releases the video capture object when exiting the context.
        """

        self._capture.release()


class _FrameProcessor:
    def _convert_to_single_channel(
        self,
        image: MatLike
    ) -> MatLike:
        """
        Converts the image to a single channel.
        """
        if image.ndim == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image


class DataSetPreProcessor(_FrameProcessor):
    """
    Class to pre-process the videos in the dataset.
    """

    _directory_to_save: str

    def __init__(
        self,
        directory_to_save: str
    ) -> None:
        """
        Initializes the data pre-processor.
        """

        self._validate_directory(directory_to_save)
        self._directory_to_save = directory_to_save

    def _validate_directory(
        self,
        directory: str
    ) -> None:
        """
        Validates the directory to save the pre-processed data.
        """

        if not os.path.exists(directory):
            os.makedirs(directory)
        elif not os.path.isdir(directory):
            raise ValueError(f"The directory {directory} is not a directory.")

    def preprocess_dataset(
        self,
        directory: str
    ) -> None:
        """
        Pre-processes all videos from the directory.\n
        This method doesn't check subdirectories.
        """
        pathlist = Path(directory).glob('*.mp4')
        for path in pathlist:
            self.preprocess_video(str(path))

    def preprocess_video(
        self,
        video_address: str
    ) -> None:
        """
        Pre-processes all frames from video and saves
        them to a new directory.
        """

        video_name = self._get_video_name(video_address)
        i = 0
        with _VideoCaptureManager(video_address) as manager:
            while True:
                success, frame = manager.read()
                if not success:
                    break
                self._save_frame(self._preprocess_frame(frame), video_name, i)
                i += 1

    def _preprocess_frame(
        self,
        frame: MatLike
    ) -> MatLike:
        """
        Pre-processes a single frame.
        """

        frame = self._convert_to_single_channel(frame)
        # do some pre-processing on the frame (e.g., resize, normalize)
        return frame

    def _save_frame(
        self,
        frame: MatLike,
        video_name: str,
        frame_number: int
    ) -> None:
        """
        Saves the pre-processed frame to a new directory.
        """

        cv2.imwrite(
                    f"{self._directory_to_save}/"
                    f"{video_name}_frame_{frame_number}.jpg", frame
                )

    def _get_video_name(
        self,
        video_address: str
    ) -> str:
        """Extracts the video name from the video address."""

        video_name = ""
        for i in range(len(video_address) - 5, -1, -1):
            if video_address[i] == "\\":
                break
            video_name = video_address[i] + video_name
        return video_name


if __name__ == "__main__":
    video_address = (
        'C:/Users/rusmi/Programming/Python/engeneering_workshop_spring_2025/'
        'data_example/REC_Video_00000004.mp4'
    )

    directory_to_save = (
        'C:/Users/rusmi/Programming/Python/'
        'engeneering_workshop_spring_2025/'
        'data_example/frames/'
    )

    directory = (
        'C:/Users/rusmi/Programming/Python/'
        'engeneering_workshop_spring_2025/'
        'data_example/'
    )

    preprocessor = DataSetPreProcessor(directory_to_save)
    preprocessor.preprocess_dataset(directory)
