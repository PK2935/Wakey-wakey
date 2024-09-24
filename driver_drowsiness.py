import cv2
import numpy as np
import dlib
from imutils import face_utils
import os
import random
import pygame
from moviepy.editor import VideoFileClip
import tempfile

print("Initializing...")

pygame.init()
pygame.mixer.init()

print("Opening camera...")
cap = cv2.VideoCapture(0)

print("Loading face detector and predictor...")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# State variables
sleep = 0
drowsy = 0
active = 0
status = ""
color = (0, 0, 0)

# Meme files
meme_directory = 'C:/Users/pkshi/Documents/Study notes/Projects/Wakey Wakey/Wakey Wakey/memes'  # Update this path to your meme folder
meme_files = []

def compute(ptA, ptB):
    return np.linalg.norm(ptA - ptB)

def blinked(a, b, c, d, e, f):
    up = compute(b, d) + compute(c, e)
    down = compute(a, f)
    ratio = up / (2.0 * down)

    if ratio > 0.25:
        return 2
    elif 0.21 < ratio <= 0.25:
        return 1
    else:
        return 0

def get_meme_files(directory):
    print(f"Searching for meme files in {directory}")
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist!")
        return []
    memes = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.mp4')]
    print(f"Found {len(memes)} meme files")
    return memes

def extract_audio(video_path):
    print(f"Extracting audio from {video_path}")
    temp_dir = tempfile.gettempdir()
    temp_audio_path = os.path.join(temp_dir, 'temp_audio.wav')
    
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(temp_audio_path, codec='pcm_s16le')
    
    return temp_audio_path

def play_next_meme():
    global meme_files
    if not meme_files:
        print("No meme files found!")
        return None, None, None
    
    meme = random.choice(meme_files)
    meme_files.remove(meme)  # Remove the meme after selecting it
    print(f"Playing meme: {meme}")
    video = cv2.VideoCapture(meme)
    audio_path = extract_audio(meme)
    audio = pygame.mixer.Sound(audio_path)
    
    return video, audio, audio_path

def resize_frame_to_square(frame, size=300):
    h, w = frame.shape[:2]
    if h > w:
        diff = h - w
        padding = diff // 2
        frame = frame[padding:padding+w, :]
    elif w > h:
        diff = w - h
        padding = diff // 2
        frame = frame[:, padding:padding+h]
    return cv2.resize(frame, (size, size))

def play_random_memes():
    global status, color, sleep, drowsy, active
    if not meme_files:
        print("No meme files found!")
        return

    print("Starting to play random memes")
    video, audio, audio_path = play_next_meme()
    if video is None:
        return  # No video to play
    audio.play()

    while status == "SLEEPING !!!":
        ret, meme_frame = video.read()
        if not ret:
            print("Finished playing current meme, reshuffling memes")
            video.release()
            pygame.mixer.stop()
            os.remove(audio_path)

            # Reshuffle memes here if you've exhausted the list
            if not meme_files:  # Check if all memes have been played
                print("Reshuffling meme files")
                meme_files.extend(get_meme_files(meme_directory))  # Reload meme files
                random.shuffle(meme_files)  # Shuffle again
            video, audio, audio_path = play_next_meme()
            audio.play()
            continue

        meme_frame = resize_frame_to_square(meme_frame)
        cv2.imshow('Wake Up Meme', meme_frame)

        # Check for face and update status
        _, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        if len(faces) > 0:
            for face in faces:
                landmarks = predictor(gray, face)
                landmarks = face_utils.shape_to_np(landmarks)

                left_blink = blinked(landmarks[36], landmarks[37], 
                                     landmarks[38], landmarks[41], landmarks[40], landmarks[39])
                right_blink = blinked(landmarks[42], landmarks[43], 
                                      landmarks[44], landmarks[47], landmarks[46], landmarks[45])

                if left_blink == 2 and right_blink == 2:
                    sleep = 0
                    drowsy = 0
                    active += 1
                    if active > 6:
                        status = "Active :)"
                        color = (0, 255, 0)
                        print("Person is now active, stopping memes")
                        break

        if cv2.waitKey(30) & 0xFF == 27:  # Press 'Esc' to exit
            print("Esc key pressed, stopping memes")
            break

    video.release()
    pygame.mixer.stop()
    os.remove(audio_path)
    cv2.destroyWindow('Wake Up Meme')

# Load meme files once
meme_files = get_meme_files(meme_directory)
random.shuffle(meme_files)

print("Starting main loop...")
while True:
    print("Capturing frame...")
    _, frame = cap.read()
    if frame is None:
        print("Failed to capture frame. Exiting...")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    face_frame = frame.copy()

    print("Detecting faces...")
    faces = detector(gray)

    if len(faces) > 0:
        print(f"Detected {len(faces)} face(s)")
        for face in faces:
            x1 = face.left()
            y1 = face.top()
            x2 = face.right()
            y2 = face.bottom()

            cv2.rectangle(face_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            landmarks = predictor(gray, face)
            landmarks = face_utils.shape_to_np(landmarks)

            left_blink = blinked(landmarks[36], landmarks[37], 
                                 landmarks[38], landmarks[41], landmarks[40], landmarks[39])
            right_blink = blinked(landmarks[42], landmarks[43], 
                                  landmarks[44], landmarks[47], landmarks[46], landmarks[45])
            
            if left_blink == 0 or right_blink == 0:
                sleep += 1
                drowsy = 0
                active = 0
                if sleep > 6:
                    status = "SLEEPING !!!"
                    color = (255, 0, 0)
                    print("Detected sleeping, playing memes")
                    play_random_memes()
            elif left_blink == 1 or right_blink == 1:
                sleep = 0
                active = 0
                drowsy += 1
                if drowsy > 6:
                    status = "Drowsy !"
                    color = (0, 0, 255)
            else:
                drowsy = 0
                sleep = 0
                active += 1
                if active > 6:
                    status = "Active :)"
                    color = (0, 255, 0)
            
            print(f"Current status: {status}")
            cv2.putText(frame, status, (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

            for n in range(0, 68):
                (x, y) = landmarks[n]
                cv2.circle(face_frame, (x, y), 1, (255, 255, 255), -1)
    else:
        print("No face detected")
        cv2.putText(frame, "No face detected", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

    cv2.imshow("Frame", frame)
    cv2.imshow("Result of detector", face_frame)
    
    key = cv2.waitKey(1)
    if key == 27:  # Press 'Esc' to exit
        print("Esc key pressed. Exiting...")
        break

print("Releasing camera and closing windows...")
cap.release()
cv2.destroyAllWindows()
pygame.quit()
print("Program ended.")
