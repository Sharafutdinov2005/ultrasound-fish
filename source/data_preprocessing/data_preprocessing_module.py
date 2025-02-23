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
from typing import Self, Optional
from numpy import mean as np_mean, array as np_array
# from pathlib import Path
from imageio import get_writer

# upper left corner of the ultrasound
_x_image_begin = 63
_y_image_begin = 18

# image size
_image_width = 386
_image_height = 424

# critical value of sum pixels in a frame
_critical_value = 24


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
        self,
        preprocess: bool = False
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
            success, frame = self.read(preprocess=True)
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

        with _VideoCaptureContextManager(self._capture) as capture:
            while True:
                success, frame = capture.read()

                if not success:
                    break

                if is_uninformative(frame):
                    continue

                cv2.imwrite(
                    f"{directory}/{self._video_name}_"
                    f"frame_{number_of_frames}",
                    frame if not preprocess else self._preprocess_frame(frame)
                    )

                number_of_frames += 1

                del frame

                capture.skip(3)


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

        number_of_frames = 0
        i = 0

        with _VideoCaptureContextManager(self._capture) as capture:
            while True:
                success, frame = capture.skip_uninformative()

                if not success or is_uninformative(frame):
                    return number_of_frames

                with get_writer(
                    f"{directory}/fish_{i}.gif", mode='I', fps=30
                ) as writer:
                    while success and not is_uninformative(frame):
                        writer.append_data(np_array(frame))
                        del frame
                        success, frame = capture.read()
                i += 1


# class DirectoryPreProcessor():
#     """
#     Class for pre-processing videos in the directory.
#     """
#     @staticmethod
#     def _validate_directory_to_save(
#         directory: str
#     ) -> None:
#         """
#         Validates the directory to save the pre-processed frames.
#         """
#         if not os.path.exists(directory):
#             os.makedirs(directory)
#         elif not os.path.isdir(directory):
#             raise ValueError(
#             f"The directory {directory} is not a directory.")
#     @staticmethod
#     def _validate_directory(
#         directory: str
#     ) -> None:
#         """
#         Validates the directory.
#         """
#         if not os.path.exists(directory):
#             raise ValueError(f"The directory {directory} does not exist.")
#     @staticmethod
#     def _validate_address(
#         address: str
#     ) -> None:
#         """
#         Validates the address.
#         """
#         if not os.path.exists(address):
#             raise ValueError(f"The address {address} does not exist.")
#     def preprocess_directory(
#         self,
#         directory: str,
#         directory_to_save: str
#     ) -> None:
#         """
#         Pre-processes all videos from the `directory` and saves them
#         to `directory_to_save`.\n
#         This method doesn't check subdirectories.
#         """
#         self._validate_directory(directory)
#         pathlist = Path(directory).glob('*.mp4')
#         for path in pathlist:
#             self.preprocess_video(str(path), directory_to_save)
#     def preprocess_video(
#         self,
#         video_address: str,
#         directory_to_save: str
#     ) -> None:
#         """
#         Pre-processes all frames from `video_addres` and saves
#         them to a `directory_to_save`.
#         """
#         self._validate_address(video_address)
#         self._validate_directory_to_save(directory_to_save)
#         i = 0
#         with _VideoCaptureContextManager(video_address) as manager:
#             while True:
#                 success, frame = manager.read()
#                 i += 1
#                 if not success:
#                     break
#                 if self._is_blank(frame):
#                     pass
#                 del frame


if __name__ == "__main__":

    # directory = input("Directory to process: ")
    # directory_to_save = input("Directory to save: ")

    a = VideoToGIF(
        'C:/Users/rusmi/Programming/Python/Ultrasound/'
        'data_example/REC_Video_00000013.mp4'
    )

    a.save_GIFs_to_directory(
        'C:/Users/rusmi/Programming/Python/Ultrasound/data_example/gifs_1'
    )
