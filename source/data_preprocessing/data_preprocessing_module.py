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
import os
from cv2.typing import MatLike
from typing import Self
from pathlib import Path


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

    @staticmethod
    def _validate_video_address(
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


def crop_image(
    image: MatLike,
    x: int = 63,
    y: int = 18,
    width: int = 386,
    height: int = 424
) -> MatLike:
    return image[y:y + height, x:x + width]


def preprocess_frame(
    image: MatLike
) -> MatLike:
    """
    Pre-processes the frame.
    """
    # TODO:
    # - add Homomorphic Filtering
    image = crop_image(image)

    image = cv2.ximgproc.anisotropicDiffusion(image, 0.2, 0.1, 5)

    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    image = cv2.equalizeHist(image)

    image = cv2.fastNlMeansDenoising(image, None, 20, 7, 21)

    return image


class DirectoryPreProcessor():
    """
    Class for pre-processing videos in the directory.
    """
    @staticmethod
    def _validate_directory_to_save(
        directory: str
    ) -> None:
        """
        Validates the directory to save the pre-processed frames.
        """
        if not os.path.exists(directory):
            os.makedirs(directory)
        elif not os.path.isdir(directory):
            raise ValueError(f"The directory {directory} is not a directory.")

    @staticmethod
    def _validate_directory(
        directory: str
    ) -> None:
        """
        Validates the directory.
        """
        if not os.path.exists(directory):
            raise ValueError(f"The directory {directory} does not exist.")

    @staticmethod
    def _validate_address(
        address: str
    ) -> None:
        """
        Validates the address.
        """
        if not os.path.exists(address):
            raise ValueError(f"The address {address} does not exist.")

    def preprocess_directory(
        self,
        directory: str,
        directory_to_save: str
    ) -> None:
        """
        Pre-processes all videos from the `directory` and saves them
        to `directory_to_save`.\n
        This method doesn't check subdirectories.
        """
        self._validate_directory(directory)
        pathlist = Path(directory).glob('*.mp4')
        for path in pathlist:
            self.preprocess_video(str(path), directory_to_save)

    def preprocess_video(
        self,
        video_address: str,
        directory_to_save: str
    ) -> None:
        """
        Pre-processes all frames from `video_addres` and saves
        them to a `directory_to_save`.
        """
        self._validate_address(video_address)
        self._validate_directory_to_save(directory_to_save)
        video_name = self._get_video_name(video_address)
        i = 0
        with _VideoCaptureManager(video_address) as manager:
            while True:
                if i % 5 != 0:
                    success, frame = manager.read()
                    i += 1
                    continue
                success, frame = manager.read()
                if not success:
                    break
                frame_name = f"{directory_to_save}/{video_name}_frame_{i}.jpg"
                assert cv2.imwrite(
                    frame_name,
                    preprocess_frame(frame)
                )
                del frame
                i += 1

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


if __name__ == "__main__":
    pp = DirectoryPreProcessor()

    # directory = input("Directory to process: ")
    # directory_to_save = input("Directory to save: ")

    pp.preprocess_video(
        'C:/Users/rusmi/Programming/Python/Ultrasound/'
        'data_example/REC_Video_00000013.mp4',
        'C:/Users/rusmi/Programming/Python/Ultrasound/data_example/frames')
