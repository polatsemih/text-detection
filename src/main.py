from tkinter import filedialog, Tk, Label, Text, Frame, Button, PhotoImage, Scrollbar, Canvas, messagebox
from PIL import Image, ImageTk
import imutils
import cv2
import easyocr
from threading import Thread

def check_if_gpu_should_be_used():
    try:
        _ = easyocr.Reader(['en', 'tr'], gpu=True)
        return True
    except Exception as e:
        print(f"GPU usage not possible: {e}")
        return False

use_gpu = check_if_gpu_should_be_used()
reader = easyocr.Reader(['en', 'tr'], gpu = use_gpu)


real_time_flag = False

def preprocess_image(image):
    results = reader.readtext(image, paragraph = True)
    return results

def detect_text(results):
    detected_text = [text[1] for text in results]
    formatted_text = "\n".join(detected_text)
    return formatted_text

def boundary_box(results, image):
    for (bbox, text) in results:
        (top_left, top_right, bottom_right, bottom_left) = bbox
        top_left = tuple(map(int, top_left))
        bottom_right = tuple(map(int, bottom_right))

        cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)
        cv2.putText(image, text, top_left, cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    return image

def upload_image():
    global real_time_flag

    try:
        real_time_flag = False
        
        file_path = filedialog.askopenfilename(title='Upload Image', filetypes=[("Image files", "*.png;*.jpg;*.jpeg")])
        if file_path:
            uploaded_image = cv2.imread(file_path)
            if uploaded_image is not None:

                original_image = uploaded_image.copy()
                results = preprocess_image(uploaded_image)
                detected_text = detect_text(results)
                bboxed_image = boundary_box(results, uploaded_image)

                # UI
                display_static_content()
                display_image(original_image, 'input') # display input original image
                display_image(bboxed_image, 'output') # display output bboxed image
                update_download_command(bboxed_image) # update download button to download new bboxed image
                detected_text_label.delete(1.0, "end") # delete old printed detected text if exists
                detected_text_label.insert("end", detected_text) # insert new detected text

            else:
                print(f"Error: Could not read the image from {file_path}")
                exit_window()

        else:
            print("No file selected.")
            exit_window()

    except Exception as e:
        print(f"Error: {e}")
        exit_window()
        
def display_image(image, type_of_image):
    max_width = 400
    max_height = 300
    image = imutils.resize(image, width=max_width, height=max_height)
    
    image_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    image_tk = ImageTk.PhotoImage(image_pil)
    
    if type_of_image == 'input':
        image_input.config(image=image_tk)
        image_input.image = image_tk
    elif type_of_image == 'output':
        image_output.config(image=image_tk) 
        image_output.image = image_tk

def update_download_command(bboxed_image):
    download_button.config(command=lambda: save_bboxed_image(bboxed_image))
    
def save_bboxed_image(bboxed_image):
    try:
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            cv2.imwrite(file_path, bboxed_image)
            messagebox.showinfo("Saved", f"Bounded image saved successfully at {file_path}")
    except Exception as e:
        print(f"Error: {e}")
        messagebox.showerror("Error", "Error saving the bounded image")
    
def real_time_detection():
    global real_time_flag
    real_time_flag = True

    try:
        display_real_time_content()

        # Create a new thread for real-time processing
        thread = Thread(target=real_time_detection_from_thread)
        thread.start()
    except Exception as e:
        print(f"Error: {e}")
        exit_window()


def real_time_detection_from_thread():
    try:
        webcam_capture = cv2.VideoCapture(0) # open the webcam (source 0)
        if webcam_capture.isOpened():
            print("Webcam opened successfully.")
            cap = webcam_capture
        else:
            print("Webcam not available, trying Android cam.")
            android_capture = cv2.VideoCapture("http://100.66.202.42:4747/video") # open the android cam
            if android_capture.isOpened():
                print("Android cam opened successfully.")
                cap = android_capture
            else:
                print("Error: Neither webcam nor Android cam available.")
                exit_window()
                
        if not cap.isOpened():
            print("Error: Could not open webcam.")
            exit_window()

        # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640) # 320
        # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) # 240
        # cap.set(cv2.CAP_PROP_EXPOSURE, -7)

        while real_time_flag:  # stop if the user uploads an image
            ret, frame = cap.read()  # read a frame from the webcam
            if not ret:  # a boolean value indicating whether the frame was read successfully
                print("Error: Could not read frame.")
                break

            results = preprocess_image(frame)
            detected_text = detect_text(results)
            bboxed_image = boundary_box(results, frame)

            display_frame(bboxed_image)
            real_time_detected_text_label.delete(1.0, "end")
            real_time_detected_text_label.insert("end", detected_text)

            window.update()  # update GUI

        cap.release()  # close the video source
    except Exception as e:
        print(f"Error: {e}")
        exit_window()

def display_frame(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = Image.fromarray(frame)
    
    window_width = window.winfo_width()
    canvas_width = window_width // 2
    aspect_ratio = frame.width / frame.height
    canvas_height = int(canvas_width / aspect_ratio)
    frame = frame.resize((canvas_width, canvas_height), Image.LANCZOS)
    
    frame_tk = ImageTk.PhotoImage(frame)
    
    video_canvas.config(width=canvas_width, height=canvas_height)
    video_canvas.create_image(0, 0, anchor='nw', image=frame_tk)
    video_canvas.image = frame_tk
        
def exit_window():
    global real_time_flag
    real_time_flag = False
    
    if window:
        window.after(1000, window.destroy) # 1000 milliseconds short delay
    else:
        print("Window has already been destroyed.")
    
####################################### UI #######################################
def display_real_time_content():
    static_content_title.pack_forget()
    static_content.pack_forget()
    static_content_text.pack_forget()
    
    real_time_content_title.pack(side="top", fill="x")
    real_time_content.pack(side="top", fill="x", pady=(default_padding, default_padding)) # visible real time content

def display_static_content():
    real_time_content_title.pack_forget()
    real_time_content.pack_forget() # hidden real time content
    
    static_content_title.pack(side="top", fill="x") # visible the original image and bboxed image titles
    static_content.pack(side="top", fill="x", pady=(default_padding, default_padding)) # visible the upload static image content
    static_content_text.pack(side="top", fill="both") # visible the textarea to print detected text

####################################### ROOT #######################################
default_font_family = 'Poppins'
default_font_size = 16
default_font_size_weak = 13
default_background_color = '#2e2e3c'
default_color = '#d0d7de'
default_padding = 10
default_border_width = 1
default_border_style = 'solid'
default_border_color = '#505050'
default_hover = '#3b3b3e'
default_cursor = 'arrow'
click_cursor = 'hand2'

card_background_color = '#19191c'
title_font_size = 20
theme_color = '#704ff6'

danger_color = '#ca0101'

####################################### WINDOW #######################################
window = Tk()

def set_window_size(window, width_percent, height_percent):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    width = int(screen_width * (width_percent / 100))
    height = int(screen_height * (height_percent / 100))

    x_position = (screen_width - width) // 2
    y_position = (screen_height - height) // 2

    window.geometry(f"{width}x{height}+{x_position}+{y_position}")

set_window_size(window, 75, 75)
window.resizable(width=True, height=True)
window.iconbitmap('icons/favicon.ico')
window.title('Text Detection - Semih Utku Polat')

window.option_add('*Font', (default_font_family, default_font_size))
window.config(
    bg=default_background_color,
    cursor=default_cursor
)

####################################### TITLE #######################################
title = Label(window, 
              text="Text Detection - Semih Utku Polat",              
              font=(default_font_family, title_font_size),
              fg=theme_color,
              bg=card_background_color,
              padx=default_padding,
              pady=default_padding
)
title.pack(side="top",
           fill="x"
)

####################################### MENU #######################################
nav_menu = Frame(window,
                    bg=card_background_color
)
nav_menu.pack(side="left",
              fill="y"
)

menu_title = Label(nav_menu, 
                   text="Menu",
                   font=(default_font_family, default_font_size),
                   fg=theme_color,
                   bg=card_background_color,
                   padx=default_padding,
                   pady=default_padding,
                   anchor="w"
)
menu_title.grid(row=0,
                column=0,
                sticky="ew"
)

def menu_item_on_hover(event):
    event.widget.config(background=default_hover)

def menu_item_off_hover(event):
    event.widget.config(background=card_background_color)

button_upload_image = Button(nav_menu,
                            text='Upload Image',
                            font=(default_font_family, default_font_size),
                            fg=default_color,
                            bg=card_background_color,
                            padx=default_padding,
                            pady=default_padding,
                            bd=default_border_width,
                            relief=default_border_style,
                            cursor=click_cursor,
                            anchor="w",
                            command=upload_image
)
button_upload_image.grid(row=1,
                         column=0,
                         sticky="ew"
)
button_upload_image.bind("<Enter>", menu_item_on_hover)
button_upload_image.bind("<Leave>", menu_item_off_hover)

button_real_time = Button(nav_menu,
                            text='Real Time',
                            font=(default_font_family, default_font_size),
                            fg=default_color,
                            bg=card_background_color,
                            padx=default_padding,
                            pady=default_padding,
                            bd=default_border_width,
                            relief=default_border_style,
                            cursor=click_cursor,
                            anchor="w",
                            command=real_time_detection
)
button_real_time.grid(row=2,
                      column=0,
                      sticky="ew"
)
button_real_time.bind("<Enter>", menu_item_on_hover)
button_real_time.bind("<Leave>", menu_item_off_hover)

button_exit_window = Button(nav_menu,
                            text='Exit',
                            font=(default_font_family, default_font_size),
                            fg=danger_color,
                            bg=card_background_color,
                            padx=default_padding,
                            pady=default_padding,
                            bd=default_border_width,
                            relief=default_border_style,
                            cursor=click_cursor,
                            anchor="w",
                            command=exit_window
)
button_exit_window.grid(row=3,
                        column=0,
                        sticky="ew"
)
button_exit_window.bind("<Enter>", menu_item_on_hover)
button_exit_window.bind("<Leave>", menu_item_off_hover)

####################################### STATIC CONTENT TITLES #######################################
static_content_title = Frame(window,
                    bg=default_background_color
)
static_content_title.pack_forget()

static_input_title = Label(static_content_title,
                   text="Original Image",
                   font=(default_font_family, default_font_size_weak),
                   fg=default_color,
                   bg=default_background_color,
                   padx=default_padding,
                   pady=default_padding
)
static_input_title.pack(side="left", fill='x', expand=True)

static_output_title = Label(static_content_title,
                   text="Image With B-BOX",
                   font=(default_font_family, default_font_size_weak),
                   fg=default_color,
                   bg=default_background_color,
                   padx=default_padding,
                   pady=default_padding
)
static_output_title.pack(side="left", fill='x', expand=True)

download_icon_path = "icons/save.png"
download_icon = PhotoImage(file=download_icon_path)
download_button = Button(static_output_title,
                         image=download_icon,
                         text='Download',
                         font=(default_font_family, default_font_size),
                         fg=default_color,
                         bg=card_background_color,
                         padx=default_padding,
                         pady=default_padding,
                         bd=default_border_width,
                         relief=default_border_style,
                         cursor=click_cursor,
                         anchor="w"
)
download_button.image = download_icon
download_button.pack(side="right")
download_button.bind("<Enter>", menu_item_on_hover)
download_button.bind("<Leave>", menu_item_off_hover)

####################################### STATIC CONTENT DISPLAY ORIGINAL AND BBOXED IMAGES #######################################
static_content = Frame(window,
                bg=default_background_color
)
static_content.pack_forget()

image_input = Label(static_content,
                   bg=default_background_color,
                   padx=default_padding,
                   pady=default_padding
)
image_input.pack(side="left",
                 expand=True
)

image_output = Label(static_content,
                   bg=default_background_color,
                   padx=default_padding,
                   pady=default_padding
)
image_output.pack(side="left",
                 expand=True
)

####################################### STATIC CONTENT DETECTED TEXT #######################################
static_content_text = Frame(window,
                    bg=default_background_color
)
static_content_text.pack_forget()


detected_text_title = Label(static_content_text,
                    text="Detected Text:",
                    font=(default_font_family, default_font_size_weak),
                    fg=default_color,
                    bg=default_background_color,
                    padx=default_padding,
                    pady=default_padding,
                    anchor='w'
)
detected_text_title.pack(side="top",
                   fill="both",
                  expand=True
)

detected_text_label = Text(static_content_text,
                    font=(default_font_family, 11),
                    fg=default_color,
                    bg=default_background_color,
                    padx=default_padding,
                    pady=default_padding,
                    wrap="word",
                    borderwidth=0,
                    highlightthickness=0
)
detected_text_label.pack(side="left",
                   fill="both",
                  expand=True
)

vertical_scrollbar = Scrollbar(static_content_text, 
                               command=detected_text_label.yview
)
vertical_scrollbar.pack(side="right", fill="y")
detected_text_label.config(yscrollcommand=vertical_scrollbar.set)

####################################### REAL TIME CONTENT TITLES #######################################
real_time_content_title = Frame(window,
                    bg=default_background_color
)
real_time_content_title.pack_forget()

real_time_input_title = Label(real_time_content_title,
                   text="Real Time Text Detection",
                   font=(default_font_family, default_font_size_weak),
                   fg=default_color,
                   bg=default_background_color,
                   padx=default_padding,
                   pady=default_padding
)
real_time_input_title.pack(side="left", fill='x', expand=True)

real_time_output_title = Label(real_time_content_title,
                   text="Detected Text",
                   font=(default_font_family, default_font_size_weak),
                   fg=default_color,
                   bg=default_background_color,
                   padx=default_padding,
                   pady=default_padding
)
real_time_output_title.pack(side="left", fill='x', expand=True)

####################################### REAL TIME CONTENT DISPLAY VIDE FRAM AND DETECTED TEXT #######################################
real_time_content = Frame(window,
                     bg=default_background_color
)
real_time_content.pack_forget()

video_canvas = Canvas(real_time_content, 
                      bg=default_background_color,
                      highlightthickness=0,
                      highlightbackground=default_background_color
)
video_canvas.pack(side="left",
                  expand=True
)

real_time_detected_text_label = Text(real_time_content,
                    font=(default_font_family, 11),
                    fg=default_color,
                    bg=default_background_color,
                    padx=default_padding,
                    pady=default_padding,
                    wrap="word",
                    borderwidth=0,
                    highlightthickness=0
)
real_time_detected_text_label.pack(side="top",
                                   fill="both",
                            expand=True
)

window.mainloop()